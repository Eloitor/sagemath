r"""
Univariate Tropical Polynomial Semirings

Tropical polynomial is a polynomial with coefficients from tropical semiring.
Tropical polynomial induces a function which is piecewise-linear and each 
piece has an integer slope. Tropical roots (zeros) of polynomial `P(x)` is 
defined as all points ``x_0`` for which the graph of ``P(x)`` change its slope.
The difference in the slopes of the two pieces adjacent to this root gives 
the order of the corresponding root. This module provides the implementation
of parent and element class for sparse tropical polynomials in one variable.

AUTHORS:

- Verrel Rievaldo Wijaya

EXAMPLES:

Construct a tropical polynomial semiring by first defining a base 
semiring and then inputting it to ``PolynomialRing`` constructor::

    sage: T = TropicalSemiring(QQ, use_min=False)
    sage: R = PolynomialRing(T,'y')
    sage: R
    Tropical Polynomial Semiring in y over Rational Field

We can define the element by giving a list or tuple of coefficients
that begins with constant. This is also the way to create a tropical
polynomial with `0` as coefficient::

    sage: p1 = R([1,4,None,0]); p1
    0*y^3 + 4*y + 1

Create an element by converting from classical polynomial::

    sage: S.<y> = PolynomialRing(QQ)
    sage: p2 = R(y^2+2*y+3); p2
    1*y^2 + 2*y + 3

We can do the addition, multiplication, and evaluation for tropical 
polynomials. When doing evaluation, make sure the input number is tropical.
If not, then it will raise an error::

    sage: p1 + p2
    0*y^3 + 1*y^2 + 4*y + 3
    sage: p1 * p2
    1*y^5 + 2*y^4 + 5*y^3 + 6*y^2 + 7*y + 4
    sage: p1(3)
    Traceback (most recent call last):
    ...
    TypeError: no common canonical parent for objects with parents: 
    'Tropical semiring over Rational Field' and 'Integer Ring'
    sage: p1(T(3))
    9

Beware that when multiplying tropical polynomial with a scalar, it
will raise an error if the scalar is not tropical number::

    sage: 2 * p1
    Traceback (most recent call last):
    ...
    ArithmeticError: cannot negate any non-infinite element
    sage: T(2) * p1
    2*y^3 + 6*y + 3 

We can also find all the tropical roots of tropical polynomial counted
with multiplicity. There will be no tropical root for constant polynomial. 
For a monomial, the tropical root is the additive identity of its base 
tropical semiring::

    sage: p1.roots()
    [-3, 2, 2]
    sage: p2.roots()
    [1, 1]
    sage: p3 = R(1)
    sage: p3.roots()
    []
    sage: p4 = R(y^2)
    sage: p4.roots()
    [-infinity, -infinity]

Even though some tropical polynomials have tropical roots, this does not
neccessarily means it can be factored into its linear factors::

    sage: p1.factor()
    (0) * (0*y^3 + 4*y + 1)
    sage: p2.factor()
    (1) * (0*y + 1)^2

Every tropical polynomial `p(x)` have a corresponding unique tropical 
polynomial `\bar{p}(x)` with the same roots which can be factored. Therefore
this two polynomial determine the same function. We call `\bar{p}(x)` the
tropical polynomial reducible form of `p(x)`::

    sage: p1.tropical_reducible()
    0*y^3 + 2*y^2 + 4*y + 1
    sage: p2.tropical_reducible()
    1*y^2 + 2*y + 3

Check that the induced tropical polynomial function of `p(x)` and its reducible 
form are really equal::

    sage: p1.piecewise_function()
    piecewise(x|-->1 on (-oo, -3], x|-->x + 4 on (-3, 2), x|-->3*x on 
    [2, +oo); x)
    sage: p1.tropical_reducible().piecewise_function()
    piecewise(x|-->1 on (-oo, -3], x|-->x + 4 on (-3, 2), x|-->3*x on 
    (2, +oo); x)

Plot the graph of some tropical polynomials::
    sage: p1.plot()
    sage: plot(p2, xmin=-1, xmax=3)

TESTS:

There is no subtraction for tropical polynomials because element in tropical 
semiring doesn't necessarily have additive inverse::

    sage: -p1
    Traceback (most recent call last):
    ...
    ArithmeticError: cannot negate any non-infinite element

REFERENCES:

    - [Bru2013]_
    - [Fil2017]_

"""

