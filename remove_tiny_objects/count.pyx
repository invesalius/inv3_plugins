# distutils: language = c++

import numpy as np
cimport numpy as np
cimport cython
from cython.parallel import prange
from libcpp.vector cimport vector
from libcpp cimport bool

ctypedef fused label_t:
    np.int16_t
    np.int32_t
    np.int64_t


@cython.boundscheck(False) # turn of bounds-checking for entire function
@cython.cdivision(True)
@cython.wraparound(False)
cdef void _count(label_t[:, :, :] image, int number_regions, np.uint32_t[:, :, :] out):
    cdef unsigned int dx, dy, dz, x, y, z
    cdef np.uint32_t[:] counts = np.zeros(number_regions, dtype=np.uint32)
    dx = image.shape[2]
    dy = image.shape[1]
    dz = image.shape[0]

    for z in range(dz):
        for y in range(dy):
            for x in range(dx):
                counts[image[z, y, x]] += 1


    for z in range(dz):
        for y in range(dy):
            for x in range(dx):
                out[z, y, x] = counts[image[z, y, x]]



def count_regions(label_t[:, :, :] image, int number_regions):
    cdef np.uint32_t[:, :, :] out = np.zeros_like(image, dtype=np.uint32)
    _count(image, number_regions, out)
    return np.asarray(out)
