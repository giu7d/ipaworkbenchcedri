import numpy as np
from scipy.spatial import distance as dist
import math


def order_points(pts):
    x_sorted = pts[np.argsort(pts[:, 0]), :]

    left_most = x_sorted[:2, :]
    right_most = x_sorted[2:, :]

    left_most = left_most[np.argsort(left_most[:, 1]), :]
    (tl, bl) = left_most

    D = dist.cdist(tl[np.newaxis], right_most, "euclidean")[0]
    (br, tr) = right_most[np.argsort(D)[::-1], :]

    return np.array([tl, tr, br, bl], dtype="float32")


def distance(p1, p2):
    d = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))
    return d


def rotate_axis(point, angle):
    nx = (point[0] * math.cos(angle)) + (point[1] * math.sin(angle))
    ny = (-point[0] * math.sin(angle)) + (point[1] * math.cos(angle))
    return [nx, ny]