# ****************************************************************************
#       Copyright (C) 2024 Verrel Rievaldo Wijaya <verrelrievaldo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from itertools import combinations
from sage.misc.cachefunc import cached_method

from sage.sets.real_set import RealSet
from sage.symbolic.ring import SR
from sage.structure.unique_representation import UniqueRepresentation
from sage.structure.parent import Parent
from sage.categories.semirings import Semirings
from sage.categories.sets_cat import Sets

from sage.rings.polynomial.polynomial_element_generic import \
Polynomial_generic_sparse
from sage.rings.semirings.tropical_semiring import TropicalSemiring
from sage.rings.polynomial.polynomial_element import Polynomial

class TropicalPolynomial(Polynomial_generic_sparse):
    """
    A generic sparse tropical polynomial.

    The `TropicalPolynomial`` class defines functionality for sparse
    polynomials over any tropical semiring. A sparse polynomial is 
    represented using a dictionary which maps each exponent to the
    corresponding coefficient. The coefficients is a tropical number.
    """                                                                            
    
    def roots(self):
        r"""
        Return the list of all tropical roots of ``self``

        OUTPUT:

        - ``tropical_roots`` -- list; Contains tropical roots of ``self``
         after being sorted counted with multiplicity

        EXAMPLES:

            sage: T = TropicalSemiring(QQ, use_min=True)
            sage: R = PolynomialRing(T, x)
            sage: p1 = R([5,4,1,0,2,4,3]); p1
            3*x^6 + 4*x^5 + 2*x^4 + 0*x^3 + 1*x^2 + 4*x + 5
            sage: p1.roots()
            [-1, -1, -1, 1, 2, 2]
            sage: p2 = R([0, None, 0]); p2
            0*x^2 + 0
            sage: p2.roots()
            [0, 0]

        """
        tropical_roots = []
        if len(self.dict()) == 1:
            exponent = list(self.dict())[0]
            if exponent == 0:
                return tropical_roots
            else:
                return [self.parent().base_ring().zero()]*exponent
        
        R = self.parent().base().base_ring()
        dict_root = {}
        dict_coeff = {i:c.lift() for i,c in self.dict().items()}
        for comb in combinations(dict_coeff, 2):
            index1, index2 = comb[0], comb[1]
            root = (dict_coeff[index1]-dict_coeff[index2])/(index2 - index1)
            val_root = dict_coeff[index1] + index1*root
            check_maks = True
            for key in dict_coeff:
                if key not in comb:
                    val = dict_coeff[key] + key*root
                    if self.base_ring()._use_min:
                        if val < val_root:
                            check_maks = False
                            break
                    else:
                        if val > val_root:
                            check_maks = False
                            break
            if check_maks:
                order = abs(index1-index2)
                if root not in  dict_root:
                    dict_root[root] = order
                else:
                    if order > dict_root[root]:
                        dict_root[root] = order
        
        for root in dict_root:
            tropical_roots += [root] * dict_root[root]
            
        return sorted(tropical_roots)
    
    def tropical_reducible(self):
        r"""
        Return the tropical polynomial which has the same roots as ``self`` but
        which can be reduced to its linear factors

        OUTPUT: TropicalPolynomial

        EXAMPLES:

            sage: T = TropicalSemiring(QQ, use_min=True)
            sage: R = PolynomialRing(T, x)
            sage: p1 = R([5,4,1,0,2,4,3]); p1
            sage: p1.tropical_reducible()
            3*x^6 + 2*x^5 + 1*x^4 + 0*x^3 + 1*x^2 + 3*x + 5 

        """
        from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
        roots = self.roots()
        R = self.parent()
        poly = R(self.dict()[self.degree()].lift())
        for root in roots:
            linear = R([root, 0])
            poly *= linear
        return poly
    
    def factor(self):
        r"""
        Return the factorization of ``self`` into its tropical linear factors

        OUTPUT:

        A Factorization object of ``self``

        EXAMPLES:

            sage: T = TropicalSemiring(QQ, use_min=True)
            sage: R = PolynomialRing(T, x)
            sage: p1 = R([6,3,1,0]); p1
            0*x^3 + 1*x^2 + 3*x + 6
            sage: factor(p1)
            (0) * (0*x + 1) * (0*x + 2) * (0*x + 3)

        Such factorization is not always possible::
        
            sage: p2 = R([4,4,2]); p2
            2*x^2 + 4*x + 4
            sage: p2.factor()
            (2) * (0*x^2 + 2*x + 2)

        """
        from sage.structure.factorization import Factorization

        if self.parent().base()._use_min:
            conjugate = self.concave_conjugate()
        else:
            conjugate = self.convex_conjugate()

        unit = self.dict()[self.degree()]
        if self != conjugate or self.roots() == []:
            factor = [(self*self.parent(-unit.lift()), 1)]
            return Factorization(factor, unit=unit)

        R = self.parent()
        roots_order = {}
        for root in self.roots():
            if root in roots_order:
                roots_order[root] += 1
            else:
                roots_order[root] = 1 
        factors = []
        for root in roots_order:
            factors.append((R([root, 0]), roots_order[root]))
        
        return Factorization(factors, unit=unit)

    def piecewise_function(self):
        r"""
        Return the tropical polynomial function of ``self`` which is a 
        piecewise linear function with the domains are split by roots

        OUTPUT:

        - ``f`` -- a piecewise function

        EXAMPLES:

            sage: T = TropicalSemiring(QQ, use_min=False)
            sage: R = PolynomialRing(T, x)
            sage: p1 = R([4,2,1,3]); p1
            3*x^3 + 1*x^2 + 2*x + 4
            sage: p1.piecewise_function()
            piecewise(x|-->4 on (-oo, 1/3], x|-->3*x + 3 on (1/3, +oo); x)

        A constant tropical polynomial will result in a constant function::

            sage: p2 = R(3)
            sage: p2.piecewise_function()
            3

        A monomial will result in a linear function::

            sage: S.<x> = PolynomialRing(QQ)
            sage: p3 = R(x^3)
            sage: p3.piecewise_function()
            3*x + 1
            
        """
        from sage.symbolic.ring import SR
        from sage.rings.infinity import infinity
        from sage.functions.piecewise import piecewise

        x = SR.var('x')
        R = self.parent().base().base_ring()
        if self.roots() == []:
            # f = R(str(self.dict()[0]))
            f = self.dict()[0].lift()
            return f
        
        if len(self.dict()) == 1:
            gradient = list(self.dict())[0]
            intercept = self.dict()[gradient].lift()
            f = intercept+gradient*x
            return f

        unique_root = sorted(list(set(self.roots())))
        pieces = []
        domain = []
        for i in range(len(unique_root)+1):
            if i == 0:
                test_number = self.base_ring()(unique_root[i]-1)
            elif i == len(unique_root):
                test_number = self.base_ring()(unique_root[i-1]+1)
            else:
                test_number = self.base_ring()((unique_root[i] + \
                                                unique_root[i-1])/2)

            terms = {i:c*(test_number**i) for i, c in self.dict().items()}
            if self.base_ring()._use_min:
                maximum = min(terms.values())
            else:
                maximum = max(terms.values())
            found_key = None
            for key, value in terms.items():
                if value == maximum:
                    found_key = key
                    break
            gradient = found_key
            intercept = self.dict()[found_key].lift()

            if i == 0:
                interval = RealSet.unbounded_below_closed(unique_root[i])
                piecewise_linear = (interval, intercept+gradient*x)
                domain.append(interval)
            elif i == len(unique_root):
                if domain[0][0].upper_closed():
                    interval = RealSet.unbounded_above_open(unique_root[i-1])
                else:
                    interval = RealSet.unbounded_above_closed(unique_root[i-1])
                piecewise_linear = (interval, intercept+gradient*x)
                domain.append(interval)
            else:
                if domain[i-1][0].upper_closed():
                    interval = RealSet((unique_root[i-1], unique_root[i]))
                else:
                    interval = RealSet([unique_root[i-1], unique_root[i]])
                piecewise_linear = (interval, intercept+gradient*x)
                domain.append(interval)
            pieces.append(piecewise_linear)

        f = piecewise(pieces)
        return f
    
    def plot(self, xmin=None, xmax=None):
        r"""
        Return the plot of tropical polynomial function of ``self``

        INPUT:

        - ``xmin`` -- (default: ``None``)
        - ``xmax`` -- (default: ``None``)

        OUTPUT:

        If ``xmin`` and ``xmax`` is given, then it will return a plot
        of piecewise linear function of ``self`` with domain start from
        ``xmin`` to ``xmax``. Otherwise, the domain will start from the
        the minimum root of ``self`` minus 1 to maximum root of ``self``
        plus 1. If the function of ``self`` is constant or linear, then 
        the default domain will be [-1,1].

        EXAMPLES:

        If the tropical semiring use a max-plus algebra, then the graph 
        will be of piecewise linear convex function::

            sage: T = TropicalSemiring(QQ, use_min=False)
            sage: R = PolynomialRing(T, x)
            sage: p1 = R([4,2,1,3]); p1
            3*x^3 + 1*x^2 + 2*x + 4
            sage: p1.roots()
            [1/3, 1/3, 1/3]
            sage: p1.plot()

        A different result will be obtained if the tropical semiring employs 
        a min-plus algebra. Rather, a graph of the piecewise linear concave 
        function will be obtained::

            sage: T = TropicalSemiring(QQ, use_min=True)
            sage: R = PolynomialRing(T, x)
            sage: p1 = R([4,2,1,3])
            sage: p1.roots()
            [-2, 1, 2]
            sage: plot(p1, xmin=-4, xmax=4)
        
        TESTS:

        If ``xmin`` or ``xmax`` is given as an input, then the others also
        have to be given. Otherwise it will raise an error::

            sage: plot(p1, 5)
            Traceback (most recent call last):
            ...
            ValueError: Expected 2 inputs for xmin and xmax, but got 1
        
        The error also occured when ``xmin`` is greater or equal than ``xmax``::

            sage: plot(p1, 5, 3)
            Traceback (most recent call last):
            ...
            ValueError: xmin = 5 should be less than xmax = 3

        """
        from sage.plot.plot import plot
        f = self.piecewise_function()
        if xmin is None and xmax is None:
            roots = sorted(self.roots())
            if roots==[] or self.parent().base().zero() in roots:
                return plot(f, xmin=-1, xmax=1)
            else:
                return plot(f, xmin=roots[0]-1, xmax=roots[-1]+1)
        elif xmin is None or xmax is None:
            raise ValueError(f"Expected 2 inputs for xmin and xmax, but got 1")
        elif (xmin>=xmax):
            raise ValueError(f"xmin = {xmin} should be less than xmax = {xmax}")
        else:
            return plot(f, xmin=xmin, xmax=xmax)
        
    def _repr_(self):
        r"""
        
        EXAMPLES:

            sage: T = TropicalSemiring(QQ)
            sage: R = PolynomialRing(T, 'x')
            sage: R([0,-1,1])
            1*x^2 + -1*x + 0

        """
        s = super()._repr()
        if s[0] == 'x':
            s = "1*" + s
        s = s.replace(" - ", " + -")
        s = s.replace(" + x", " + 1*x")
        s = s.replace(" -", " -1*")
        return s
    
