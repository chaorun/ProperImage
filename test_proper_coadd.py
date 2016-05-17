# -*- coding: utf-8 -*-
"""
Created on Fri May 13 17:06:14 2016

@author: bruno
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import stats

from imsim import simtools
import propercoadd as pc


N = 128  # side

#x = [np.random.randint(low=10, high=N-10) for j in range(100)]
#y = [np.random.randint(low=10, high=N-10) for j in range(100)]
#xy = [(x[i], y[i]) for i in range(100)]

m = simtools.delta_point(N, center=True)

im = simtools.image(m*10000, N, t_exp=1, FWHM=5, SN=10, bkg_pdf='gaussian')

plt.imshow(im)
plt.show()

