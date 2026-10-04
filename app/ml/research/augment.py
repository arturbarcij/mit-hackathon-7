"""Capture-protocol augmentation for the "protocol" job.

Noor photographs leaves at the house, on a plain page, in daylight. That brings colour casts,
uneven exposure and soft shadows that the 128 px JMuBEN close-ups do not have. SheetLight adds
those shifts. It works on PIL images with numpy only, and is picklable for Windows DataLoader
workers (no lambdas).
"""
from __future__ import annotations

import random

import numpy as np
from PIL import Image


class SheetLight:
    def __init__(self, p: float = 0.8, shadow_p: float = 0.6):
        self.p = p
        self.shadow_p = shadow_p

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() > self.p:
            return img
        arr = np.asarray(img.convert("RGB"), dtype=np.float32)
        # White balance: daylight, shade and indoor light at the house.
        gains = np.array([random.uniform(0.85, 1.15), random.uniform(0.92, 1.08), random.uniform(0.85, 1.15)],
                         dtype=np.float32)
        arr *= gains
        # Exposure.
        arr *= random.uniform(0.7, 1.3)
        # Soft shadow from a hand, the phone or a door frame, at a random angle.
        if random.random() < self.shadow_p:
            h, w = arr.shape[:2]
            ang = random.uniform(0.0, 2.0 * np.pi)
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            proj = (xx - w / 2.0) * np.cos(ang) + (yy - h / 2.0) * np.sin(ang)
            proj = (proj - proj.min()) / (float(np.ptp(proj)) + 1e-6)
            edge = random.uniform(0.3, 0.7)
            width = random.uniform(0.05, 0.25)
            depth = random.uniform(0.15, 0.45)
            mask = 1.0 / (1.0 + np.exp(-(proj - edge) / width))
            arr *= (1.0 - depth * mask)[..., None]
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def train_transform_for(aug: str):
    """v1's training transform, optionally with SheetLight. Imports train.py lazily (torch)."""
    from torchvision import transforms
    from common import IMAGENET_MEAN, IMAGENET_STD, INPUT_SIZE
    from train import RandomJPEG, RandomMildBlur, train_transform

    if aug == "v1":
        return train_transform()
    if aug != "sheet":
        raise ValueError(f"unknown aug {aug}")
    return transforms.Compose([
        transforms.RandomResizedCrop(INPUT_SIZE, scale=(0.6, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(25),
        transforms.ColorJitter(0.25, 0.25, 0.2, 0.05),
        SheetLight(),
        RandomMildBlur(),
        RandomJPEG(),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
