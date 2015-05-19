#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test suite for the functions module of the pyunlocbox package.
"""

import sys
import numpy as np
import numpy.testing as nptest
from pyunlocbox import functions, solvers

# Use the unittest2 backport on Python 2.6 to profit from the new features.
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class FunctionsTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_solve(self):
        """
        Test some features of the solving function.
        """
        y = 5 - 10 * np.random.uniform(size=(15, 4))
        x0 = np.zeros(y.shape)
        param = {'x0': x0, 'verbosity': 'NONE'}

        # Function verbosity.
        f = functions.dummy()
        self.assertEqual(f.verbosity, 'NONE')
        f.verbosity = 'LOW'
        solvers.solve([f], **param)
        self.assertEqual(f.verbosity, 'LOW')

        # Input parameters.
        self.assertRaises(ValueError, solvers.solve, [f], x0, verbosity='??')

        # Addition of dummy function.
        param['maxit'] = 1
        self.assertRaises(ValueError, solvers.solve, [], **param)
        solver = solvers.forward_backward()
        solvers.solve([f], solver=solver, **param)
        self.assertIsInstance(solver.f1, functions.dummy)
        self.assertIsInstance(solver.f2, functions.dummy)

        # Automatic solver selection.
        f0 = functions.func()
        f0._eval = lambda x: 0
        f0._grad = lambda x: x
        f1 = functions.func()
        f1._eval = lambda x: 0
        f1._grad = lambda x: x
        f1._prox = lambda x, T: x
        f2 = functions.func()
        f2._eval = lambda x: 0
        f2._prox = lambda x, T: x
        self.assertRaises(ValueError, solvers.solve, [f0, f0], **param)
        ret = solvers.solve([f0, f1], **param)
        self.assertEqual(ret['solver'], 'forward_backward')
        ret = solvers.solve([f1, f0], **param)
        self.assertEqual(ret['solver'], 'forward_backward')
        ret = solvers.solve([f1, f2], **param)
        self.assertEqual(ret['solver'], 'forward_backward')
        ret = solvers.solve([f2, f2], **param)
        self.assertEqual(ret['solver'], 'douglas_rachford')
        ret = solvers.solve([f1, f2, f0], **param)
        self.assertEqual(ret['solver'], 'generalized_forward_backward')

        # Stopping criteria.
        f = functions.norm_l2(y=y)
        atol = 1e-6
        r = solvers.solve([f], x0, None, atol, None, None, None, None, 'NONE')
        self.assertEqual(r['crit'], 'ATOL')
        self.assertLess(np.sum(r['objective'][-1]), atol)
        dtol = 1e-8
        r = solvers.solve([f], x0, None, None, dtol, None, None, None, 'NONE')
        self.assertEqual(r['crit'], 'DTOL')
        err = np.abs(np.sum(r['objective'][-1]) - np.sum(r['objective'][-2]))
        self.assertLess(err, dtol)
        rtol = .1
        r = solvers.solve([f], x0, None, None, None, rtol, None, None, 'NONE')
        self.assertEqual(r['crit'], 'RTOL')
        err = np.abs(np.sum(r['objective'][-1]) - np.sum(r['objective'][-2]))
        err /= np.sum(r['objective'][-1])
        self.assertLess(err, rtol)
        xtol = 1e-4
        r = solvers.solve([f], x0, None, None, None, None, xtol, None, 'NONE')
        self.assertEqual(r['crit'], 'XTOL')
        r2 = solvers.solve([f], x0, maxit=r['niter']-1, verbosity='NONE')
        err = np.linalg.norm(r['sol'] - r2['sol']) / x0.size
        self.assertLess(err, xtol)
        maxit = 15
        r = solvers.solve([f], x0, None, None, None, None, None, maxit, 'NONE')
        self.assertEqual(r['crit'], 'MAXIT')
        self.assertEqual(r['niter'], maxit)

        # Return values.
        f = functions.norm_l2(y=y)
        ret = solvers.solve([f], **param)
        self.assertEqual(len(ret), 6)
        self.assertIsInstance(ret['sol'], np.ndarray)
        self.assertIsInstance(ret['solver'], str)
        self.assertIsInstance(ret['crit'], str)
        self.assertIsInstance(ret['niter'], int)
        self.assertIsInstance(ret['time'], float)
        self.assertIsInstance(ret['objective'], list)

    def test_forward_backward_fista(self):
        """
        Test FISTA algorithm of forward-backward solver with L1-norm, L2-norm
        and dummy functions.
        """
        y = [4, 5, 6, 7]
        x0 = np.zeros(len(y))
        solver = solvers.forward_backward(method='FISTA')
        param = {'x0': x0, 'solver': solver}
        param['atol'] = 1e-5
        param['verbosity'] = 'NONE'

        # L2-norm prox and dummy gradient.
        f1 = functions.norm_l2(y=y)
        f2 = functions.dummy()
        sol = [3.99996922, 4.99996153, 5.99995383, 6.99994614]
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], sol)
        self.assertEqual(ret['crit'], 'ATOL')
        self.assertEqual(ret['niter'], 10)

        # Dummy prox and L2-norm gradient.
        f1 = functions.dummy()
        f2 = functions.norm_l2(y=y, lambda_=0.6)
        sol = [3.99867319, 4.99834148, 5.99800978, 6.99767808]
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], sol)
        self.assertEqual(ret['crit'], 'ATOL')
        self.assertEqual(ret['niter'], 10)

        # L2-norm prox and L2-norm gradient.
        f1 = functions.norm_l2(y=y)
        f2 = functions.norm_l2(y=y)
        sol = [3.99904855, 4.99881069, 5.99857282, 6.99833496]
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], sol)
        self.assertEqual(ret['crit'], 'MAXIT')

        # L1-norm prox and dummy gradient.
        f1 = functions.norm_l1(y=y)
        f2 = functions.dummy()
        sol = y
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], sol)
        self.assertEqual(ret['crit'], 'ATOL')
        self.assertEqual(ret['niter'], 6)

        # Dummy prox and L1-norm gradient. As L1-norm possesses no gradient,
        # the algorithm exchanges the functions : exact same solution.
        f1 = functions.dummy()
        f2 = functions.norm_l1(y=y)
        sol = y
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], sol)
        self.assertEqual(ret['crit'], 'ATOL')
        self.assertEqual(ret['niter'], 6)

        # L1-norm prox and L1-norm gradient. L1-norm possesses no gradient.
        f1 = functions.norm_l1(y=y)
        f2 = functions.norm_l1(y=y)
        self.assertRaises(ValueError, solvers.solve, [f1, f2], **param)

        # L1-norm prox and L2-norm gradient.
        f1 = functions.norm_l1(y=y, lambda_=1.0)
        f2 = functions.norm_l2(y=y, lambda_=0.8)
        sol = y
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], sol)
        self.assertEqual(ret['crit'], 'ATOL')
        self.assertEqual(ret['niter'], 4)

    def test_forward_backward_ista(self):
        """
        Test ISTA algorithm of forward-backward solver with L1-norm, L2-norm
        and dummy functions. Test the effect of step and lambda parameters.
        """
        y = [4, 5, 6, 7]
        x0 = np.zeros(len(y))
        # Smaller step size and update rate --> slower convergence.
        solver = solvers.forward_backward(method='ISTA', step=.8, lambda_=.5)
        param = {'x0': x0, 'solver': solver}
        param['atol'] = 1e-5
        param['verbosity'] = 'NONE'

        # L2-norm prox and dummy gradient.
        f1 = functions.norm_l2(y=y)
        f2 = functions.dummy()
        sol = [3.99915094, 4.99893867, 5.9987264, 6.99851414]
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], sol)
        self.assertEqual(ret['crit'], 'ATOL')
        self.assertEqual(ret['niter'], 23)

        # L1-norm prox and L2-norm gradient.
        f1 = functions.norm_l1(y=y, lambda_=1.0)
        f2 = functions.norm_l2(y=y, lambda_=0.8)
        sol = [3.99999825, 4.9999979, 5.99999756, 6.99999723]
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], sol)
        self.assertEqual(ret['crit'], 'ATOL')
        self.assertEqual(ret['niter'], 21)

    def test_douglas_rachford(self):
        """
        Test douglas-rachford solver with L1-norm, L2-norm and dummy functions.
        """
        y = [4, 5, 6, 7]
        x0 = np.zeros(len(y))
        solver = solvers.douglas_rachford()
        param = {'x0': x0, 'solver': solver, 'verbosity': 'NONE'}

        # L2-norm prox and dummy prox.
        f1 = functions.norm_l2(y=y)
        f2 = functions.dummy()
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], y)
        self.assertEqual(ret['crit'], 'RTOL')
        self.assertEqual(ret['niter'], 35)

        # L2-norm prox and L1-norm prox.
        f1 = functions.norm_l2(y=y)
        f2 = functions.norm_l1(y=y)
        ret = solvers.solve([f1, f2], **param)
        nptest.assert_allclose(ret['sol'], y)
        self.assertEqual(ret['crit'], 'RTOL')
        self.assertEqual(ret['niter'], 4)

    def test_generalized_forward_backward(self):
        """
        Test the generalized forward-backward algorithm.
        """
        y = [4, 5, 6, 7]
        x0 = np.zeros(len(y))
        L = 4
        solver = solvers.generalized_forward_backward(step=.9/L, lambda_=.8)
        params = {'x0': x0, 'solver':solver, 'verbosity': 'NONE'}

        # Functions .
        f1 = functions.norm_l1(y=y, lambda_=.7)  # Smooth.
        f2 = functions.norm_l2(y=y, lambda_=L/2.)  # Non-smooth.

        # Solve with 1 smooth and 1 non-smooth.
        ret = solvers.solve([f1, f2], **params)
        nptest.assert_allclose(ret['sol'], y)

        # Solve with 1 smooth.
        ret = solvers.solve([f1], **params)
        nptest.assert_allclose(ret['sol'], y)

        # Solve with 1 non-smooth.
        ret = solvers.solve([f2], **params)
        nptest.assert_allclose(ret['sol'], y)

        # Solve with 1 smooth and 2 non-smooth.
        ret = solvers.solve([f1, f2, f2], **params)
        nptest.assert_allclose(ret['sol'], y)

        # Solve with 2 smooth and 2 non-smooth.
        ret = solvers.solve([f2, f1, f2, f1], **params)
        nptest.assert_allclose(ret['sol'], y)


suite = unittest.TestLoader().loadTestsFromTestCase(FunctionsTestCase)


def run():
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    run()
