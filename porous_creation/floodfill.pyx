#cython: language_level=3str

import numpy as np
cimport numpy as np
cimport cython

from collections import deque

from cython.parallel import prange
from libc.math cimport floor, ceil
from libcpp cimport bool
from libcpp.deque cimport deque as cdeque
from libcpp.vector cimport vector
from libc.stdlib cimport abs

cdef struct s_coord:
    int x
    int y
    int z
    int sx
    int sy
    int sz

ctypedef s_coord coord


@cython.boundscheck(False) # turn of bounds-checking for entire function
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
def jump_flooding(int number_sites, int size_x=250, int size_y=250, int size_z=250, bool normalize=True):
    cdef np.ndarray[np.float32_t, ndim=3] image_voronoy = np.zeros((size_z, size_y, size_x), dtype=np.float32)
    cdef np.ndarray[np.int32_t, ndim=3] map_owners = np.zeros((size_z, size_y, size_x), dtype=np.int32)
    cdef np.ndarray[np.int32_t, ndim=2] sites = np.random.randint((0, 0, 0), (size_z, size_y, size_x), (number_sites, 3), dtype=np.int32)
    cdef np.ndarray[np.int32_t, ndim=1] counts = np.zeros(number_sites, dtype=np.int32)
    cdef np.ndarray[np.int32_t, ndim=2] new_sites = np.zeros((number_sites, 3), dtype=np.int32)
    cdef np.ndarray[np.float32_t, ndim=1] max_dists = np.zeros(number_sites, dtype=np.float32)

    cdef int n_steps = int(np.log2(max(size_x, size_y, size_z)))
    cdef int offset_x = size_x // 2
    cdef int offset_y = size_y // 2
    cdef int offset_z = size_z // 2
    cdef int i, z, y, x, zi, yi, xi, sz, sy, sx, z0, y0, x0, z1, y1, x1, idx0, idx1
    cdef float dist0, dist1

    for i in range(number_sites):
        z = sites[i, 0]
        y = sites[i, 1]
        x = sites[i, 2]
        map_owners[z, y, x] = i + 1

    for i in range(n_steps):
        for z in prange(size_z, nogil=True):
            for y in range(size_y):
                for x in range(size_x):

                    for zi in range(-1, 2):
                        for yi in range(-1, 2):
                            for xi in range(-1, 2):

                                if xi == 0 and yi == 0 and zi == 0:
                                    continue

                                sz = z + zi*offset_z
                                sy = y + yi*offset_y
                                sx = x + xi*offset_x

                                if 0 <= sz < size_z and 0 <= sy < size_y and 0 <= sx < size_x:
                                    idx0 = map_owners[z, y, x]
                                    idx1 = map_owners[sz, sy, sx]

                                    if idx1 > 0:
                                        z1 = sites[idx1 - 1, 0]
                                        y1 = sites[idx1 - 1, 1]
                                        x1 = sites[idx1 - 1, 2]

                                        dist0 = image_voronoy[z, y, x]
                                        dist1 = ((z - z1)**2 + (y - y1)**2 + (x - x1)**2)**0.5
                                        if idx0 > 0:
                                            if dist1 < dist0:
                                                map_owners[z, y, x] = idx1
                                                z0 = sites[idx1 - 1, 0]
                                                y0 = sites[idx1 - 1, 1]
                                                x0 = sites[idx1 - 1, 2]
                                                image_voronoy[z, y, x] = dist1
                                        else:
                                            image_voronoy[z, y, x] = dist1
                                            map_owners[z, y, x] = idx1
        offset_x = offset_x // 2
        offset_y = offset_y // 2
        offset_z = offset_z // 2

    if normalize:
        print("finding centers")
        for z in range(size_z):
            for y in range(size_y):
                for x in range(size_x):
                    idx0 = map_owners[z, y, x] - 1
                    counts[idx0] += 1
                    new_sites[idx0, 0] += z
                    new_sites[idx0, 1] += y
                    new_sites[idx0, 2] += x

        print("setting centers")
        for i in range(number_sites):
            if counts[i] > 0:
                new_sites[i, 0] /= counts[i]
                new_sites[i, 1] /= counts[i]
                new_sites[i, 2] /= counts[i]

        print("recalculating dists")
        for z in range(size_z):
            for y in range(size_y):
                for x in range(size_x):
                    idx0 = map_owners[z, y, x] - 1
                    z0 = new_sites[idx0, 0]
                    y0 = new_sites[idx0, 1]
                    x0 = new_sites[idx0, 2]
                    image_voronoy[z, y, x] = ((z - z0)**2 + (y - y0)**2 + (x - x0)**2)**0.5
                    max_dists[idx0] = max(max_dists[idx0], image_voronoy[z, y, x])

        print("Normalizing")
        for z in range(size_z):
            for y in range(size_y):
                for x in range(size_x):
                    idx0 = map_owners[z, y, x] - 1
                    image_voronoy[z, y, x] /= max_dists[idx0]

    return image_voronoy


@cython.boundscheck(False) # turn of bounds-checking for entire function
@cython.wraparound(False)
@cython.nonecheck(False)
def floodfill_voronoy(np.ndarray[np.float32_t, ndim=3] data, list seeds, np.ndarray[np.uint8_t, ndim=3] strct, int distance):
    cdef int x, y, z, sx, sy, sz
    cdef int dx, dy, dz
    cdef int odx, ody, odz
    cdef int xo, yo, zo
    cdef int i, j, k
    cdef int offset_x, offset_y, offset_z
    cdef float dist

    assert(distance <= 1, "Distance not available")

    dz = data.shape[0]
    dy = data.shape[1]
    dx = data.shape[2]

    odz = strct.shape[0]
    ody = strct.shape[1]
    odx = strct.shape[2]

    cdef cdeque[coord] stack
    cdef coord c

    offset_z = odz // 2
    offset_y = ody // 2
    offset_x = odx // 2

    for i, j, k in seeds:
        c.x = i
        c.y = j
        c.z = k
        c.sx = i
        c.sy = j
        c.sz = k

        stack.push_back(c)

    with nogil:
        while stack.size():
            c = stack.back()
            stack.pop_back()

            x = c.x
            y = c.y
            z = c.z
            sx = c.sx
            sy = c.sy
            sz = c.sz

            if distance == 0:
                dist = ((x - sx)**2 + (y - sy)**2 + (z - sz)**2)**0.5
            elif distance == 1:
                dist = abs(x - sx) + abs(y - sy) + abs(z - sz)
            if data[z, y, x] == -1 or dist < data[z, y, x]:
                data[z, y, x] = dist
                for k in xrange(odz):
                    zo = z + k - offset_z
                    for j in xrange(ody):
                        yo = y + j - offset_y
                        for i in xrange(odx):
                            xo = x + i - offset_x
                            if strct[k, j, i] and 0 <= xo < dx and 0 <= yo < dy and 0 <= zo < dz:
                                xo = x + i - offset_x
                                c.x = xo
                                c.y = yo
                                c.z = zo
                                c.sx = sx
                                c.sy = sy
                                c.sz = sz
                                stack.push_back(c)
