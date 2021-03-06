#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  image_stats.py
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
"""image_ensemble module from ProperImage,
for coadding astronomical images.

Written by Bruno SANCHEZ

PhD of Astromoy - UNC
bruno@oac.unc.edu.ar

Instituto de Astronomia Teorica y Experimental (IATE) UNC
Cordoba - Argentina

Of 301
"""

from multiprocessing import Queue
from collections import MutableSequence

import numpy as np

from astropy.io import fits

from . import utils
from .combinator import Combinator
from .single_image import SingleImage
from .utils import chunk_it

try:
    import cPickle as pickle
except:
    import pickle

try:
    import pyfftw
    _fftwn = pyfftw.interfaces.numpy_fft.fftn
    _ifftwn = pyfftw.interfaces.numpy_fft.ifftn
except:
    _fftwn = np.fft.fft2
    _ifftwn = np.fft.ifft2


class ImageEnsemble(MutableSequence):
    """Processor for several images that uses SingleImage as an atomic processing
    unit. It deploys the utilities provided in the mentioned class and combines
    the results, making possible to coadd and subtract astronomical images with
    optimal techniques.

    Parameters
    ----------
    imgpaths: List or tuple of path of images. At this moment it should be a
    fits file for each image.

    Returns
    -------
    An instance of ImageEnsemble

    """
    def __init__(self, imgpaths, pow_th=0.9, *arg, **kwargs):
        super(ImageEnsemble, self).__init__(*arg, **kwargs)
        self.imgl = imgpaths
        self.pow_th = pow_th
        self.global_shape = fits.getdata(imgpaths[0]).shape
        print self.global_shape

    def __setitem__(self, i, v):
        self.imgl[i] = v

    def __getitem__(self, i):
        return self.imgl[i]

    def __delitem__(self, i):
        del self.imgl[i]

    def __len__(self):
        return len(self.imgl)

    def insert(self, i, v):
        self.imgl.insert(i, v)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._clean()

    @property
    def atoms(self):
        """Property method.
        Transforms the list of images into a list of 'atoms'
        that are instances of the SingleImage class.
        This atoms are capable of compute statistics of Psf on every image,
        and are the main unit of image processing.

        Parameters
        ----------
        None parameters are passed, it is a property.

        Returns
        -------
        A list of instances of SingleImage class, one per each image in the
        list of images passed to ImageEnsemble.

        """
        if not hasattr(self, '_atoms'):
            self._atoms = [SingleImage(im, imagefile=True, pow_th=self.pow_th)
                           for im in self.imgl]
        elif len(self._atoms) is not len(self.imgl):
            self._atoms = [SingleImage(im, imagefile=True, pow_th=self.pow_th)
                           for im in self.imgl]
        return self._atoms

    @property
    def transparencies(self):
        zps, meanmags = utils.transparency(self.atoms)
        self._zps = zps
        for j, anatom in enumerate(self.atoms):
            anatom.zp = zps[j]
        return self._zps

    def calculate_S(self, n_procs=2):
        """Method for properly coadding images given by Zackay & Ofek 2015
        (http://arxiv.org/abs/1512.06872, and http://arxiv.org/abs/1512.06879)
        It uses multiprocessing for parallelization of the processing of each
        image.

        Parameters
        ----------
        n_procs: int
            number of processes for computational parallelization. Should not
            be greater than the number of cores of the machine.

        Returns
        -------
        S: np.array 2D of floats
            S image, calculated by the SingleImage method s_component.

        """
        queues = []
        procs = []
        for chunk in chunk_it(self.atoms, n_procs):
            queue = Queue()
            proc = Combinator(chunk, queue, stack=True, fourier=False)
            print 'starting new process'
            proc.start()

            queues.append(queue)
            procs.append(proc)

        print 'all chunks started, and procs appended'

        S = np.zeros(self.global_shape)
        for q in queues:
            serialized = q.get()
            print 'loading pickles'
            s_comp = pickle.loads(serialized)

            S = np.ma.add(s_comp, S)

        print 'S calculated, now starting to join processes'

        for proc in procs:
            print 'waiting for procs to finish'
            proc.join()

        print 'processes finished, now returning S'
        return S

    def calculate_R(self, n_procs=2, return_S=False, debug=False):
        """Method for properly coadding images given by Zackay & Ofek 2015
        (http://arxiv.org/abs/1512.06872, and http://arxiv.org/abs/1512.06879)
        It uses multiprocessing for parallelization of the processing of each
        image.

        Parameters
        ----------
        n_procs: int
            number of processes for computational parallelization. Should not
            be greater than the number of cores of the machine.

        Returns
        -------
        R: np.array 2D of floats
            R image, calculated by the ImageEnsemble method.

        """
        queues = []
        procs = []
        for chunk in chunk_it(self.atoms, n_procs):
            queue = Queue()
            proc = Combinator(chunk, queue, fourier=True, stack=False)
            print 'starting new process'
            proc.start()

            queues.append(queue)
            procs.append(proc)

        print 'all chunks started, and procs appended'

        S_stk = []
        S_hat_stk = []

        for q in queues:
            serialized = q.get()
            print 'loading pickles'
            s_list, s_hat_list = pickle.loads(serialized)

            S_stk.extend(s_list)
            S_hat_stk.extend(s_hat_list)

        S_stack = np.stack(S_stk, axis=-1)
        # S_stack = np.tensordot(S_stack, self.transparencies, axes=(-1, 0))

        S_hat_stack = np.stack(S_hat_stk, axis=-1)

        # real_s_hat = S_hat_stack.real
        # imag_s_hat = S_hat_stack.imag

        # real_std = np.ma.std(real_s_hat, axis=2)
        # imag_std = np.ma.std(imag_s_hat, axis=2)

        # hat_std = real_std + 1j* imag_std

        S = np.ma.sum(S_stack, axis=2)

        # S_hat = _fftwn(S)
        S_hat = np.ma.sum(S_hat_stack, axis=2)

        hat_std = np.ma.std(S_hat_stack, axis=2)
        R_hat = np.ma.divide(S_hat, hat_std)

        R = _ifftwn(R_hat)

        for proc in procs:
            print 'waiting for procs to finish'
            proc.join()

        if debug:
            return [S_hat_stack, S_stack, S_hat, S, R_hat]
        if return_S:
            print 'processes finished, now returning R, S'
            return R, S
        else:
            print 'processes finished, now returning R'
            return R

    def _clean(self):
        """Method to end the sequence processing stage. This is the end
        of the ensemble's life. It empties the memory and cleans the numpydbs
        created for each atom.

        """
        for anatom in self.atoms:
            anatom._clean()
