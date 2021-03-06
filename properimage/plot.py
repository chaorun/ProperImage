#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  plot.py
#
#  Copyright 2017 Bruno S <bruno@oac.unc.edu.ar>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

"""plot module from ProperImage,
for coadding astronomical images.

Written by Bruno SANCHEZ

PhD of Astromoy - UNC
bruno@oac.unc.edu.ar

Instituto de Astronomia Teorica y Experimental (IATE) UNC
Cordoba - Argentina

Of 301
"""

import numpy as np

import matplotlib.pyplot as plt

font = {'family'    : 'sans-serif',
        'sans-serif': ['Computer Modern Sans serif'],
        'weight'    : 'regular',
        'size'      : 12}

text = {'usetex'    : True}

plt.rc('font', **font)
plt.rc('text', **text)


def primes(n):
    divisors = [d for d in range(2, n//2+1) if n % d == 0]
    prims = [d for d in divisors if
             all(d % od != 0 for od in divisors if od != d)]
    if len(prims) is 0:
        return n
    else:
        return max(prims)


def plot_psfbasis(psf_basis, path=None, nbook=False, size=4, **kwargs):
    psf_basis.reverse()
    N = len(psf_basis)
    p = primes(N)
    if N == 2:
        subplots = (2, 1)
    elif p == N:
        subplots = (np.rint(np.sqrt(N)),  np.rint(np.sqrt(N)))
    else:
        subplots = (N/float(p), p)

    plt.figure(figsize=(size*subplots[0], size*subplots[1]))
    for i in range(len(psf_basis)):
        plt.subplot(subplots[1], subplots[0], i+1)
        plt.imshow(psf_basis[i], interpolation='none', cmap='viridis')
        plt.title(r'$p_i, i = {}$'.format(i+1))  # , interpolation='linear')
        plt.tight_layout()
        # plt.colorbar(shrink=0.85)
    if path is not None:
        plt.savefig(path)
    if not nbook:
        plt.close()

    return


def plot_afields(a_fields, shape, path=None, nbook=False, size=4, **kwargs):
    if a_fields is None:
        print 'No a_fields were calculated. Only one Psf Basis'
        return
    a_fields.reverse()
    N = len(a_fields)
    p = primes(N)
    if N == 2:
        subplots = (2, 1)
    elif p == N:
        subplots = (np.rint(np.sqrt(N)),  np.rint(np.sqrt(N)))
    else:
        subplots = (N/float(p), p)

    plt.figure(figsize=(size*subplots[0], size*subplots[1]), **kwargs)
    x, y = np.mgrid[:shape[0], :shape[1]]
    for i in range(len(a_fields)):
        plt.subplot(subplots[1], subplots[0], i+1)
        plt.imshow(a_fields[i](x, y), cmap='viridis')
        plt.title(r'$a_i, i = {}$'.format(i+1))
        plt.tight_layout()
        # plt.colorbar(shrink=0.85, aspect=30)
    if path is not None:
        plt.savefig(path)
    if not nbook:
        plt.close()
    return


def plot_S(S, path=None, nbook=False):
    if isinstance(S, np.ma.masked_array):
        S = S.filled()
    plt.imshow(np.log10(S), interpolation='none', cmap='viridis')
    plt.tight_layout()
    plt.colorbar()
    if path is not None:
        plt.savefig(path)
    else:
        plt.show()
    if not nbook:
        plt.close()
    return


def plot_R(R, path=None, nbook=False):
    if isinstance(R[0, 0], np.complex):
        R = R.real
    if isinstance(R, np.ma.masked_array):
        R = R.filled()
    plt.imshow(np.log10(R), interpolation='none', cmap='viridis')
    plt.tight_layout()
    plt.colorbar()
    if path is not None:
        plt.savefig(path)
    else:
        plt.show()
    if not nbook:
        plt.close()
    return
