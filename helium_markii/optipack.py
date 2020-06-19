#!/usr/bin/env python3

# Made 2020, Mingsong Wu, Kenton Kwok
# mingsongwu [at] outlook [dot] sg
# github.com/starryblack/quVario


### This script provides the montypython object AND minimiss object that handles any calls to monte carlo integration functions and minimisation functions of our design. It interfaces with the python packages installed for basic functionalities (ie mcint)
### optipack should serve helium_markii.py which is the higher level script for direct user interface


### as of 27 may 2020 montypython uses mcint, and minimiss uses scipy fmin functions as main work horses.

### montypython removed, replaced with simple functions because this is the only sane way to be able to numba jit them

import math
import sys
import os
import time
from datetime import datetime


### using sympy methods for symbolic integration. Potentially more precise and convenient (let's not numerically estimate yet)
import numpy as np
import scipy as sp
import scipy.constants as sc
import sympy as sy
from sympy import conjugate, simplify, lambdify, sqrt
from sympy import *
from IPython.display import display
from scipy import optimize, integrate

import matplotlib.pyplot as plt

#### For future monte carlo integration work hopefully
import random
from numba import jit, njit, prange


@njit
def metropolis_hastings(pfunc, iter, alpha, dims):

    # we make steps based on EACH electron, the number of which we calculate from dims/3
    # 'scale' of the problem. this is arbitrary
    s = 3.
    # we discard some initial steps to allow the walkers to reach the distribution
    equi_threshold = 0
    initial_matrix = np.zeros((int(dims/3), 3))
    reject_ratio = 0.
    therm = 1
    test = []
    samples = []

    for i in range(int(dims/3)):
        initial_matrix[i] = 2.*s*np.random.rand(3) - s


    # now sample iter number of points
    for i in range(iter):

        # choose which electron to take for a walk:
        e_index = np.random.randint(0, dims/3)
        trial_matrix = initial_matrix.copy()
        trial_matrix[e_index] += (2.*s*np.random.rand(3) - s)/(dims/3)

        # trial_matrix[e_index] = hi
        proposed_pt = np.reshape(trial_matrix, (1, dims))[0]
        initial_pt = np.reshape(initial_matrix, (1, dims))[0]

        # print(initial_pt)
        p = pfunc(proposed_pt, alpha) / pfunc(initial_pt, alpha)
        if p > np.random.rand():
            initial_matrix = trial_matrix.copy()
            # print(initial_matrix == trial_matrix)

        else:
            reject_ratio += 1./iter

        if i > equi_threshold:
            if (i-therm)%therm == 0:
                test.append(np.reshape(initial_matrix, (1, dims))[0][3])
                samples.append(np.reshape(initial_matrix, (1, dims))[0])

    return samples, reject_ratio, test


@njit
def integrator_mcmc(pfunc, qfunc, sample_iter, walkers, alpha, dims):

    therm = 0
    vals = np.zeros(walkers)
    val_errors = 0.
    test = []
    for i in range(walkers):
        mc_samples, rejects, p  = metropolis_hastings(pfunc, sample_iter, alpha, dims)
        sums = 0.

        # obtain arithmetic average of sampled Q values
        for array in mc_samples[therm:]:
            sums += qfunc(array, alpha)
            test.append(qfunc(array, alpha))
        vals[i] = (sums/(sample_iter - therm))
    # also calculate the variance
    vals_squared = np.sum(vals**2)
    vals_avg = np.sum(vals) /walkers
    variance = vals_squared/walkers - (vals_avg) ** 2
    std_error = np.sqrt(variance/walkers)


    print('Iteration cycle complete, result = ', vals_avg, 'error = ', std_error, 'rejects = ', rejects, 'alpha current = ', alpha)
    return vals_avg, std_error, rejects, test, p


#%%%%%%%%%%%









class MiniMiss():

    def __init__(self):
        print('MiniMiss optimisation machine initialised and ready!\n')

    def minimise(self, func, guess, ftol):
        starttime = time.time()

        temp = optimize.fmin(func, guess, full_output = 1, ftol = ftol)

        endtime = time.time()
        elapsedtime = endtime - starttime
        now = datetime.now()
        date_time = now.strftime('%d/%m/%Y %H:%M:%S')
        # just returns datetime of attempt, elapsed time, optimised parameter, optimised value, number of iterations
        return [date_time, elapsedtime, guess, temp[0], temp[1], temp[3]]

    def __enter__(self):
        return self

    def __exit__(self, e_type, e_val, traceback):
        print('\n\nMiniMiss object self-destructing\n\n')
