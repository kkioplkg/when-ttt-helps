"""CIFAR-10/100 and CIFAR-10-C/100-C loaders."""
import os

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, TensorDataset
from torchvision import datasets, transforms

MEAN = {"cifar10": (0.4914, 0.4822, 0.4465), "cifar100": (0.5071, 0.4865, 0.4409)}
STD = {"cifar10": (0.2470, 0.2435, 0.2616), "cifar100": (0.2673, 0.2564, 0.2762)}

CORRUPTIONS = [
    "gaussian_noise", "shot_noise", "impulse_noise", "defocus_blur", "glass_blur",
    "motion_blur", "zoom_blur", "snow", "frost", "fog", "brightness", "contrast",
    "elastic_transform", "pixelate", "jpeg_compression",
]


def train_transforms(ds):
    return transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(MEAN[ds], STD[ds]),
    ])


def test_transforms(ds):
    return transforms.Compose([
        transforms.ToTensor(), transforms.Normalize(MEAN[ds], STD[ds])])


def get_train_loader(ds, root, batch_size=128, workers=8):
    cls = datasets.CIFAR10 if ds == "cifar10" else datasets.CIFAR100
    tr = cls(root, train=True, download=True, transform=train_transforms(ds))
    return DataLoader(tr, batch_size=batch_size, shuffle=True,
                      num_workers=workers, pin_memory=True, drop_last=True)


def get_test_loader(ds, root, batch_size=256, workers=4):
    cls = datasets.CIFAR10 if ds == "cifar10" else datasets.CIFAR100
    te = cls(root, train=False, download=True, transform=test_transforms(ds))
    return DataLoader(te, batch_size=batch_size, shuffle=False,
                      num_workers=workers, pin_memory=True)


class CIFARCorrupted(Dataset):
    """CIFAR-10-C / CIFAR-100-C: numpy files, 5 severities x 10000 images each."""

    def __init__(self, ds, root, corruption, severity):
        cdir = os.path.join(root, "CIFAR-10-C" if ds == "cifar10" else "CIFAR-100-C")
        x = np.load(os.path.join(cdir, f"{corruption}.npy"))
        y = np.load(os.path.join(cdir, "labels.npy"))
        i0, i1 = (severity - 1) * 10000, severity * 10000
        self.x = x[i0:i1]
        self.y = y[i0:i1].astype(np.int64)
        self.mean = np.array(MEAN[ds], dtype=np.float32)
        self.std = np.array(STD[ds], dtype=np.float32)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, i):
        img = self.x[i].astype(np.float32) / 255.0
        img = (img - self.mean) / self.std
        return torch.from_numpy(img.transpose(2, 0, 1)), int(self.y[i])


def corrupted_tensor(ds, root, corruption, severity, n=None, seed=0):
    """Return (x, y) tensors, optionally a fixed random subset of size n."""
    dset = CIFARCorrupted(ds, root, corruption, severity)
    idx = np.arange(len(dset))
    if n is not None and n < len(idx):
        idx = np.random.default_rng(seed).choice(idx, size=n, replace=False)
    xs = torch.stack([dset[i][0] for i in idx])
    ys = torch.tensor([dset[i][1] for i in idx])
    return xs, ys