class TropicalPolynomialSemiring(UniqueRepresentation, Parent):
    """
    Semiring structure of tropical polynomials in one variable
    """

    @staticmethod
    def __classcall_private__(cls, base_semiring, names=None):
        if names is None:
           names = 'x'
        if isinstance(names, str):
            names = (names,)
        return super().__classcall__(cls, base_semiring, tuple(names))

    def __init__(self, base_semiring, names):
        """
        EXAMPLES:

            sage: T = TropicalSemiring(QQ, use_min=False)
            sage: R.<x> = PolynomialRing(T)
            sage: x.parent()
            Univariate Tropical Polynomial Semiring in x over Rational Field
            sage: (x + T(1)*x^2) * R(3)
            4*x^2 + 3*x
            sage: TestSuite(R).run()

        """
        if not isinstance(base_semiring, TropicalSemiring):
            raise ValueError(f"{base_semiring} is not a tropical semiring")
        Parent.__init__(self, base=base_semiring, names=names, category=Sets())

    Element = TropicalPolynomial

    def _element_constructor_(self, x, check=True):
        """
        Convert ``x`` into this tropical polynomial semiring
        """
        C = self.element_class
        if isinstance(x, (list, tuple)):
            for i, coeff in enumerate(x):
                if coeff == 0:
                    x[i] = self.base()(0)
        return C(self, x, check=check)

    def _repr_(self):
        return (f"Univariate Tropical Polynomial Semiring in {self.variable_name()}"
            f" over {self.base_ring().base_ring()}")

    
    def gen(self, n=0):
        """
        Return the indeterminate generator of this polynomial ring.
        """
        if n != 0:
            raise IndexError("generator n not defined")
        return self.gens()[n]
    
    @cached_method
    def gens(self):
        """
        Return a tuple whose entries are the generators for this
        object, in order.
        """
        return tuple([self([None,0])])
    
    def ngens(self):
        """
        Return the number of generators of this polynomial ring, which is 1
        since it is a univariate polynomial ring.
        """
        from sage.rings.integer_ring import ZZ
        return ZZ.one()

    def random_element(self, degree=(-1, 2), monic=False, *args, **kwds):
        """
        Return a random polynomial
        """
        from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
        R = PolynomialRing(self.base().base_ring(), self.variable_names())
        return self(R.random_element(degree=degree, monic=monic, *args, **kwds))
    
    def is_sparse(self):
        return True
    
    def interpolation(self, points):
        """
        Return a tropical polynomial with its function goes through each point
        in ``points`` if possible

        INPUT:

        - points -- a list of tuple (x,y)

        EXAMPLES:

            sage: T = TropicalSemiring(QQ, use_min=True)
            sage: R = PolynomialRing(T, 'x')
            sage: points = [(-2,-3),(1,3),(2,4)]
            sage: p1 = R.interpolation(points); p1
            1*x^2 + 2*x + 4
            sage: p1.plot()

        ::

            sage: T = TropicalSemiring(QQ, use_min=False)
            sage: R = PolynomialRing(T,'x')
            sage: points = [(0,0),(1,1),(2,4)]
            sage: p1 = R.interpolation(points); p1
            -2*x^3 + -1*x^2 + 0*x + 0
            sage: p1.plot()
        
        TESTS:

        Every piecewise linear component of tropical polynomial function has
        to have an integer slope::

            sage: T = TropicalSemiring(QQ, use_min=False)
            sage: R = PolynomialRing(T,'x')
            sage: points = [(0,0),(2,3)]
            sage: R.interpolation(points)
            Traceback (most recent call last):
            ...
            ValueError: the slope is not an integer
        
        For max-plus algebra, the slope of the componenets has to be increasing
        as we move from left to right. Conversely for min-plus algebra, the 
        slope of the componenets has to be decreasing from left to right::

            sage: T = TropicalSemiring(QQ, use_min=False)
            sage: R = PolynomialRing(T,'x')
            sage: points = [(-2,-3),(1,3),(2,4)]
            sage: R.interpolation(points)
            Traceback (most recent call last):
            ...
            ValueError: can not interpolate these points
        """
        points = sorted(points, key=lambda point: point[0])
        all_slope = [0]
        roots = {}
        if self.base()._use_min:
            point_order = range(len(points)-1, 0, -1)
        else:
            point_order = range(len(points)-1)
        for i in point_order:
            if self.base()._use_min:
                slope = (points[i-1][1]-points[i][1])/(points[i-1][0]-points[i][0])
            else:
                slope = (points[i+1][1]-points[i][1])/(points[i+1][0]-points[i][0])
            if not slope.is_integer():
                raise ValueError("the slope is not an integer")
            if slope < all_slope[-1]:
                raise ValueError("can not interpolate these points")
            elif slope > all_slope[-1]:
                order = slope - all_slope[-1]
                all_slope.append(slope)
                roots[points[i][0]] = order
        if len(all_slope) == 1: # constant polynomial
            return self(points[0][1])
        
        result = self.zero()
        for root, ord in roots.items():
            result *= self([root,0])**ord
        test_value = result(self.base()(points[0][0]))
        unit = self.base()(points[0][1]-test_value.lift())
        result *= unit
        return result