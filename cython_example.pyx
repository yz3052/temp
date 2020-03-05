cimport cython
import numpy as np
from numpy cimport ndarray, int_t, float64_t, long_t




def test_max(ndarray[float64_t, ndim=1] a):

    cdef double t_max = a[0]
    cdef double t_min = a[0]
    
    cdef int_t i
    for i in range(1,len(a)):
        if a[i] >= t_max:
            t_max = a[i]
        if a[i] <= t_max:
            t_min = a[i]
    
    return t_max, t_min


def test_max_np(ndarray[float64_t, ndim=1] a):

    return a.max(), a.min()