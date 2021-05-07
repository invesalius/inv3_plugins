import numpy as np
from scipy import ndimage as nd
import random

from . import floodfill


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


def create_voronoy(sx=256, sy=256, sz=256, number_sites=1000, normalize=False):
    #  image = np.zeros((sz, sy, sx), dtype=np.float32)
    #  image[:] = -1
    #  sites = [(random.randrange(0, sx), random.randrange(0, sy), random.randrange(0, sz)) for i in range(number_sites)]
    image = floodfill.jump_flooding(number_sites, sx, sy, sz, normalize)
    print(image.min(), image.max())
    return image
