"""Metode image enhancement + grayscale."""
import cv2
import numpy as np


def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def none(g):
    return g


def hist_eq(g):
    return cv2.equalizeHist(g)


def clahe(g):
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)


def gaussian_unsharp(g):
    blur = cv2.GaussianBlur(g, (0, 0), 2.0)
    return cv2.addWeighted(g, 1.8, blur, -0.8, 0)


def median_denoise(g):
    return cv2.medianBlur(g, 3)


def clahe_unsharp(g):
    return gaussian_unsharp(clahe(median_denoise(g)))


def otsu(g):
    g = cv2.GaussianBlur(g, (3, 3), 0)
    return cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def adaptive(g):
    return cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 15)


METHODS = {
    "none": none,
    "hist_eq": hist_eq,
    "clahe": clahe,
    "gaussian_unsharp": gaussian_unsharp,
    "median_denoise": median_denoise,
    "clahe_unsharp": clahe_unsharp,
    "otsu": otsu,
    "adaptive": adaptive,
}


def apply(g, method):
    return METHODS[method](g)
