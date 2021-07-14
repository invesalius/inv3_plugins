import numpy as np
from scipy import ndimage as nd
import random

from . import floodfill


GAUSSIAN_SIGMA = 1.5


def create_schwarzp(method, init_x, end_x, init_y, end_y, init_z, end_z, sx=256, sy=256, sz=256):
    z, y, x = np.ogrid[
        init_z : end_z : complex(0, sz),
        init_y : end_y : complex(0, sy),
        init_x : end_x : complex(0, sx),
    ]
    if method == 'Schwarz P':
        return np.cos(x) + np.cos(y) + np.cos(z)
    elif method == 'Schwarz D':
        return np.sin(x)*np.sin(y)*np.sin(z) + np.sin(x)*np.cos(y)*np.cos(z) + np.cos(x)*np.sin(y)*np.cos(z) + np.cos(x)*np.cos(y)*np.sin(z)
    elif method == 'Gyroid':
        return np.cos(x) * np.sin(y) + np.cos(y) * np.sin(z) + np.cos(z) * np.sin(x)
    elif method == 'Neovius':
        return 3 * (np.cos(x) + np.cos(y) + np.cos(z)) + 4 * np.cos(x) * np.cos(y) * np.cos(z)
    elif method == 'iWP':
        return np.cos(x) * np.cos(y) + np.cos(y) * np.cos(z) + np.cos(z) * np.cos(x) - np.cos(x) * np.cos(y) * np.cos(z)
    elif method == 'P_W_Hybrid':
        return 4.0 * (np.cos(x) * np.cos(y) + np.cos(y) * np.cos(z) + np.cos(z) * np.cos(x)) - 3 * np.cos(x) * np.cos(y) * np.cos(z) + 2.4


def create_blobs(sx=256, sy=256, sz=256, gaussian=5):
    random_image = np.random.random((sz, sy, sx))
    image = nd.gaussian_filter(random_image, sigma=gaussian)
    return image


def create_voronoi(sx=256, sy=256, sz=256, number_sites=1000, normalize=False, border=True):
    distance_map = np.zeros((sz, sy, sx), dtype=np.float32)
    map_owners = np.zeros((sz, sy, sx), dtype=np.int32)
    sites = np.random.randint((0, 0, 0), (sz, sy, sx), (number_sites, 3), dtype=np.int32)
    floodfill.jump_flooding(distance_map, map_owners, sites, normalize)
    if border:
        if sz == 1:
            gy, gx = np.gradient(map_owners[0])
            mag = np.sqrt(gy*gy + gx*gx).reshape(sz, sy, sx)
        else:
            gz, gy, gx = np.gradient(map_owners)
            mag = np.sqrt(gz*gz + gy*gy + gx*gx)
        borders =  mag > 0
        return nd.gaussian_filter(borders.astype(np.float32), GAUSSIAN_SIGMA)
    else:
        return distance_map


def create_voronoi_non_random(sx=256, sy=256, sz=256, nsx=25, nsy=25, nsz=25, normalize=False, noise=False, border=True):
    distance_map = np.zeros((sz, sy, sx), dtype=np.float32)
    map_owners = np.zeros((sz, sy, sx), dtype=np.int32)
    x = np.arange(nsx)
    y = np.arange(nsy)
    z = np.arange(nsz)
    z, y, x = np.meshgrid(z, y, x)
    x = (x.flatten() + 0.5)
    y = (y.flatten() + 0.5)
    z = (z.flatten() + 0.5)
    sites = np.stack((z, y, x), axis=1)
    if noise:
        r_noise = np.random.random(sites.shape) * 0.5 - 0.25
        sites += r_noise
    sites[:, 0] *= (sz / nsz)
    sites[:, 1] *= (sy / nsy)
    sites[:, 2] *= (sx / nsx)
    sites = np.array(sites, dtype=np.int32)
    floodfill.jump_flooding(distance_map, map_owners, sites, normalize)
    if border:
        if sz == 1:
            gy, gx = np.gradient(map_owners[0])
            mag = np.sqrt(gy**2 + gx**2).reshape(sz, sy, sx)
        else:
            gz, gy, gx = np.gradient(map_owners)
            mag = np.sqrt(gz**2 + gy**2 + gx**2)
        borders =  mag > 0
        return nd.gaussian_filter(borders.astype(np.float32), GAUSSIAN_SIGMA)
    else:
        return distance_map
