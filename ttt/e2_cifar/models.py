"""Models for E2: ResNet-26-GN with TTT rotation branch, WRN-28-10-BN for Tent."""
import copy

import torch
import torch.nn as nn
import torch.nn.functional as F


def gn(c):
    return nn.GroupNorm(8, c)


class BasicBlockGN(nn.Module):
    def __init__(self, cin, cout, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(cin, cout, 3, stride, 1, bias=False)
        self.n1 = gn(cout)
        self.conv2 = nn.Conv2d(cout, cout, 3, 1, 1, bias=False)
        self.n2 = gn(cout)
        self.short = None
        if stride != 1 or cin != cout:
            self.short = nn.Sequential(nn.Conv2d(cin, cout, 1, stride, bias=False), gn(cout))

    def forward(self, x):
        out = F.relu(self.n1(self.conv1(x)))
        out = self.n2(self.conv2(out))
        sc = x if self.short is None else self.short(x)
        return F.relu(out + sc)


def _group(cin, cout, n, stride):
    layers = [BasicBlockGN(cin, cout, stride)]
    layers += [BasicBlockGN(cout, cout) for _ in range(n - 1)]
    return nn.Sequential(*layers)


class ResNet26TTT(nn.Module):
    """ResNet-26 (n=4 basic blocks/group, widths 16/32/64), GroupNorm.

    TTT split: shared encoder = conv1 + group1 + group2;
    main branch = group3 + fc(num_classes); ssl branch = copy(group3) + fc(4 rotations).
    """

    def __init__(self, num_classes=10):
        super().__init__()
        n = 4
        self.conv1 = nn.Conv2d(3, 16, 3, 1, 1, bias=False)
        self.n1 = gn(16)
        self.group1 = _group(16, 16, n, 1)
        self.group2 = _group(16, 32, n, 2)
        self.group3 = _group(32, 64, n, 2)
        self.fc = nn.Linear(64, num_classes)
        self.ssl_group3 = copy.deepcopy(self.group3)
        self.ssl_fc = nn.Linear(64, 4)

    def shared(self, x):
        return self.group2(self.group1(F.relu(self.n1(self.conv1(x)))))

    def forward(self, x):
        z = self.shared(x)
        h = F.adaptive_avg_pool2d(self.group3(z), 1).flatten(1)
        return self.fc(h)

    def forward_ssl(self, x):
        z = self.shared(x)
        h = F.adaptive_avg_pool2d(self.ssl_group3(z), 1).flatten(1)
        return self.ssl_fc(h)

    def forward_both(self, x):
        z = self.shared(x)
        hm = F.adaptive_avg_pool2d(self.group3(z), 1).flatten(1)
        hs = F.adaptive_avg_pool2d(self.ssl_group3(z), 1).flatten(1)
        return self.fc(hm), self.ssl_fc(hs)

    def encoder_named_params(self):
        for prefix in ["conv1", "n1", "group1", "group2"]:
            mod = getattr(self, prefix)
            for n_, p in mod.named_parameters():
                yield f"{prefix}.{n_}", p


class WideBasic(nn.Module):
    def __init__(self, cin, cout, stride, drop=0.0):
        super().__init__()
        self.bn1 = nn.BatchNorm2d(cin)
        self.conv1 = nn.Conv2d(cin, cout, 3, 1, 1, bias=False)
        self.drop = nn.Dropout(drop)
        self.bn2 = nn.BatchNorm2d(cout)
        self.conv2 = nn.Conv2d(cout, cout, 3, stride, 1, bias=False)
        self.short = None
        if stride != 1 or cin != cout:
            self.short = nn.Conv2d(cin, cout, 1, stride, bias=False)

    def forward(self, x):
        out = self.drop(self.conv1(F.relu(self.bn1(x))))
        out = self.conv2(F.relu(self.bn2(out)))
        sc = x if self.short is None else self.short(x)
        return out + sc


class WRN2810(nn.Module):
    def __init__(self, num_classes=10, drop=0.0):
        super().__init__()
        widths = [16, 160, 320, 640]
        n = 4
        self.conv1 = nn.Conv2d(3, widths[0], 3, 1, 1, bias=False)
        layers = []
        cin = widths[0]
        for i, w in enumerate(widths[1:]):
            stride = 1 if i == 0 else 2
            layers.append(WideBasic(cin, w, stride, drop))
            for _ in range(n - 1):
                layers.append(WideBasic(w, w, 1, drop))
            cin = w
        self.blocks = nn.Sequential(*layers)
        self.bn = nn.BatchNorm2d(widths[-1])
        self.fc = nn.Linear(widths[-1], num_classes)

    def forward(self, x):
        out = self.blocks(self.conv1(x))
        out = F.relu(self.bn(out))
        out = F.adaptive_avg_pool2d(out, 1).flatten(1)
        return self.fc(out)


class ReconHead(nn.Module):
    """Small decoder from shared features (B,32,16,16) -> (B,3,32,32) for
    masked-reconstruction TTT. Trained post-hoc on the frozen source encoder."""

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(32, 64, 3, 1, 1), nn.ReLU(),
            nn.Upsample(scale_factor=2, mode="nearest"),
            nn.Conv2d(64, 32, 3, 1, 1), nn.ReLU(),
            nn.Conv2d(32, 3, 3, 1, 1))

    def forward(self, z):
        return self.net(z)


def attach_recon_head(model: "ResNet26TTT"):
    model.recon_head = ReconHead()

    def forward_recon(x, m=model):
        return m.recon_head(m.shared(x))

    model.forward_recon = forward_recon
    return model


def rotate_batch(x):
    """Return (x_rot, labels): each image rotated by k*90deg, k uniform."""
    k = torch.randint(0, 4, (x.size(0),), device=x.device)
    xs = torch.stack([torch.rot90(img, int(kk), dims=(1, 2)) for img, kk in zip(x, k)])
    return xs, k


def build_model(arch, num_classes):
    if arch == "resnet26ttt":
        return ResNet26TTT(num_classes)
    if arch == "wrn2810":
        return WRN2810(num_classes)
    raise ValueError(arch)
