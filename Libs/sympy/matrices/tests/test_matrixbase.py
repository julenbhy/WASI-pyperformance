import concurrent.futures
import random
from collections.abc import Hashable

from sympy import (
    Abs, Add, Array, DeferredVector, E, Expr, FiniteSet, Float, Function,
    GramSchmidt, I, ImmutableDenseMatrix, ImmutableMatrix,
    ImmutableSparseMatrix, Integer, KroneckerDelta, MatPow, Matrix,
    MatrixSymbol, Max, Min, MutableDenseMatrix, MutableSparseMatrix, Poly, Pow,
    PurePoly, Q, Quaternion, Rational, RootOf, S, SparseMatrix, Symbol, Tuple,
    Wild, banded, casoratian, cos, diag, diff, exp, expand, eye, hessian,
    integrate, log, matrix_multiply_elementwise, nan, ones, oo, pi, randMatrix,
    rot_axis1, rot_axis2, rot_axis3, rot_ccw_axis1, rot_ccw_axis2,
    rot_ccw_axis3, signsimp, simplify, sin, sqrt, sstr, symbols, sympify, tan,
    trigsimp, wronskian, zeros)
from sympy.abc import a, b, c, d, t, x, y, z
from sympy.core.kind import NumberKind, UndefinedKind
from sympy.matrices.determinant import _find_reasonable_pivot_naive
from sympy.matrices.exceptions import (
    MatrixError, NonSquareMatrixError, ShapeError)
from sympy.matrices.kind import MatrixKind
from sympy.matrices.utilities import _dotprodsimp_state, _simplify, dotprodsimp
from sympy.tensor.array.array_derivatives import ArrayDerivative
from sympy.testing.pytest import (
    ignore_warnings, raises, skip, skip_under_pyodide, slow,
    warns_deprecated_sympy)
from sympy.utilities.iterables import capture, iterable
from importlib.metadata import version

all_classes = (Matrix, SparseMatrix, ImmutableMatrix, ImmutableSparseMatrix)
mutable_classes = (Matrix, SparseMatrix)
immutable_classes = (ImmutableMatrix, ImmutableSparseMatrix)


def test__MinimalMatrix():
    x = Matrix(2, 3, [1, 2, 3, 4, 5, 6])
    assert x.rows == 2
    assert x.cols == 3
    assert x[2] == 3
    assert x[1, 1] == 5
    assert list(x) == [1, 2, 3, 4, 5, 6]
    assert list(x[1, :]) == [4, 5, 6]
    assert list(x[:, 1]) == [2, 5]
    assert list(x[:, :]) == list(x)
    assert x[:, :] == x
    assert Matrix(x) == x
    assert Matrix([[1, 2, 3], [4, 5, 6]]) == x
    assert Matrix(([1, 2, 3], [4, 5, 6])) == x
    assert Matrix([(1, 2, 3), (4, 5, 6)]) == x
    assert Matrix(((1, 2, 3), (4, 5, 6))) == x
    assert not (Matrix([[1, 2], [3, 4], [5, 6]]) == x)


def test_kind():
    assert Matrix([[1, 2], [3, 4]]).kind == MatrixKind(NumberKind)
    assert Matrix([[0, 0], [0, 0]]).kind == MatrixKind(NumberKind)
    assert Matrix(0, 0, []).kind == MatrixKind(NumberKind)
    assert Matrix([[x]]).kind == MatrixKind(NumberKind)
    assert Matrix([[1, Matrix([[1]])]]).kind == MatrixKind(UndefinedKind)
    assert SparseMatrix([[1]]).kind == MatrixKind(NumberKind)
    assert SparseMatrix([[1, Matrix([[1]])]]).kind == MatrixKind(UndefinedKind)


def test_todok():
    a, b, c, d = symbols('a:d')
    m1 = MutableDenseMatrix([[a, b], [c, d]])
    m2 = ImmutableDenseMatrix([[a, b], [c, d]])
    m3 = MutableSparseMatrix([[a, b], [c, d]])
    m4 = ImmutableSparseMatrix([[a, b], [c, d]])
    assert m1.todok() == m2.todok() == m3.todok() == m4.todok() == \
        {(0, 0): a, (0, 1): b, (1, 0): c, (1, 1): d}


def test_tolist():
    lst = [[S.One, S.Half, x*y, S.Zero], [x, y, z, x**2], [y, -S.One, z*x, 3]]
    flat_lst = [S.One, S.Half, x*y, S.Zero, x, y, z, x**2, y, -S.One, z*x, 3]
    m = Matrix(3, 4, flat_lst)
    assert m.tolist() == lst


def test_todod():
    m = Matrix([[S.One, 0], [0, S.Half], [x, 0]])
    dict = {0: {0: S.One}, 1: {1: S.Half}, 2: {0: x}}
    assert m.todod() == dict


def test_row_col_del():
    e = ImmutableMatrix(3, 3, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    raises(IndexError, lambda: e.row_del(5))
    raises(IndexError, lambda: e.row_del(-5))
    raises(IndexError, lambda: e.col_del(5))
    raises(IndexError, lambda: e.col_del(-5))

    assert e.row_del(2) == e.row_del(-1) == Matrix([[1, 2, 3], [4, 5, 6]])
    assert e.col_del(2) == e.col_del(-1) == Matrix([[1, 2], [4, 5], [7, 8]])

    assert e.row_del(1) == e.row_del(-2) == Matrix([[1, 2, 3], [7, 8, 9]])
    assert e.col_del(1) == e.col_del(-2) == Matrix([[1, 3], [4, 6], [7, 9]])


def test_get_diag_blocks1():
    a = Matrix([[1, 2], [2, 3]])
    b = Matrix([[3, x], [y, 3]])
    c = Matrix([[3, x, 3], [y, 3, z], [x, y, z]])
    assert a.get_diag_blocks() == [a]
    assert b.get_diag_blocks() == [b]
    assert c.get_diag_blocks() == [c]


def test_get_diag_blocks2():
    a = Matrix([[1, 2], [2, 3]])
    b = Matrix([[3, x], [y, 3]])
    c = Matrix([[3, x, 3], [y, 3, z], [x, y, z]])
    A, B, C, D = diag(a, b, b), diag(a, b, c), diag(a, c, b), diag(c, c, b)
    A = Matrix(A.rows, A.cols, A)
    B = Matrix(B.rows, B.cols, B)
    C = Matrix(C.rows, C.cols, C)
    D = Matrix(D.rows, D.cols, D)

    assert A.get_diag_blocks() == [a, b, b]
    assert B.get_diag_blocks() == [a, b, c]
    assert C.get_diag_blocks() == [a, c, b]
    assert D.get_diag_blocks() == [c, c, b]


def test_row_col():
    m = Matrix(3, 3, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert m.row(0) == Matrix(1, 3, [1, 2, 3])
    assert m.col(0) == Matrix(3, 1, [1, 4, 7])


def test_row_join():
    assert eye(3).row_join(Matrix([7, 7, 7])) == \
           Matrix([[1, 0, 0, 7],
                   [0, 1, 0, 7],
                   [0, 0, 1, 7]])


def test_col_join():
    assert eye(3).col_join(Matrix([[7, 7, 7]])) == \
           Matrix([[1, 0, 0],
                   [0, 1, 0],
                   [0, 0, 1],
                   [7, 7, 7]])


def test_row_insert():
    r4 = Matrix([[4, 4, 4]])
    for i in range(-4, 5):
        l = [1, 0, 0]
        l.insert(i, 4)
        assert eye(3).row_insert(i, r4).col(0).flat() == l


def test_col_insert():
    c4 = Matrix([4, 4, 4])
    for i in range(-4, 5):
        l = [0, 0, 0]
        l.insert(i, 4)
        assert zeros(3).col_insert(i, c4).row(0).flat() == l
    # issue 13643
    assert eye(6).col_insert(3, Matrix([[2, 2], [2, 2], [2, 2], [2, 2], [2, 2], [2, 2]])) == \
           Matrix([[1, 0, 0, 2, 2, 0, 0, 0],
                   [0, 1, 0, 2, 2, 0, 0, 0],
                   [0, 0, 1, 2, 2, 0, 0, 0],
                   [0, 0, 0, 2, 2, 1, 0, 0],
                   [0, 0, 0, 2, 2, 0, 1, 0],
                   [0, 0, 0, 2, 2, 0, 0, 1]])


def test_extract():
    m = Matrix(4, 3, lambda i, j: i*3 + j)
    assert m.extract([0, 1, 3], [0, 1]) == Matrix(3, 2, [0, 1, 3, 4, 9, 10])
    assert m.extract([0, 3], [0, 0, 2]) == Matrix(2, 3, [0, 0, 2, 9, 9, 11])
    assert m.extract(range(4), range(3)) == m
    raises(IndexError, lambda: m.extract([4], [0]))
    raises(IndexError, lambda: m.extract([0], [3]))


def test_hstack():
    m = Matrix(4, 3, lambda i, j: i*3 + j)
    m2 = Matrix(3, 4, lambda i, j: i*3 + j)
    assert m == m.hstack(m)
    assert m.hstack(m, m, m) == Matrix.hstack(m, m, m) == Matrix([
                [0,  1,  2, 0,  1,  2, 0,  1,  2],
                [3,  4,  5, 3,  4,  5, 3,  4,  5],
                [6,  7,  8, 6,  7,  8, 6,  7,  8],
                [9, 10, 11, 9, 10, 11, 9, 10, 11]])
    raises(ShapeError, lambda: m.hstack(m, m2))
    assert Matrix.hstack() == Matrix()

    # test regression #12938
    M1 = Matrix.zeros(0, 0)
    M2 = Matrix.zeros(0, 1)
    M3 = Matrix.zeros(0, 2)
    M4 = Matrix.zeros(0, 3)
    m = Matrix.hstack(M1, M2, M3, M4)
    assert m.rows == 0 and m.cols == 6


def test_vstack():
    m = Matrix(4, 3, lambda i, j: i*3 + j)
    m2 = Matrix(3, 4, lambda i, j: i*3 + j)
    assert m == m.vstack(m)
    assert m.vstack(m, m, m) == Matrix.vstack(m, m, m) == Matrix([
                                [0,  1,  2],
                                [3,  4,  5],
                                [6,  7,  8],
                                [9, 10, 11],
                                [0,  1,  2],
                                [3,  4,  5],
                                [6,  7,  8],
                                [9, 10, 11],
                                [0,  1,  2],
                                [3,  4,  5],
                                [6,  7,  8],
                                [9, 10, 11]])
    raises(ShapeError, lambda: m.vstack(m, m2))
    assert Matrix.vstack() == Matrix()


def test_has():
    A = Matrix(((x, y), (2, 3)))
    assert A.has(x)
    assert not A.has(z)
    assert A.has(Symbol)

    A = Matrix(((2, y), (2, 3)))
    assert not A.has(x)


def test_is_anti_symmetric():
    x = symbols('x')
    assert Matrix(2, 1, [1, 2]).is_anti_symmetric() is False
    m = Matrix(3, 3, [0, x**2 + 2*x + 1, y, -(x + 1)**2, 0, x*y, -y, -x*y, 0])
    assert m.is_anti_symmetric() is True
    assert m.is_anti_symmetric(simplify=False) is False
    assert m.is_anti_symmetric(simplify=lambda x: x) is False

    m = Matrix(3, 3, [x.expand() for x in m])
    assert m.is_anti_symmetric(simplify=False) is True
    m = Matrix(3, 3, [x.expand() for x in [S.One] + list(m)[1:]])
    assert m.is_anti_symmetric() is False


def test_is_hermitian():
    a = Matrix([[1, I], [-I, 1]])
    assert a.is_hermitian
    a = Matrix([[2*I, I], [-I, 1]])
    assert a.is_hermitian is False
    a = Matrix([[x, I], [-I, 1]])
    assert a.is_hermitian is None
    a = Matrix([[x, 1], [-I, 1]])
    assert a.is_hermitian is False


def test_is_symbolic():
    a = Matrix([[x, x], [x, x]])
    assert a.is_symbolic() is True
    a = Matrix([[1, 2, 3, 4], [5, 6, 7, 8]])
    assert a.is_symbolic() is False
    a = Matrix([[1, 2, 3, 4], [5, 6, x, 8]])
    assert a.is_symbolic() is True
    a = Matrix([[1, x, 3]])
    assert a.is_symbolic() is True
    a = Matrix([[1, 2, 3]])
    assert a.is_symbolic() is False
    a = Matrix([[1], [x], [3]])
    assert a.is_symbolic() is True
    a = Matrix([[1], [2], [3]])
    assert a.is_symbolic() is False


def test_is_square():
    m = Matrix([[1], [1]])
    m2 = Matrix([[2, 2], [2, 2]])
    assert not m.is_square
    assert m2.is_square


def test_is_symmetric():
    m = Matrix(2, 2, [0, 1, 1, 0])
    assert m.is_symmetric()
    m = Matrix(2, 2, [0, 1, 0, 1])
    assert not m.is_symmetric()


def test_is_hessenberg():
    A = Matrix([[3, 4, 1], [2, 4, 5], [0, 1, 2]])
    assert A.is_upper_hessenberg
    A = Matrix(3, 3, [3, 2, 0, 4, 4, 1, 1, 5, 2])
    assert A.is_lower_hessenberg
    A = Matrix(3, 3, [3, 2, -1, 4, 4, 1, 1, 5, 2])
    assert A.is_lower_hessenberg is False
    assert A.is_upper_hessenberg is False

    A = Matrix([[3, 4, 1], [2, 4, 5], [3, 1, 2]])
    assert not A.is_upper_hessenberg


def test_values():
    assert set(Matrix(2, 2, [0, 1, 2, 3]
        ).values()) == {1, 2, 3}
    x = Symbol('x', real=True)
    assert set(Matrix(2, 2, [x, 0, 0, 1]
        ).values()) == {x, 1}


def test_conjugate():
    M = Matrix([[0, I, 5],
                [1, 2, 0]])

    assert M.T == Matrix([[0, 1],
                          [I, 2],
                          [5, 0]])

    assert M.C == Matrix([[0, -I, 5],
                          [1,  2, 0]])
    assert M.C == M.conjugate()

    assert M.H == M.T.C
    assert M.H == Matrix([[ 0, 1],
                          [-I, 2],
                          [ 5, 0]])


def test_doit():
    a = Matrix([[Add(x, x, evaluate=False)]])
    assert a[0] != 2*x
    assert a.doit() == Matrix([[2*x]])


def test_evalf():
    a = Matrix(2, 1, [sqrt(5), 6])
    assert all(a.evalf()[i] == a[i].evalf() for i in range(2))
    assert all(a.evalf(2)[i] == a[i].evalf(2) for i in range(2))
    assert all(a.n(2)[i] == a[i].n(2) for i in range(2))


def test_replace():
    F, G = symbols('F, G', cls=Function)
    K = Matrix(2, 2, lambda i, j: G(i+j))
    M = Matrix(2, 2, lambda i, j: F(i+j))
    N = M.replace(F, G)
    assert N == K


def test_replace_map():
    F, G = symbols('F, G', cls=Function)
    M = Matrix(2, 2, lambda i, j: F(i+j))
    N, d = M.replace(F, G, True)
    assert N == Matrix(2, 2, lambda i, j: G(i+j))
    assert d == {F(0): G(0), F(1): G(1), F(2): G(2)}

def test_numpy_conversion():
    try:
        from numpy import array, array_equal
    except ImportError:
        skip('NumPy must be available to test creating matrices from ndarrays')
    A = Matrix([[1,2], [3,4]])
    np_array = array([[1,2], [3,4]])
    assert array_equal(array(A), np_array)
    assert array_equal(array(A, copy=True), np_array)
    if(int(version('numpy').split('.')[0]) >= 2): #run this test only if numpy is new enough that copy variable is passed properly.
        raises(TypeError, lambda: array(A, copy=False))

def test_rot90():
    A = Matrix([[1, 2], [3, 4]])
    assert A == A.rot90(0) == A.rot90(4)
    assert A.rot90(2) == A.rot90(-2) == A.rot90(6) == Matrix(((4, 3), (2, 1)))
    assert A.rot90(3) == A.rot90(-1) == A.rot90(7) == Matrix(((2, 4), (1, 3)))
    assert A.rot90() == A.rot90(-7) == A.rot90(-3) == Matrix(((3, 1), (4, 2)))


def test_subs():
    assert Matrix([[1, x], [x, 4]]).subs(x, 5) == Matrix([[1, 5], [5, 4]])
    assert Matrix([[x, 2], [x + y, 4]]).subs([[x, -1], [y, -2]]) == \
           Matrix([[-1, 2], [-3, 4]])
    assert Matrix([[x, 2], [x + y, 4]]).subs([(x, -1), (y, -2)]) == \
           Matrix([[-1, 2], [-3, 4]])
    assert Matrix([[x, 2], [x + y, 4]]).subs({x: -1, y: -2}) == \
           Matrix([[-1, 2], [-3, 4]])
    assert Matrix([[x*y]]).subs({x: y - 1, y: x - 1}, simultaneous=True) == \
           Matrix([[(x - 1)*(y - 1)]])


def test_permute():
    a = Matrix(3, 4, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    raises(IndexError, lambda: a.permute([[0, 5]]))
    raises(ValueError, lambda: a.permute(Symbol('x')))
    b = a.permute_rows([[0, 2], [0, 1]])
    assert a.permute([[0, 2], [0, 1]]) == b == Matrix([
                                            [5,  6,  7,  8],
                                            [9, 10, 11, 12],
                                            [1,  2,  3,  4]])

    b = a.permute_cols([[0, 2], [0, 1]])
    assert a.permute([[0, 2], [0, 1]], orientation='cols') == b ==\
                            Matrix([
                            [ 2,  3, 1,  4],
                            [ 6,  7, 5,  8],
                            [10, 11, 9, 12]])

    b = a.permute_cols([[0, 2], [0, 1]], direction='backward')
    assert a.permute([[0, 2], [0, 1]], orientation='cols', direction='backward') == b ==\
                            Matrix([
                            [ 3, 1,  2,  4],
                            [ 7, 5,  6,  8],
                            [11, 9, 10, 12]])

    assert a.permute([1, 2, 0, 3]) == Matrix([
                                            [5,  6,  7,  8],
                                            [9, 10, 11, 12],
                                            [1,  2,  3,  4]])

    from sympy.combinatorics import Permutation
    assert a.permute(Permutation([1, 2, 0, 3])) == Matrix([
                                            [5,  6,  7,  8],
                                            [9, 10, 11, 12],
                                            [1,  2,  3,  4]])

def test_upper_triangular():

    A = Matrix([
                [1, 1, 1, 1],
                [1, 1, 1, 1],
                [1, 1, 1, 1],
                [1, 1, 1, 1]
            ])

    R = A.upper_triangular(2)
    assert R == Matrix([
                        [0, 0, 1, 1],
                        [0, 0, 0, 1],
                        [0, 0, 0, 0],
                        [0, 0, 0, 0]
                    ])

    R = A.upper_triangular(-2)
    assert R == Matrix([
                        [1, 1, 1, 1],
                        [1, 1, 1, 1],
                        [1, 1, 1, 1],
                        [0, 1, 1, 1]
                    ])

    R = A.upper_triangular()
    assert R == Matrix([
                        [1, 1, 1, 1],
                        [0, 1, 1, 1],
                        [0, 0, 1, 1],
                        [0, 0, 0, 1]
                    ])


def test_lower_triangular():
    A = Matrix([
                        [1, 1, 1, 1],
                        [1, 1, 1, 1],
                        [1, 1, 1, 1],
                        [1, 1, 1, 1]
                    ])

    L = A.lower_triangular()
    assert L == Matrix([
                        [1, 0, 0, 0],
                        [1, 1, 0, 0],
                        [1, 1, 1, 0],
                        [1, 1, 1, 1]])

    L = A.lower_triangular(2)
    assert L == Matrix([
                        [1, 1, 1, 0],
                        [1, 1, 1, 1],
                        [1, 1, 1, 1],
                        [1, 1, 1, 1]
                    ])

    L = A.lower_triangular(-2)
    assert L == Matrix([
                        [0, 0, 0, 0],
                        [0, 0, 0, 0],
                        [1, 0, 0, 0],
                        [1, 1, 0, 0]
                    ])


def test_add():
    m = Matrix([[1, 2, 3], [x, y, x], [2*y, -50, z*x]])
    assert m + m == Matrix([[2, 4, 6], [2*x, 2*y, 2*x], [4*y, -100, 2*z*x]])
    n = Matrix(1, 2, [1, 2])
    raises(ShapeError, lambda: m + n)


def test_matmul():
    a = Matrix([[1, 2], [3, 4]])

    assert a.__matmul__(2) == NotImplemented

    assert a.__rmatmul__(2) == NotImplemented

    #This is done this way because @ is only supported in Python 3.5+
    #To check 2@a case
    try:
        eval('2 @ a')
    except SyntaxError:
        pass
    except TypeError:  #TypeError is raised in case of NotImplemented is returned
        pass

    #Check a@2 case
    try:
        eval('a @ 2')
    except SyntaxError:
        pass
    except TypeError:  #TypeError is raised in case of NotImplemented is returned
        pass


def test_non_matmul():
    """
    Test that if explicitly specified as non-matrix, mul reverts
    to scalar multiplication.
    """
    class foo(Expr):
        is_Matrix=False
        is_MatrixLike=False
        shape = (1, 1)

    A = Matrix([[1, 2], [3, 4]])
    b = foo()
    assert b*A == Matrix([[b, 2*b], [3*b, 4*b]])
    assert A*b == Matrix([[b, 2*b], [3*b, 4*b]])


def test_neg():
    n = Matrix(1, 2, [1, 2])
    assert -n == Matrix(1, 2, [-1, -2])


def test_sub():
    n = Matrix(1, 2, [1, 2])
    assert n - n == Matrix(1, 2, [0, 0])


def test_div():
    n = Matrix(1, 2, [1, 2])
    assert n/2 == Matrix(1, 2, [S.Half, S(2)/2])


def test_eye():
    assert list(Matrix.eye(2, 2)) == [1, 0, 0, 1]
    assert list(Matrix.eye(2)) == [1, 0, 0, 1]
    assert type(Matrix.eye(2)) == Matrix
    assert type(Matrix.eye(2, cls=Matrix)) == Matrix


def test_ones():
    assert list(Matrix.ones(2, 2)) == [1, 1, 1, 1]
    assert list(Matrix.ones(2)) == [1, 1, 1, 1]
    assert Matrix.ones(2, 3) == Matrix([[1, 1, 1], [1, 1, 1]])
    assert type(Matrix.ones(2)) == Matrix
    assert type(Matrix.ones(2, cls=Matrix)) == Matrix


def test_zeros():
    assert list(Matrix.zeros(2, 2)) == [0, 0, 0, 0]
    assert list(Matrix.zeros(2)) == [0, 0, 0, 0]
    assert Matrix.zeros(2, 3) == Matrix([[0, 0, 0], [0, 0, 0]])
    assert type(Matrix.zeros(2)) == Matrix
    assert type(Matrix.zeros(2, cls=Matrix)) == Matrix


def test_diag_make():
    diag = Matrix.diag
    a = Matrix([[1, 2], [2, 3]])
    b = Matrix([[3, x], [y, 3]])
    c = Matrix([[3, x, 3], [y, 3, z], [x, y, z]])
    assert diag(a, b, b) == Matrix([
        [1, 2, 0, 0, 0, 0],
        [2, 3, 0, 0, 0, 0],
        [0, 0, 3, x, 0, 0],
        [0, 0, y, 3, 0, 0],
        [0, 0, 0, 0, 3, x],
        [0, 0, 0, 0, y, 3],
    ])
    assert diag(a, b, c) == Matrix([
        [1, 2, 0, 0, 0, 0, 0],
        [2, 3, 0, 0, 0, 0, 0],
        [0, 0, 3, x, 0, 0, 0],
        [0, 0, y, 3, 0, 0, 0],
        [0, 0, 0, 0, 3, x, 3],
        [0, 0, 0, 0, y, 3, z],
        [0, 0, 0, 0, x, y, z],
    ])
    assert diag(a, c, b) == Matrix([
        [1, 2, 0, 0, 0, 0, 0],
        [2, 3, 0, 0, 0, 0, 0],
        [0, 0, 3, x, 3, 0, 0],
        [0, 0, y, 3, z, 0, 0],
        [0, 0, x, y, z, 0, 0],
        [0, 0, 0, 0, 0, 3, x],
        [0, 0, 0, 0, 0, y, 3],
    ])
    a = Matrix([x, y, z])
    b = Matrix([[1, 2], [3, 4]])
    c = Matrix([[5, 6]])
    # this "wandering diagonal" is what makes this
    # a block diagonal where each block is independent
    # of the others
    assert diag(a, 7, b, c) == Matrix([
        [x, 0, 0, 0, 0, 0],
        [y, 0, 0, 0, 0, 0],
        [z, 0, 0, 0, 0, 0],
        [0, 7, 0, 0, 0, 0],
        [0, 0, 1, 2, 0, 0],
        [0, 0, 3, 4, 0, 0],
        [0, 0, 0, 0, 5, 6]])
    raises(ValueError, lambda: diag(a, 7, b, c, rows=5))
    assert diag(1) == Matrix([[1]])
    assert diag(1, rows=2) == Matrix([[1, 0], [0, 0]])
    assert diag(1, cols=2) == Matrix([[1, 0], [0, 0]])
    assert diag(1, rows=3, cols=2) == Matrix([[1, 0], [0, 0], [0, 0]])
    assert diag(*[2, 3]) == Matrix([
        [2, 0],
        [0, 3]])
    assert diag(Matrix([2, 3])) == Matrix([
        [2],
        [3]])
    assert diag([1, [2, 3], 4], unpack=False) == \
            diag([[1], [2, 3], [4]], unpack=False) == Matrix([
        [1, 0],
        [2, 3],
        [4, 0]])
    assert type(diag(1)) == Matrix
    assert type(diag(1, cls=Matrix)) == Matrix
    assert Matrix.diag([1, 2, 3]) == Matrix.diag(1, 2, 3)
    assert Matrix.diag([1, 2, 3], unpack=False).shape == (3, 1)
    assert Matrix.diag([[1, 2, 3]]).shape == (3, 1)
    assert Matrix.diag([[1, 2, 3]], unpack=False).shape == (1, 3)
    assert Matrix.diag([[[1, 2, 3]]]).shape == (1, 3)
    # kerning can be used to move the starting point
    assert Matrix.diag(ones(0, 2), 1, 2) == Matrix([
        [0, 0, 1, 0],
        [0, 0, 0, 2]])
    assert Matrix.diag(ones(2, 0), 1, 2) == Matrix([
        [0, 0],
        [0, 0],
        [1, 0],
        [0, 2]])


def test_diagonal():
    m = Matrix(3, 3, range(9))
    d = m.diagonal()
    assert d == m.diagonal(0)
    assert tuple(d) == (0, 4, 8)
    assert tuple(m.diagonal(1)) == (1, 5)
    assert tuple(m.diagonal(-1)) == (3, 7)
    assert tuple(m.diagonal(2)) == (2,)
    assert type(m.diagonal()) == type(m)
    s = SparseMatrix(3, 3, {(1, 1): 1})
    assert type(s.diagonal()) == type(s)
    assert type(m) != type(s)
    raises(ValueError, lambda: m.diagonal(3))
    raises(ValueError, lambda: m.diagonal(-3))
    raises(ValueError, lambda: m.diagonal(pi))
    M = ones(2, 3)
    assert banded({i: list(M.diagonal(i))
        for i in range(1-M.rows, M.cols)}) == M


def test_jordan_block():
    assert Matrix.jordan_block(3, 2) == Matrix.jordan_block(3, eigenvalue=2) \
            == Matrix.jordan_block(size=3, eigenvalue=2) \
            == Matrix.jordan_block(3, 2, band='upper') \
            == Matrix.jordan_block(
                size=3, eigenval=2, eigenvalue=2) \
            == Matrix([
                [2, 1, 0],
                [0, 2, 1],
                [0, 0, 2]])

    assert Matrix.jordan_block(3, 2, band='lower') == Matrix([
                    [2, 0, 0],
                    [1, 2, 0],
                    [0, 1, 2]])
    # missing eigenvalue
    raises(ValueError, lambda: Matrix.jordan_block(2))
    # non-integral size
    raises(ValueError, lambda: Matrix.jordan_block(3.5, 2))
    # size not specified
    raises(ValueError, lambda: Matrix.jordan_block(eigenvalue=2))
    # inconsistent eigenvalue
    raises(ValueError,
    lambda: Matrix.jordan_block(
        eigenvalue=2, eigenval=4))

    # Using alias keyword
    assert Matrix.jordan_block(size=3, eigenvalue=2) == \
        Matrix.jordan_block(size=3, eigenval=2)


def test_orthogonalize():
    m = Matrix([[1, 2], [3, 4]])
    assert m.orthogonalize(Matrix([[2], [1]])) == [Matrix([[2], [1]])]
    assert m.orthogonalize(Matrix([[2], [1]]), normalize=True) == \
        [Matrix([[2*sqrt(5)/5], [sqrt(5)/5]])]
    assert m.orthogonalize(Matrix([[1], [2]]), Matrix([[-1], [4]])) == \
        [Matrix([[1], [2]]), Matrix([[Rational(-12, 5)], [Rational(6, 5)]])]
    assert m.orthogonalize(Matrix([[0], [0]]), Matrix([[-1], [4]])) == \
        [Matrix([[-1], [4]])]
    assert m.orthogonalize(Matrix([[0], [0]])) == []

    n = Matrix([[9, 1, 9], [3, 6, 10], [8, 5, 2]])
    vecs = [Matrix([[-5], [1]]), Matrix([[-5], [2]]), Matrix([[-5], [-2]])]
    assert n.orthogonalize(*vecs) == \
        [Matrix([[-5], [1]]), Matrix([[Rational(5, 26)], [Rational(25, 26)]])]

    vecs = [Matrix([0, 0, 0]), Matrix([1, 2, 3]), Matrix([1, 4, 5])]
    raises(ValueError, lambda: Matrix.orthogonalize(*vecs, rankcheck=True))

    vecs = [Matrix([1, 2, 3]), Matrix([4, 5, 6]), Matrix([7, 8, 9])]
    raises(ValueError, lambda: Matrix.orthogonalize(*vecs, rankcheck=True))

def test_wilkinson():

    wminus, wplus = Matrix.wilkinson(1)
    assert wminus == Matrix([
                                [-1, 1, 0],
                                [1, 0, 1],
                                [0, 1, 1]])
    assert wplus == Matrix([
                            [1, 1, 0],
                            [1, 0, 1],
                            [0, 1, 1]])

    wminus, wplus = Matrix.wilkinson(3)
    assert wminus == Matrix([
                                [-3,  1,  0, 0, 0, 0, 0],
                                [1, -2,  1, 0, 0, 0, 0],
                                [0,  1, -1, 1, 0, 0, 0],
                                [0,  0,  1, 0, 1, 0, 0],
                                [0,  0,  0, 1, 1, 1, 0],
                                [0,  0,  0, 0, 1, 2, 1],

      [0,  0,  0, 0, 0, 1, 3]])

    assert wplus == Matrix([
                            [3, 1, 0, 0, 0, 0, 0],
                            [1, 2, 1, 0, 0, 0, 0],
                            [0, 1, 1, 1, 0, 0, 0],
                            [0, 0, 1, 0, 1, 0, 0],
                            [0, 0, 0, 1, 1, 1, 0],
                            [0, 0, 0, 0, 1, 2, 1],
                            [0, 0, 0, 0, 0, 1, 3]])


def test_limit():
    x, y = symbols('x y')
    m = Matrix(2, 1, [1/x, y])
    assert m.limit(x, 5) == Matrix(2, 1, [Rational(1, 5), y])
    A = Matrix(((1, 4, sin(x)/x), (y, 2, 4), (10, 5, x**2 + 1)))
    assert A.limit(x, 0) == Matrix(((1, 4, 1), (y, 2, 4), (10, 5, 1)))


def test_issue_13774():
    M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    v = [1, 1, 1]
    raises(TypeError, lambda: M*v)
    raises(TypeError, lambda: v*M)


def test_companion():
    x = Symbol('x')
    y = Symbol('y')
    raises(ValueError, lambda: Matrix.companion(1))
    raises(ValueError, lambda: Matrix.companion(Poly([1], x)))
    raises(ValueError, lambda: Matrix.companion(Poly([2, 1], x)))
    raises(ValueError, lambda: Matrix.companion(Poly(x*y, [x, y])))

    c0, c1, c2 = symbols('c0:3')
    assert Matrix.companion(Poly([1, c0], x)) == Matrix([-c0])
    assert Matrix.companion(Poly([1, c1, c0], x)) == \
        Matrix([[0, -c0], [1, -c1]])
    assert Matrix.companion(Poly([1, c2, c1, c0], x)) == \
        Matrix([[0, 0, -c0], [1, 0, -c1], [0, 1, -c2]])


def test_issue_10589():
    x, y, z = symbols("x, y z")
    M1 = Matrix([x, y, z])
    M1 = M1.subs(zip([x, y, z], [1, 2, 3]))
    assert M1 == Matrix([[1], [2], [3]])

    M2 = Matrix([[x, x, x, x, x], [x, x, x, x, x], [x, x, x, x, x]])
    M2 = M2.subs(zip([x], [1]))
    assert M2 == Matrix([[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1]])


def test_rmul_pr19860():
    class Foo(ImmutableDenseMatrix):
        _op_priority = MutableDenseMatrix._op_priority + 0.01

    a = Matrix(2, 2, [1, 2, 3, 4])
    b = Foo(2, 2, [1, 2, 3, 4])

    # This would throw a RecursionError: maximum recursion depth
    # since b always has higher priority even after a.as_mutable()
    c = a*b

    assert isinstance(c, Foo)
    assert c == Matrix([[7, 10], [15, 22]])


def test_issue_18956():
    A = Array([[1, 2], [3, 4]])
    B = Matrix([[1,2],[3,4]])
    raises(TypeError, lambda: B + A)
    raises(TypeError, lambda: A + B)


def test__eq__():
    class My(object):
        def __iter__(self):
            yield 1
            yield 2
            return
        def __getitem__(self, i):
            return list(self)[i]
    a = Matrix(2, 1, [1, 2])
    assert a != My()
    class My_sympy(My):
        def _sympy_(self):
            return Matrix(self)
    assert a == My_sympy()


def test_args():
    for n, cls in enumerate(all_classes):
        m = cls.zeros(3, 2)
        # all should give back the same type of arguments, e.g. ints for shape
        assert m.shape == (3, 2) and all(type(i) is int for i in m.shape)
        assert m.rows == 3 and type(m.rows) is int
        assert m.cols == 2 and type(m.cols) is int
        if not n % 2:
            assert type(m.flat()) in (list, tuple, Tuple)
        else:
            assert type(m.todok()) is dict


def test_deprecated_mat_smat():
    for cls in Matrix, ImmutableMatrix:
        m = cls.zeros(3, 2)
        with warns_deprecated_sympy():
            mat = m._mat
        assert mat == m.flat()
    for cls in SparseMatrix, ImmutableSparseMatrix:
        m = cls.zeros(3, 2)
        with warns_deprecated_sympy():
            smat = m._smat
        assert smat == m.todok()


def test_division():
    v = Matrix(1, 2, [x, y])
    assert v/z == Matrix(1, 2, [x/z, y/z])


def test_sum():
    m = Matrix([[1, 2, 3], [x, y, x], [2*y, -50, z*x]])
    assert m + m == Matrix([[2, 4, 6], [2*x, 2*y, 2*x], [4*y, -100, 2*z*x]])
    n = Matrix(1, 2, [1, 2])
    raises(ShapeError, lambda: m + n)


def test_abs():
    m = Matrix([[1, -2], [x, y]])
    assert abs(m) == Matrix([[1, 2], [Abs(x), Abs(y)]])
    m = Matrix(1, 2, [-3, x])
    n = Matrix(1, 2, [3, Abs(x)])
    assert abs(m) == n


def test_addition():
    a = Matrix((
        (1, 2),
        (3, 1),
    ))

    b = Matrix((
        (1, 2),
        (3, 0),
    ))

    assert a + b == a.add(b) == Matrix([[2, 4], [6, 1]])


def test_fancy_index_matrix():
    for M in (Matrix, SparseMatrix):
        a = M(3, 3, range(9))
        assert a == a[:, :]
        assert a[1, :] == Matrix(1, 3, [3, 4, 5])
        assert a[:, 1] == Matrix([1, 4, 7])
        assert a[[0, 1], :] == Matrix([[0, 1, 2], [3, 4, 5]])
        assert a[[0, 1], 2] == a[[0, 1], [2]]
        assert a[2, [0, 1]] == a[[2], [0, 1]]
        assert a[:, [0, 1]] == Matrix([[0, 1], [3, 4], [6, 7]])
        assert a[0, 0] == 0
        assert a[0:2, :] == Matrix([[0, 1, 2], [3, 4, 5]])
        assert a[:, 0:2] == Matrix([[0, 1], [3, 4], [6, 7]])
        assert a[::2, 1] == a[[0, 2], 1]
        assert a[1, ::2] == a[1, [0, 2]]
        a = M(3, 3, range(9))
        assert a[[0, 2, 1, 2, 1], :] == Matrix([
            [0, 1, 2],
            [6, 7, 8],
            [3, 4, 5],
            [6, 7, 8],
            [3, 4, 5]])
        assert a[:, [0,2,1,2,1]] == Matrix([
            [0, 2, 1, 2, 1],
            [3, 5, 4, 5, 4],
            [6, 8, 7, 8, 7]])

    a = SparseMatrix.zeros(3)
    a[1, 2] = 2
    a[0, 1] = 3
    a[2, 0] = 4
    assert a.extract([1, 1], [2]) == Matrix([
    [2],
    [2]])
    assert a.extract([1, 0], [2, 2, 2]) == Matrix([
    [2, 2, 2],
    [0, 0, 0]])
    assert a.extract([1, 0, 1, 2], [2, 0, 1, 0]) == Matrix([
        [2, 0, 0, 0],
        [0, 0, 3, 0],
        [2, 0, 0, 0],
        [0, 4, 0, 4]])


def test_multiplication():
    a = Matrix((
        (1, 2),
        (3, 1),
        (0, 6),
    ))

    b = Matrix((
        (1, 2),
        (3, 0),
    ))

    raises(ShapeError, lambda: b*a)
    raises(TypeError, lambda: a*{})

    c = a*b
    assert c[0, 0] == 7
    assert c[0, 1] == 2
    assert c[1, 0] == 6
    assert c[1, 1] == 6
    assert c[2, 0] == 18
    assert c[2, 1] == 0

    c = a @ b
    assert c[0, 0] == 7
    assert c[0, 1] == 2
    assert c[1, 0] == 6
    assert c[1, 1] == 6
    assert c[2, 0] == 18
    assert c[2, 1] == 0

    h = matrix_multiply_elementwise(a, c)
    assert h == a.multiply_elementwise(c)
    assert h[0, 0] == 7
    assert h[0, 1] == 4
    assert h[1, 0] == 18
    assert h[1, 1] == 6
    assert h[2, 0] == 0
    assert h[2, 1] == 0
    raises(ShapeError, lambda: matrix_multiply_elementwise(a, b))

    c = b * Symbol("x")
    assert isinstance(c, Matrix)
    assert c[0, 0] == x
    assert c[0, 1] == 2*x
    assert c[1, 0] == 3*x
    assert c[1, 1] == 0

    c2 = x * b
    assert c == c2

    c = 5 * b
    assert isinstance(c, Matrix)
    assert c[0, 0] == 5
    assert c[0, 1] == 2*5
    assert c[1, 0] == 3*5
    assert c[1, 1] == 0

    M = Matrix([[oo, 0], [0, oo]])
    assert M ** 2 == M

    M = Matrix([[oo, oo], [0, 0]])
    assert M ** 2 == Matrix([[nan, nan], [nan, nan]])

    # https://github.com/sympy/sympy/issues/22353
    A = Matrix(ones(3, 1))
    _h = -Rational(1, 2)
    B = Matrix([_h, _h, _h])
    assert A.multiply_elementwise(B) == Matrix([
        [_h],
        [_h],
        [_h]])


def test_power():
    raises(NonSquareMatrixError, lambda: Matrix((1, 2))**2)

    A = Matrix([[2, 3], [4, 5]])
    assert A**5 == Matrix([[6140, 8097], [10796, 14237]])
    A = Matrix([[2, 1, 3], [4, 2, 4], [6, 12, 1]])
    assert A**3 == Matrix([[290, 262, 251], [448, 440, 368], [702, 954, 433]])
    assert A**0 == eye(3)
    assert A**1 == A
    assert (Matrix([[2]]) ** 100)[0, 0] == 2**100
    assert Matrix([[1, 2], [3, 4]])**Integer(2) == Matrix([[7, 10], [15, 22]])
    A = Matrix([[1,2],[4,5]])
    assert A.pow(20, method='cayley') == A.pow(20, method='multiply')
    assert A**Integer(2) == Matrix([[9, 12], [24, 33]])
    assert eye(2)**10000000 == eye(2)

    A = Matrix([[33, 24], [48, 57]])
    assert (A**S.Half)[:] == [5, 2, 4, 7]
    A = Matrix([[0, 4], [-1, 5]])
    assert (A**S.Half)**2 == A

    assert Matrix([[1, 0], [1, 1]])**S.Half == Matrix([[1, 0], [S.Half, 1]])
    assert Matrix([[1, 0], [1, 1]])**0.5 == Matrix([[1, 0], [0.5, 1]])
    from sympy.abc import n
    assert Matrix([[1, a], [0, 1]])**n == Matrix([[1, a*n], [0, 1]])
    assert Matrix([[b, a], [0, b]])**n == Matrix([[b**n, a*b**(n-1)*n], [0, b**n]])
    assert Matrix([
        [a**n, a**(n - 1)*n, (a**n*n**2 - a**n*n)/(2*a**2)],
        [   0,         a**n,                  a**(n - 1)*n],
        [   0,            0,                          a**n]])
    assert Matrix([[a, 1, 0], [0, a, 0], [0, 0, b]])**n == Matrix([
        [a**n, a**(n-1)*n, 0],
        [0, a**n, 0],
        [0, 0, b**n]])

    A = Matrix([[1, 0], [1, 7]])
    assert A._matrix_pow_by_jordan_blocks(S(3)) == A._eval_pow_by_recursion(3)
    A = Matrix([[2]])
    assert A**10 == Matrix([[2**10]]) == A._matrix_pow_by_jordan_blocks(S(10)) == \
        A._eval_pow_by_recursion(10)

    # testing a matrix that cannot be jordan blocked issue 11766
    m = Matrix([[3, 0, 0, 0, -3], [0, -3, -3, 0, 3], [0, 3, 0, 3, 0], [0, 0, 3, 0, 3], [3, 0, 0, 3, 0]])
    raises(MatrixError, lambda: m._matrix_pow_by_jordan_blocks(S(10)))

    # test issue 11964
    raises(MatrixError, lambda: Matrix([[1, 1], [3, 3]])._matrix_pow_by_jordan_blocks(S(-10)))
    A = Matrix([[0, 1, 0], [0, 0, 1], [0, 0, 0]])  # Nilpotent jordan block size 3
    assert A**10.0 == Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    raises(ValueError, lambda: A**2.1)
    raises(ValueError, lambda: A**Rational(3, 2))
    A = Matrix([[8, 1], [3, 2]])
    assert A**10.0 == Matrix([[1760744107, 272388050], [817164150, 126415807]])
    A = Matrix([[0, 0, 1], [0, 0, 1], [0, 0, 1]])  # Nilpotent jordan block size 1
    assert A**10.0 == Matrix([[0, 0, 1], [0, 0, 1], [0, 0, 1]])
    A = Matrix([[0, 1, 0], [0, 0, 1], [0, 0, 1]])  # Nilpotent jordan block size 2
    assert A**10.0 == Matrix([[0, 0, 1], [0, 0, 1], [0, 0, 1]])
    n = Symbol('n', integer=True)
    assert isinstance(A**n, MatPow)
    n = Symbol('n', integer=True, negative=True)
    raises(ValueError, lambda: A**n)
    n = Symbol('n', integer=True, nonnegative=True)
    assert A**n == Matrix([
        [KroneckerDelta(0, n), KroneckerDelta(1, n), -KroneckerDelta(0, n) - KroneckerDelta(1, n) + 1],
        [                   0, KroneckerDelta(0, n),                         1 - KroneckerDelta(0, n)],
        [                   0,                    0,                                                1]])
    assert A**(n + 2) == Matrix([[0, 0, 1], [0, 0, 1], [0, 0, 1]])
    raises(ValueError, lambda: A**Rational(3, 2))
    A = Matrix([[0, 0, 1], [3, 0, 1], [4, 3, 1]])
    assert A**5.0 == Matrix([[168,  72,  89], [291, 144, 161], [572, 267, 329]])
    assert A**5.0 == A**5
    A = Matrix([[0, 1, 0],[-1, 0, 0],[0, 0, 0]])
    n = Symbol("n")
    An = A**n
    assert An.subs(n, 2).doit() == A**2
    raises(ValueError, lambda: An.subs(n, -2).doit())
    assert An * An == A**(2*n)

    # concretizing behavior for non-integer and complex powers
    A = Matrix([[0,0,0],[0,0,0],[0,0,0]])
    n = Symbol('n', integer=True, positive=True)
    assert A**n == A
    n = Symbol('n', integer=True, nonnegative=True)
    assert A**n == diag(0**n, 0**n, 0**n)
    assert (A**n).subs(n, 0) == eye(3)
    assert (A**n).subs(n, 1) == zeros(3)
    A = Matrix ([[2,0,0],[0,2,0],[0,0,2]])
    assert A**2.1 == diag (2**2.1, 2**2.1, 2**2.1)
    assert A**I == diag (2**I, 2**I, 2**I)
    A = Matrix([[0, 1, 0], [0, 0, 1], [0, 0, 1]])
    raises(ValueError, lambda: A**2.1)
    raises(ValueError, lambda: A**I)
    A = Matrix([[S.Half, S.Half], [S.Half, S.Half]])
    assert A**S.Half == A
    A = Matrix([[1, 1],[3, 3]])
    assert A**S.Half == Matrix ([[S.Half, S.Half], [3*S.Half, 3*S.Half]])


def test_issue_17247_expression_blowup_1():
    M = Matrix([[1+x, 1-x], [1-x, 1+x]])
    with dotprodsimp(True):
        assert M.exp().expand() == Matrix([
            [ (exp(2*x) + exp(2))/2, (-exp(2*x) + exp(2))/2],
            [(-exp(2*x) + exp(2))/2,  (exp(2*x) + exp(2))/2]])


def test_issue_17247_expression_blowup_2():
    M = Matrix([[1+x, 1-x], [1-x, 1+x]])
    with dotprodsimp(True):
        P, J = M.jordan_form ()
        assert P*J*P.inv()


def test_issue_17247_expression_blowup_3():
    M = Matrix([[1+x, 1-x], [1-x, 1+x]])
    with dotprodsimp(True):
        assert M**100 == Matrix([
            [633825300114114700748351602688*x**100 + 633825300114114700748351602688, 633825300114114700748351602688 - 633825300114114700748351602688*x**100],
            [633825300114114700748351602688 - 633825300114114700748351602688*x**100, 633825300114114700748351602688*x**100 + 633825300114114700748351602688]])


def test_issue_17247_expression_blowup_4():
# This matrix takes extremely long on current master even with intermediate simplification so an abbreviated version is used. It is left here for test in case of future optimizations.
#     M = Matrix(S('''[
#         [             -3/4,       45/32 - 37*I/16,         1/4 + I/2,      -129/64 - 9*I/64,      1/4 - 5*I/16,      65/128 + 87*I/64,         -9/32 - I/16,      183/256 - 97*I/128,       3/64 + 13*I/64,         -23/32 - 59*I/256,      15/128 - 3*I/32,        19/256 + 551*I/1024],
#         [-149/64 + 49*I/32, -177/128 - 1369*I/128,  125/64 + 87*I/64, -2063/256 + 541*I/128,  85/256 - 33*I/16,  805/128 + 2415*I/512, -219/128 + 115*I/256, 6301/4096 - 6609*I/1024,  119/128 + 143*I/128, -10879/2048 + 4343*I/4096,  129/256 - 549*I/512, 42533/16384 + 29103*I/8192],
#         [          1/2 - I,         9/4 + 55*I/16,              -3/4,       45/32 - 37*I/16,         1/4 + I/2,      -129/64 - 9*I/64,         1/4 - 5*I/16,        65/128 + 87*I/64,         -9/32 - I/16,        183/256 - 97*I/128,       3/64 + 13*I/64,          -23/32 - 59*I/256],
#         [   -5/8 - 39*I/16,   2473/256 + 137*I/64, -149/64 + 49*I/32, -177/128 - 1369*I/128,  125/64 + 87*I/64, -2063/256 + 541*I/128,     85/256 - 33*I/16,    805/128 + 2415*I/512, -219/128 + 115*I/256,   6301/4096 - 6609*I/1024,  119/128 + 143*I/128,  -10879/2048 + 4343*I/4096],
#         [            1 + I,         -19/4 + 5*I/4,           1/2 - I,         9/4 + 55*I/16,              -3/4,       45/32 - 37*I/16,            1/4 + I/2,        -129/64 - 9*I/64,         1/4 - 5*I/16,          65/128 + 87*I/64,         -9/32 - I/16,         183/256 - 97*I/128],
#         [         21/8 + I,    -537/64 + 143*I/16,    -5/8 - 39*I/16,   2473/256 + 137*I/64, -149/64 + 49*I/32, -177/128 - 1369*I/128,     125/64 + 87*I/64,   -2063/256 + 541*I/128,     85/256 - 33*I/16,      805/128 + 2415*I/512, -219/128 + 115*I/256,    6301/4096 - 6609*I/1024],
#         [               -2,         17/4 - 13*I/2,             1 + I,         -19/4 + 5*I/4,           1/2 - I,         9/4 + 55*I/16,                 -3/4,         45/32 - 37*I/16,            1/4 + I/2,          -129/64 - 9*I/64,         1/4 - 5*I/16,           65/128 + 87*I/64],
#         [     1/4 + 13*I/4,    -825/64 - 147*I/32,          21/8 + I,    -537/64 + 143*I/16,    -5/8 - 39*I/16,   2473/256 + 137*I/64,    -149/64 + 49*I/32,   -177/128 - 1369*I/128,     125/64 + 87*I/64,     -2063/256 + 541*I/128,     85/256 - 33*I/16,       805/128 + 2415*I/512],
#         [             -4*I,            27/2 + 6*I,                -2,         17/4 - 13*I/2,             1 + I,         -19/4 + 5*I/4,              1/2 - I,           9/4 + 55*I/16,                 -3/4,           45/32 - 37*I/16,            1/4 + I/2,           -129/64 - 9*I/64],
#         [      1/4 + 5*I/2,       -23/8 - 57*I/16,      1/4 + 13*I/4,    -825/64 - 147*I/32,          21/8 + I,    -537/64 + 143*I/16,       -5/8 - 39*I/16,     2473/256 + 137*I/64,    -149/64 + 49*I/32,     -177/128 - 1369*I/128,     125/64 + 87*I/64,      -2063/256 + 541*I/128],
#         [               -4,               9 - 5*I,              -4*I,            27/2 + 6*I,                -2,         17/4 - 13*I/2,                1 + I,           -19/4 + 5*I/4,              1/2 - I,             9/4 + 55*I/16,                 -3/4,            45/32 - 37*I/16],
#         [             -2*I,        119/8 + 29*I/4,       1/4 + 5*I/2,       -23/8 - 57*I/16,      1/4 + 13*I/4,    -825/64 - 147*I/32,             21/8 + I,      -537/64 + 143*I/16,       -5/8 - 39*I/16,       2473/256 + 137*I/64,    -149/64 + 49*I/32,      -177/128 - 1369*I/128]]'''))
#     assert M**10 == Matrix([
#         [    7*(-221393644768594642173548179825793834595 - 1861633166167425978847110897013541127952*I)/9671406556917033397649408,      15*(31670992489131684885307005100073928751695 + 10329090958303458811115024718207404523808*I)/77371252455336267181195264,   7*(-3710978679372178839237291049477017392703 + 1377706064483132637295566581525806894169*I)/19342813113834066795298816,            (9727707023582419994616144751727760051598 - 59261571067013123836477348473611225724433*I)/9671406556917033397649408,      (31896723509506857062605551443641668183707 + 54643444538699269118869436271152084599580*I)/38685626227668133590597632,       (-2024044860947539028275487595741003997397402 + 130959428791783397562960461903698670485863*I)/309485009821345068724781056,     3*(26190251453797590396533756519358368860907 - 27221191754180839338002754608545400941638*I)/77371252455336267181195264,      (1154643595139959842768960128434994698330461 + 3385496216250226964322872072260446072295634*I)/618970019642690137449562112,     3*(-31849347263064464698310044805285774295286 - 11877437776464148281991240541742691164309*I)/77371252455336267181195264,     (4661330392283532534549306589669150228040221 - 4171259766019818631067810706563064103956871*I)/1237940039285380274899124224,        (9598353794289061833850770474812760144506 + 358027153990999990968244906482319780943983*I)/309485009821345068724781056,     (-9755135335127734571547571921702373498554177 - 4837981372692695195747379349593041939686540*I)/2475880078570760549798248448],
#         [(-379516731607474268954110071392894274962069 - 422272153179747548473724096872271700878296*I)/77371252455336267181195264, (41324748029613152354787280677832014263339501 - 12715121258662668420833935373453570749288074*I)/1237940039285380274899124224, (-339216903907423793947110742819264306542397 + 494174755147303922029979279454787373566517*I)/77371252455336267181195264, (-18121350839962855576667529908850640619878381 - 37413012454129786092962531597292531089199003*I)/1237940039285380274899124224, (2489661087330511608618880408199633556675926 + 1137821536550153872137379935240732287260863*I)/309485009821345068724781056, (-136644109701594123227587016790354220062972119 + 110130123468183660555391413889600443583585272*I)/4951760157141521099596496896, (1488043981274920070468141664150073426459593 - 9691968079933445130866371609614474474327650*I)/1237940039285380274899124224,  27*(4636797403026872518131756991410164760195942 + 3369103221138229204457272860484005850416533*I)/4951760157141521099596496896, (-8534279107365915284081669381642269800472363 + 2241118846262661434336333368511372725482742*I)/1237940039285380274899124224,  (60923350128174260992536531692058086830950875 - 263673488093551053385865699805250505661590126*I)/9903520314283042199192993792, (18520943561240714459282253753348921824172569 + 24846649186468656345966986622110971925703604*I)/4951760157141521099596496896,  (-232781130692604829085973604213529649638644431 + 35981505277760667933017117949103953338570617*I)/9903520314283042199192993792],
#         [      (8742968295129404279528270438201520488950 + 3061473358639249112126847237482570858327*I)/4835703278458516698824704,      (-245657313712011778432792959787098074935273 + 253113767861878869678042729088355086740856*I)/38685626227668133590597632,      (1947031161734702327107371192008011621193 - 19462330079296259148177542369999791122762*I)/9671406556917033397649408,        (552856485625209001527688949522750288619217 + 392928441196156725372494335248099016686580*I)/77371252455336267181195264,      (-44542866621905323121630214897126343414629 + 3265340021421335059323962377647649632959*I)/19342813113834066795298816,          (136272594005759723105646069956434264218730 - 330975364731707309489523680957584684763587*I)/38685626227668133590597632,       (27392593965554149283318732469825168894401 + 75157071243800133880129376047131061115278*I)/38685626227668133590597632,      7*(-357821652913266734749960136017214096276154 - 45509144466378076475315751988405961498243*I)/309485009821345068724781056,       (104485001373574280824835174390219397141149 - 99041000529599568255829489765415726168162*I)/77371252455336267181195264,      (1198066993119982409323525798509037696321291 + 4249784165667887866939369628840569844519936*I)/618970019642690137449562112,       (-114985392587849953209115599084503853611014 - 52510376847189529234864487459476242883449*I)/77371252455336267181195264,      (6094620517051332877965959223269600650951573 - 4683469779240530439185019982269137976201163*I)/1237940039285380274899124224],
#         [ (611292255597977285752123848828590587708323 - 216821743518546668382662964473055912169502*I)/77371252455336267181195264,  (-1144023204575811464652692396337616594307487 + 12295317806312398617498029126807758490062855*I)/309485009821345068724781056, (-374093027769390002505693378578475235158281 - 573533923565898290299607461660384634333639*I)/77371252455336267181195264,   (47405570632186659000138546955372796986832987 - 2837476058950808941605000274055970055096534*I)/1237940039285380274899124224,   (-571573207393621076306216726219753090535121 + 533381457185823100878764749236639320783831*I)/77371252455336267181195264,     (-7096548151856165056213543560958582513797519 - 24035731898756040059329175131592138642195366*I)/618970019642690137449562112,  (2396762128833271142000266170154694033849225 + 1448501087375679588770230529017516492953051*I)/309485009821345068724781056, (-150609293845161968447166237242456473262037053 + 92581148080922977153207018003184520294188436*I)/4951760157141521099596496896, 5*(270278244730804315149356082977618054486347 - 1997830155222496880429743815321662710091562*I)/1237940039285380274899124224,   (62978424789588828258068912690172109324360330 + 44803641177219298311493356929537007630129097*I)/2475880078570760549798248448, 19*(-451431106327656743945775812536216598712236 + 114924966793632084379437683991151177407937*I)/1237940039285380274899124224,   (63417747628891221594106738815256002143915995 - 261508229397507037136324178612212080871150958*I)/9903520314283042199192993792],
#         [     (-2144231934021288786200752920446633703357 + 2305614436009705803670842248131563850246*I)/1208925819614629174706176,       (-90720949337459896266067589013987007078153 - 221951119475096403601562347412753844534569*I)/19342813113834066795298816,      (11590973613116630788176337262688659880376 + 6514520676308992726483494976339330626159*I)/4835703278458516698824704,      3*(-131776217149000326618649542018343107657237 + 79095042939612668486212006406818285287004*I)/38685626227668133590597632,       (10100577916793945997239221374025741184951 - 28631383488085522003281589065994018550748*I)/9671406556917033397649408,         67*(10090295594251078955008130473573667572549 + 10449901522697161049513326446427839676762*I)/77371252455336267181195264,       (-54270981296988368730689531355811033930513 - 3413683117592637309471893510944045467443*I)/19342813113834066795298816,         (440372322928679910536575560069973699181278 - 736603803202303189048085196176918214409081*I)/77371252455336267181195264,        (33220374714789391132887731139763250155295 + 92055083048787219934030779066298919603554*I)/38685626227668133590597632,      5*(-594638554579967244348856981610805281527116 - 82309245323128933521987392165716076704057*I)/309485009821345068724781056,       (128056368815300084550013708313312073721955 - 114619107488668120303579745393765245911404*I)/77371252455336267181195264,       21*(59839959255173222962789517794121843393573 + 241507883613676387255359616163487405826334*I)/618970019642690137449562112],
#         [ (-13454485022325376674626653802541391955147 + 184471402121905621396582628515905949793486*I)/19342813113834066795298816,   (-6158730123400322562149780662133074862437105 - 3416173052604643794120262081623703514107476*I)/154742504910672534362390528,  (770558003844914708453618983120686116100419 - 127758381209767638635199674005029818518766*I)/77371252455336267181195264,   (-4693005771813492267479835161596671660631703 + 12703585094750991389845384539501921531449948*I)/309485009821345068724781056,   (-295028157441149027913545676461260860036601 - 841544569970643160358138082317324743450770*I)/77371252455336267181195264,     (56716442796929448856312202561538574275502893 + 7216818824772560379753073185990186711454778*I)/1237940039285380274899124224,  15*(-87061038932753366532685677510172566368387 + 61306141156647596310941396434445461895538*I)/154742504910672534362390528,    (-3455315109680781412178133042301025723909347 - 24969329563196972466388460746447646686670670*I)/618970019642690137449562112,   (2453418854160886481106557323699250865361849 + 1497886802326243014471854112161398141242514*I)/309485009821345068724781056, (-151343224544252091980004429001205664193082173 + 90471883264187337053549090899816228846836628*I)/4951760157141521099596496896,   (1652018205533026103358164026239417416432989 - 9959733619236515024261775397109724431400162*I)/1237940039285380274899124224,  3*(40676374242956907656984876692623172736522006 + 31023357083037817469535762230872667581366205*I)/4951760157141521099596496896],
#         [     (-1226990509403328460274658603410696548387 - 4131739423109992672186585941938392788458*I)/1208925819614629174706176,         (162392818524418973411975140074368079662703 + 23706194236915374831230612374344230400704*I)/9671406556917033397649408,      (-3935678233089814180000602553655565621193 + 2283744757287145199688061892165659502483*I)/1208925819614629174706176,         (-2400210250844254483454290806930306285131 - 315571356806370996069052930302295432758205*I)/19342813113834066795298816,       (13365917938215281056563183751673390817910 + 15911483133819801118348625831132324863881*I)/4835703278458516698824704,        3*(-215950551370668982657516660700301003897855 + 51684341999223632631602864028309400489378*I)/38685626227668133590597632,        (20886089946811765149439844691320027184765 - 30806277083146786592790625980769214361844*I)/9671406556917033397649408,        (562180634592713285745940856221105667874855 + 1031543963988260765153550559766662245114916*I)/77371252455336267181195264,       (-65820625814810177122941758625652476012867 - 12429918324787060890804395323920477537595*I)/19342813113834066795298816,         (319147848192012911298771180196635859221089 - 402403304933906769233365689834404519960394*I)/38685626227668133590597632,        (23035615120921026080284733394359587955057 + 115351677687031786114651452775242461310624*I)/38685626227668133590597632,      (-3426830634881892756966440108592579264936130 - 1022954961164128745603407283836365128598559*I)/309485009821345068724781056],
#         [ (-192574788060137531023716449082856117537757 - 69222967328876859586831013062387845780692*I)/19342813113834066795298816,     (2736383768828013152914815341491629299773262 - 2773252698016291897599353862072533475408743*I)/77371252455336267181195264,  (-23280005281223837717773057436155921656805 + 214784953368021840006305033048142888879224*I)/19342813113834066795298816,     (-3035247484028969580570400133318947903462326 - 2195168903335435855621328554626336958674325*I)/77371252455336267181195264,     (984552428291526892214541708637840971548653 - 64006622534521425620714598573494988589378*I)/77371252455336267181195264,      (-3070650452470333005276715136041262898509903 + 7286424705750810474140953092161794621989080*I)/154742504910672534362390528,    (-147848877109756404594659513386972921139270 - 416306113044186424749331418059456047650861*I)/38685626227668133590597632,    (55272118474097814260289392337160619494260781 + 7494019668394781211907115583302403519488058*I)/1237940039285380274899124224,     (-581537886583682322424771088996959213068864 + 542191617758465339135308203815256798407429*I)/77371252455336267181195264,    (-6422548983676355789975736799494791970390991 - 23524183982209004826464749309156698827737702*I)/618970019642690137449562112,     7*(180747195387024536886923192475064903482083 + 84352527693562434817771649853047924991804*I)/154742504910672534362390528, (-135485179036717001055310712747643466592387031 + 102346575226653028836678855697782273460527608*I)/4951760157141521099596496896],
#         [        (3384238362616083147067025892852431152105 + 156724444932584900214919898954874618256*I)/604462909807314587353088,        (-59558300950677430189587207338385764871866 + 114427143574375271097298201388331237478857*I)/4835703278458516698824704,      (-1356835789870635633517710130971800616227 - 7023484098542340388800213478357340875410*I)/1208925819614629174706176,          (234884918567993750975181728413524549575881 + 79757294640629983786895695752733890213506*I)/9671406556917033397649408,        (-7632732774935120473359202657160313866419 + 2905452608512927560554702228553291839465*I)/1208925819614629174706176,           (52291747908702842344842889809762246649489 - 520996778817151392090736149644507525892649*I)/19342813113834066795298816,        (17472406829219127839967951180375981717322 + 23464704213841582137898905375041819568669*I)/4835703278458516698824704,        (-911026971811893092350229536132730760943307 + 150799318130900944080399439626714846752360*I)/38685626227668133590597632,         (26234457233977042811089020440646443590687 - 45650293039576452023692126463683727692890*I)/9671406556917033397649408,       3*(288348388717468992528382586652654351121357 + 454526517721403048270274049572136109264668*I)/77371252455336267181195264,        (-91583492367747094223295011999405657956347 - 12704691128268298435362255538069612411331*I)/19342813113834066795298816,          (411208730251327843849027957710164064354221 - 569898526380691606955496789378230959965898*I)/38685626227668133590597632],
#         [    (27127513117071487872628354831658811211795 - 37765296987901990355760582016892124833857*I)/4835703278458516698824704,     (1741779916057680444272938534338833170625435 + 3083041729779495966997526404685535449810378*I)/77371252455336267181195264, 3*(-60642236251815783728374561836962709533401 - 24630301165439580049891518846174101510744*I)/19342813113834066795298816,      3*(445885207364591681637745678755008757483408 - 350948497734812895032502179455610024541643*I)/38685626227668133590597632,    (-47373295621391195484367368282471381775684 + 219122969294089357477027867028071400054973*I)/19342813113834066795298816,       (-2801565819673198722993348253876353741520438 - 2250142129822658548391697042460298703335701*I)/77371252455336267181195264,      (801448252275607253266997552356128790317119 - 50890367688077858227059515894356594900558*I)/77371252455336267181195264,    (-5082187758525931944557763799137987573501207 + 11610432359082071866576699236013484487676124*I)/309485009821345068724781056,     (-328925127096560623794883760398247685166830 - 643447969697471610060622160899409680422019*I)/77371252455336267181195264,    15*(2954944669454003684028194956846659916299765 + 33434406416888505837444969347824812608566*I)/1237940039285380274899124224,      (-415749104352001509942256567958449835766827 + 479330966144175743357171151440020955412219*I)/77371252455336267181195264,  3*(-4639987285852134369449873547637372282914255 - 11994411888966030153196659207284951579243273*I)/1237940039285380274899124224],
#         [       (-478846096206269117345024348666145495601 + 1249092488629201351470551186322814883283*I)/302231454903657293676544,         (-17749319421930878799354766626365926894989 - 18264580106418628161818752318217357231971*I)/1208925819614629174706176,         (2801110795431528876849623279389579072819 + 363258850073786330770713557775566973248*I)/604462909807314587353088,          (-59053496693129013745775512127095650616252 + 78143588734197260279248498898321500167517*I)/4835703278458516698824704,         (-283186724922498212468162690097101115349 - 6443437753863179883794497936345437398276*I)/1208925819614629174706176,            (188799118826748909206887165661384998787543 + 84274736720556630026311383931055307398820*I)/9671406556917033397649408,         (-5482217151670072904078758141270295025989 + 1818284338672191024475557065444481298568*I)/1208925819614629174706176,          (56564463395350195513805521309731217952281 - 360208541416798112109946262159695452898431*I)/19342813113834066795298816,        11*(1259539805728870739006416869463689438068 + 1409136581547898074455004171305324917387*I)/4835703278458516698824704,       5*(-123701190701414554945251071190688818343325 + 30997157322590424677294553832111902279712*I)/38685626227668133590597632,          (16130917381301373033736295883982414239781 - 32752041297570919727145380131926943374516*I)/9671406556917033397649408,          (650301385108223834347093740500375498354925 + 899526407681131828596801223402866051809258*I)/77371252455336267181195264],
#         [      (9011388245256140876590294262420614839483 + 8167917972423946282513000869327525382672*I)/1208925819614629174706176,       (-426393174084720190126376382194036323028924 + 180692224825757525982858693158209545430621*I)/9671406556917033397649408,     (24588556702197802674765733448108154175535 - 45091766022876486566421953254051868331066*I)/4835703278458516698824704,      (1872113939365285277373877183750416985089691 + 3030392393733212574744122057679633775773130*I)/77371252455336267181195264,    (-222173405538046189185754954524429864167549 - 75193157893478637039381059488387511299116*I)/19342813113834066795298816,        (2670821320766222522963689317316937579844558 - 2645837121493554383087981511645435472169191*I)/77371252455336267181195264,     5*(-2100110309556476773796963197283876204940 + 41957457246479840487980315496957337371937*I)/19342813113834066795298816,     (-5733743755499084165382383818991531258980593 - 3328949988392698205198574824396695027195732*I)/154742504910672534362390528,      (707827994365259025461378911159398206329247 - 265730616623227695108042528694302299777294*I)/77371252455336267181195264,    (-1442501604682933002895864804409322823788319 + 11504137805563265043376405214378288793343879*I)/309485009821345068724781056,         (-56130472299445561499538726459719629522285 - 61117552419727805035810982426639329818864*I)/9671406556917033397649408,    (39053692321126079849054272431599539429908717 - 10209127700342570953247177602860848130710666*I)/1237940039285380274899124224]])
    M = Matrix(S('''[
        [             -3/4,       45/32 - 37*I/16,         1/4 + I/2,      -129/64 - 9*I/64,      1/4 - 5*I/16,      65/128 + 87*I/64],
        [-149/64 + 49*I/32, -177/128 - 1369*I/128,  125/64 + 87*I/64, -2063/256 + 541*I/128,  85/256 - 33*I/16,  805/128 + 2415*I/512],
        [          1/2 - I,         9/4 + 55*I/16,              -3/4,       45/32 - 37*I/16,         1/4 + I/2,      -129/64 - 9*I/64],
        [   -5/8 - 39*I/16,   2473/256 + 137*I/64, -149/64 + 49*I/32, -177/128 - 1369*I/128,  125/64 + 87*I/64, -2063/256 + 541*I/128],
        [            1 + I,         -19/4 + 5*I/4,           1/2 - I,         9/4 + 55*I/16,              -3/4,       45/32 - 37*I/16],
        [         21/8 + I,    -537/64 + 143*I/16,    -5/8 - 39*I/16,   2473/256 + 137*I/64, -149/64 + 49*I/32, -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert M**10 == Matrix(S('''[
            [     7369525394972778926719607798014571861/604462909807314587353088 - 229284202061790301477392339912557559*I/151115727451828646838272,   -19704281515163975949388435612632058035/1208925819614629174706176 + 14319858347987648723768698170712102887*I/302231454903657293676544,      -3623281909451783042932142262164941211/604462909807314587353088 - 6039240602494288615094338643452320495*I/604462909807314587353088,    109260497799140408739847239685705357695/2417851639229258349412352 - 7427566006564572463236368211555511431*I/2417851639229258349412352, -16095803767674394244695716092817006641/2417851639229258349412352 + 10336681897356760057393429626719177583*I/1208925819614629174706176,    -42207883340488041844332828574359769743/2417851639229258349412352 - 182332262671671273188016400290188468499*I/4835703278458516698824704],
            [50566491050825573392726324995779608259/1208925819614629174706176 - 90047007594468146222002432884052362145*I/2417851639229258349412352,  74273703462900000967697427843983822011/1208925819614629174706176 + 265947522682943571171988741842776095421*I/1208925819614629174706176, -116900341394390200556829767923360888429/2417851639229258349412352 - 53153263356679268823910621474478756845*I/2417851639229258349412352, 195407378023867871243426523048612490249/1208925819614629174706176 - 1242417915995360200584837585002906728929*I/9671406556917033397649408,   -863597594389821970177319682495878193/302231454903657293676544 + 476936100741548328800725360758734300481*I/9671406556917033397649408, -3154451590535653853562472176601754835575/19342813113834066795298816 - 232909875490506237386836489998407329215*I/2417851639229258349412352],
            [   -1715444997702484578716037230949868543/302231454903657293676544 + 5009695651321306866158517287924120777*I/302231454903657293676544,     -30551582497996879620371947949342101301/604462909807314587353088 - 7632518367986526187139161303331519629*I/151115727451828646838272,           312680739924495153190604170938220575/18889465931478580854784 - 108664334509328818765959789219208459*I/75557863725914323419136,    -14693696966703036206178521686918865509/604462909807314587353088 + 72345386220900843930147151999899692401*I/1208925819614629174706176,  -8218872496728882299722894680635296519/1208925819614629174706176 - 16776782833358893712645864791807664983*I/1208925819614629174706176,      143237839169380078671242929143670635137/2417851639229258349412352 + 2883817094806115974748882735218469447*I/2417851639229258349412352],
            [   3087979417831061365023111800749855987/151115727451828646838272 + 34441942370802869368851419102423997089*I/604462909807314587353088, -148309181940158040917731426845476175667/604462909807314587353088 - 263987151804109387844966835369350904919*I/9671406556917033397649408,   50259518594816377378747711930008883165/1208925819614629174706176 - 95713974916869240305450001443767979653*I/2417851639229258349412352,  153466447023875527996457943521467271119/2417851639229258349412352 + 517285524891117105834922278517084871349*I/2417851639229258349412352,  -29184653615412989036678939366291205575/604462909807314587353088 - 27551322282526322041080173287022121083*I/1208925819614629174706176,   196404220110085511863671393922447671649/1208925819614629174706176 - 1204712019400186021982272049902206202145*I/9671406556917033397649408],
            [     -2632581805949645784625606590600098779/151115727451828646838272 - 589957435912868015140272627522612771*I/37778931862957161709568,     26727850893953715274702844733506310247/302231454903657293676544 - 10825791956782128799168209600694020481*I/302231454903657293676544,      -1036348763702366164044671908440791295/151115727451828646838272 + 3188624571414467767868303105288107375*I/151115727451828646838272,     -36814959939970644875593411585393242449/604462909807314587353088 - 18457555789119782404850043842902832647*I/302231454903657293676544,      12454491297984637815063964572803058647/604462909807314587353088 - 340489532842249733975074349495329171*I/302231454903657293676544,      -19547211751145597258386735573258916681/604462909807314587353088 + 87299583775782199663414539883938008933*I/1208925819614629174706176],
            [  -40281994229560039213253423262678393183/604462909807314587353088 - 2939986850065527327299273003299736641*I/604462909807314587353088, 331940684638052085845743020267462794181/2417851639229258349412352 - 284574901963624403933361315517248458969*I/1208925819614629174706176,      6453843623051745485064693628073010961/302231454903657293676544 + 36062454107479732681350914931391590957*I/604462909807314587353088,  -147665869053634695632880753646441962067/604462909807314587353088 - 305987938660447291246597544085345123927*I/9671406556917033397649408,  107821369195275772166593879711259469423/2417851639229258349412352 - 11645185518211204108659001435013326687*I/302231454903657293676544,     64121228424717666402009446088588091619/1208925819614629174706176 + 265557133337095047883844369272389762133*I/1208925819614629174706176]]'''))


def test_issue_17247_expression_blowup_5():
    M = Matrix(6, 6, lambda i, j: 1 + (-1)**(i+j)*I)
    with dotprodsimp(True):
        assert M.charpoly('x') == PurePoly(x**6 + (-6 - 6*I)*x**5 + 36*I*x**4, x, domain='EX')


def test_issue_17247_expression_blowup_6():
    M = Matrix(8, 8, [x+i for i in range (64)])
    with dotprodsimp(True):
        assert M.det('bareiss') == 0


def test_issue_17247_expression_blowup_7():
    M = Matrix(6, 6, lambda i, j: 1 + (-1)**(i+j)*I)
    with dotprodsimp(True):
        assert M.det('berkowitz') == 0


def test_issue_17247_expression_blowup_8():
    M = Matrix(8, 8, [x+i for i in range (64)])
    with dotprodsimp(True):
        assert M.det('lu') == 0


def test_issue_17247_expression_blowup_9():
    M = Matrix(8, 8, [x+i for i in range (64)])
    with dotprodsimp(True):
        assert M.rref() == (Matrix([
            [1, 0, -1, -2, -3, -4, -5, -6],
            [0, 1,  2,  3,  4,  5,  6,  7],
            [0, 0,  0,  0,  0,  0,  0,  0],
            [0, 0,  0,  0,  0,  0,  0,  0],
            [0, 0,  0,  0,  0,  0,  0,  0],
            [0, 0,  0,  0,  0,  0,  0,  0],
            [0, 0,  0,  0,  0,  0,  0,  0],
            [0, 0,  0,  0,  0,  0,  0,  0]]), (0, 1))


def test_issue_17247_expression_blowup_10():
    M = Matrix(6, 6, lambda i, j: 1 + (-1)**(i+j)*I)
    with dotprodsimp(True):
        assert M.cofactor(0, 0) == 0


def test_issue_17247_expression_blowup_11():
    M = Matrix(6, 6, lambda i, j: 1 + (-1)**(i+j)*I)
    with dotprodsimp(True):
        assert M.cofactor_matrix() == Matrix(6, 6, [0]*36)


def test_issue_17247_expression_blowup_12():
    M = Matrix(6, 6, lambda i, j: 1 + (-1)**(i+j)*I)
    with dotprodsimp(True):
        assert M.eigenvals() == {6: 1, 6*I: 1, 0: 4}


def test_issue_17247_expression_blowup_13():
    M = Matrix([
        [    0, 1 - x, x + 1, 1 - x],
        [1 - x, x + 1,     0, x + 1],
        [    0, 1 - x, x + 1, 1 - x],
        [    0,     0,     1 - x, 0]])

    ev = M.eigenvects()
    assert ev[0] == (0, 2, [Matrix([0, -1, 0, 1])])
    assert ev[1][0] == x - sqrt(2)*(x - 1) + 1
    assert ev[1][1] == 1
    assert ev[1][2][0].expand(deep=False, numer=True) == Matrix([
        [(-x + sqrt(2)*(x - 1) - 1)/(x - 1)],
        [-4*x/(x**2 - 2*x + 1) + (x + 1)*(x - sqrt(2)*(x - 1) + 1)/(x**2 - 2*x + 1)],
        [(-x + sqrt(2)*(x - 1) - 1)/(x - 1)],
        [1]
    ])

    assert ev[2][0] == x + sqrt(2)*(x - 1) + 1
    assert ev[2][1] == 1
    assert ev[2][2][0].expand(deep=False, numer=True) == Matrix([
        [(-x - sqrt(2)*(x - 1) - 1)/(x - 1)],
        [-4*x/(x**2 - 2*x + 1) + (x + 1)*(x + sqrt(2)*(x - 1) + 1)/(x**2 - 2*x + 1)],
        [(-x - sqrt(2)*(x - 1) - 1)/(x - 1)],
        [1]
    ])


def test_issue_17247_expression_blowup_14():
    M = Matrix(8, 8, ([1+x, 1-x]*4 + [1-x, 1+x]*4)*4)
    with dotprodsimp(True):
        assert M.echelon_form() == Matrix([
            [x + 1, 1 - x, x + 1, 1 - x, x + 1, 1 - x, x + 1, 1 - x],
            [    0,   4*x,     0,   4*x,     0,   4*x,     0,   4*x],
            [    0,     0,     0,     0,     0,     0,     0,     0],
            [    0,     0,     0,     0,     0,     0,     0,     0],
            [    0,     0,     0,     0,     0,     0,     0,     0],
            [    0,     0,     0,     0,     0,     0,     0,     0],
            [    0,     0,     0,     0,     0,     0,     0,     0],
            [    0,     0,     0,     0,     0,     0,     0,     0]])


def test_issue_17247_expression_blowup_15():
    M = Matrix(8, 8, ([1+x, 1-x]*4 + [1-x, 1+x]*4)*4)
    with dotprodsimp(True):
        assert M.rowspace() == [Matrix([[x + 1, 1 - x, x + 1, 1 - x, x + 1, 1 - x, x + 1, 1 - x]]), Matrix([[0, 4*x, 0, 4*x, 0, 4*x, 0, 4*x]])]


def test_issue_17247_expression_blowup_16():
    M = Matrix(8, 8, ([1+x, 1-x]*4 + [1-x, 1+x]*4)*4)
    with dotprodsimp(True):
        assert M.columnspace() == [Matrix([[x + 1],[1 - x],[x + 1],[1 - x],[x + 1],[1 - x],[x + 1],[1 - x]]), Matrix([[1 - x],[x + 1],[1 - x],[x + 1],[1 - x],[x + 1],[1 - x],[x + 1]])]


def test_issue_17247_expression_blowup_17():
    M = Matrix(8, 8, [x+i for i in range (64)])
    with dotprodsimp(True):
        assert M.nullspace() == [
            Matrix([[1],[-2],[1],[0],[0],[0],[0],[0]]),
            Matrix([[2],[-3],[0],[1],[0],[0],[0],[0]]),
            Matrix([[3],[-4],[0],[0],[1],[0],[0],[0]]),
            Matrix([[4],[-5],[0],[0],[0],[1],[0],[0]]),
            Matrix([[5],[-6],[0],[0],[0],[0],[1],[0]]),
            Matrix([[6],[-7],[0],[0],[0],[0],[0],[1]])]


def test_issue_17247_expression_blowup_18():
    M = Matrix(6, 6, ([1+x, 1-x]*3 + [1-x, 1+x]*3)*3)
    with dotprodsimp(True):
        assert not M.is_nilpotent()


def test_issue_17247_expression_blowup_19():
    M = Matrix(S('''[
        [             -3/4,                     0,         1/4 + I/2,                     0],
        [                0, -177/128 - 1369*I/128,                 0, -2063/256 + 541*I/128],
        [          1/2 - I,                     0,                 0,                     0],
        [                0,                     0,                 0, -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert not M.is_diagonalizable()


def test_issue_17247_expression_blowup_20():
    M = Matrix([
    [x + 1,  1 - x,      0,      0],
    [1 - x,  x + 1,      0,  x + 1],
    [    0,  1 - x,  x + 1,      0],
    [    0,      0,      0,  x + 1]])
    with dotprodsimp(True):
        assert M.diagonalize() == (Matrix([
            [1,  1, 0, (x + 1)/(x - 1)],
            [1, -1, 0,               0],
            [1,  1, 1,               0],
            [0,  0, 0,               1]]),
            Matrix([
            [2,   0,     0,     0],
            [0, 2*x,     0,     0],
            [0,   0, x + 1,     0],
            [0,   0,     0, x + 1]]))


def test_issue_17247_expression_blowup_21():
    M = Matrix(S('''[
        [             -3/4,       45/32 - 37*I/16,                   0,                     0],
        [-149/64 + 49*I/32, -177/128 - 1369*I/128,                   0, -2063/256 + 541*I/128],
        [                0,         9/4 + 55*I/16, 2473/256 + 137*I/64,                     0],
        [                0,                     0,                   0, -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert M.inv(method='GE') == Matrix(S('''[
            [-26194832/3470993 - 31733264*I/3470993, 156352/3470993 + 10325632*I/3470993, 0, -7741283181072/3306971225785 + 2999007604624*I/3306971225785],
            [4408224/3470993 - 9675328*I/3470993, -2422272/3470993 + 1523712*I/3470993, 0, -1824666489984/3306971225785 - 1401091949952*I/3306971225785],
            [-26406945676288/22270005630769 + 10245925485056*I/22270005630769, 7453523312640/22270005630769 + 1601616519168*I/22270005630769, 633088/6416033 - 140288*I/6416033, 872209227109521408/21217636514687010905 + 6066405081802389504*I/21217636514687010905],
            [0, 0, 0, -11328/952745 + 87616*I/952745]]'''))


def test_issue_17247_expression_blowup_22():
    M = Matrix(S('''[
        [             -3/4,       45/32 - 37*I/16,                   0,                     0],
        [-149/64 + 49*I/32, -177/128 - 1369*I/128,                   0, -2063/256 + 541*I/128],
        [                0,         9/4 + 55*I/16, 2473/256 + 137*I/64,                     0],
        [                0,                     0,                   0, -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert M.inv(method='LU') == Matrix(S('''[
            [-26194832/3470993 - 31733264*I/3470993, 156352/3470993 + 10325632*I/3470993, 0, -7741283181072/3306971225785 + 2999007604624*I/3306971225785],
            [4408224/3470993 - 9675328*I/3470993, -2422272/3470993 + 1523712*I/3470993, 0, -1824666489984/3306971225785 - 1401091949952*I/3306971225785],
            [-26406945676288/22270005630769 + 10245925485056*I/22270005630769, 7453523312640/22270005630769 + 1601616519168*I/22270005630769, 633088/6416033 - 140288*I/6416033, 872209227109521408/21217636514687010905 + 6066405081802389504*I/21217636514687010905],
            [0, 0, 0, -11328/952745 + 87616*I/952745]]'''))


def test_issue_17247_expression_blowup_23():
    M = Matrix(S('''[
        [             -3/4,       45/32 - 37*I/16,                   0,                     0],
        [-149/64 + 49*I/32, -177/128 - 1369*I/128,                   0, -2063/256 + 541*I/128],
        [                0,         9/4 + 55*I/16, 2473/256 + 137*I/64,                     0],
        [                0,                     0,                   0, -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert M.inv(method='ADJ').expand() == Matrix(S('''[
            [-26194832/3470993 - 31733264*I/3470993, 156352/3470993 + 10325632*I/3470993, 0, -7741283181072/3306971225785 + 2999007604624*I/3306971225785],
            [4408224/3470993 - 9675328*I/3470993, -2422272/3470993 + 1523712*I/3470993, 0, -1824666489984/3306971225785 - 1401091949952*I/3306971225785],
            [-26406945676288/22270005630769 + 10245925485056*I/22270005630769, 7453523312640/22270005630769 + 1601616519168*I/22270005630769, 633088/6416033 - 140288*I/6416033, 872209227109521408/21217636514687010905 + 6066405081802389504*I/21217636514687010905],
            [0, 0, 0, -11328/952745 + 87616*I/952745]]'''))


def test_issue_17247_expression_blowup_24():
    M = SparseMatrix(S('''[
        [             -3/4,       45/32 - 37*I/16,                   0,                     0],
        [-149/64 + 49*I/32, -177/128 - 1369*I/128,                   0, -2063/256 + 541*I/128],
        [                0,         9/4 + 55*I/16, 2473/256 + 137*I/64,                     0],
        [                0,                     0,                   0, -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert M.inv(method='CH') == Matrix(S('''[
            [-26194832/3470993 - 31733264*I/3470993, 156352/3470993 + 10325632*I/3470993, 0, -7741283181072/3306971225785 + 2999007604624*I/3306971225785],
            [4408224/3470993 - 9675328*I/3470993, -2422272/3470993 + 1523712*I/3470993, 0, -1824666489984/3306971225785 - 1401091949952*I/3306971225785],
            [-26406945676288/22270005630769 + 10245925485056*I/22270005630769, 7453523312640/22270005630769 + 1601616519168*I/22270005630769, 633088/6416033 - 140288*I/6416033, 872209227109521408/21217636514687010905 + 6066405081802389504*I/21217636514687010905],
            [0, 0, 0, -11328/952745 + 87616*I/952745]]'''))


def test_issue_17247_expression_blowup_25():
    M = SparseMatrix(S('''[
        [             -3/4,       45/32 - 37*I/16,                   0,                     0],
        [-149/64 + 49*I/32, -177/128 - 1369*I/128,                   0, -2063/256 + 541*I/128],
        [                0,         9/4 + 55*I/16, 2473/256 + 137*I/64,                     0],
        [                0,                     0,                   0, -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert M.inv(method='LDL') == Matrix(S('''[
            [-26194832/3470993 - 31733264*I/3470993, 156352/3470993 + 10325632*I/3470993, 0, -7741283181072/3306971225785 + 2999007604624*I/3306971225785],
            [4408224/3470993 - 9675328*I/3470993, -2422272/3470993 + 1523712*I/3470993, 0, -1824666489984/3306971225785 - 1401091949952*I/3306971225785],
            [-26406945676288/22270005630769 + 10245925485056*I/22270005630769, 7453523312640/22270005630769 + 1601616519168*I/22270005630769, 633088/6416033 - 140288*I/6416033, 872209227109521408/21217636514687010905 + 6066405081802389504*I/21217636514687010905],
            [0, 0, 0, -11328/952745 + 87616*I/952745]]'''))


def test_issue_17247_expression_blowup_26():
    M = Matrix(S('''[
        [             -3/4,       45/32 - 37*I/16,         1/4 + I/2,      -129/64 - 9*I/64,      1/4 - 5*I/16,      65/128 + 87*I/64,         -9/32 - I/16,      183/256 - 97*I/128],
        [-149/64 + 49*I/32, -177/128 - 1369*I/128,  125/64 + 87*I/64, -2063/256 + 541*I/128,  85/256 - 33*I/16,  805/128 + 2415*I/512, -219/128 + 115*I/256, 6301/4096 - 6609*I/1024],
        [          1/2 - I,         9/4 + 55*I/16,              -3/4,       45/32 - 37*I/16,         1/4 + I/2,      -129/64 - 9*I/64,         1/4 - 5*I/16,        65/128 + 87*I/64],
        [   -5/8 - 39*I/16,   2473/256 + 137*I/64, -149/64 + 49*I/32, -177/128 - 1369*I/128,  125/64 + 87*I/64, -2063/256 + 541*I/128,     85/256 - 33*I/16,    805/128 + 2415*I/512],
        [            1 + I,         -19/4 + 5*I/4,           1/2 - I,         9/4 + 55*I/16,              -3/4,       45/32 - 37*I/16,            1/4 + I/2,        -129/64 - 9*I/64],
        [         21/8 + I,    -537/64 + 143*I/16,    -5/8 - 39*I/16,   2473/256 + 137*I/64, -149/64 + 49*I/32, -177/128 - 1369*I/128,     125/64 + 87*I/64,   -2063/256 + 541*I/128],
        [               -2,         17/4 - 13*I/2,             1 + I,         -19/4 + 5*I/4,           1/2 - I,         9/4 + 55*I/16,                 -3/4,         45/32 - 37*I/16],
        [     1/4 + 13*I/4,    -825/64 - 147*I/32,          21/8 + I,    -537/64 + 143*I/16,    -5/8 - 39*I/16,   2473/256 + 137*I/64,    -149/64 + 49*I/32,   -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert M.rank() == 4


def test_issue_17247_expression_blowup_27():
    M = Matrix([
        [    0, 1 - x, x + 1, 1 - x],
        [1 - x, x + 1,     0, x + 1],
        [    0, 1 - x, x + 1, 1 - x],
        [    0,     0,     1 - x, 0]])
    with dotprodsimp(True):
        P, J = M.jordan_form()
        assert P.expand() == Matrix(S('''[
            [    0,  4*x/(x**2 - 2*x + 1), -(-17*x**4 + 12*sqrt(2)*x**4 - 4*sqrt(2)*x**3 + 6*x**3 - 6*x - 4*sqrt(2)*x + 12*sqrt(2) + 17)/(-7*x**4 + 5*sqrt(2)*x**4 - 6*sqrt(2)*x**3 + 8*x**3 - 2*x**2 + 8*x + 6*sqrt(2)*x - 5*sqrt(2) - 7), -(12*sqrt(2)*x**4 + 17*x**4 - 6*x**3 - 4*sqrt(2)*x**3 - 4*sqrt(2)*x + 6*x - 17 + 12*sqrt(2))/(7*x**4 + 5*sqrt(2)*x**4 - 6*sqrt(2)*x**3 - 8*x**3 + 2*x**2 - 8*x + 6*sqrt(2)*x - 5*sqrt(2) + 7)],
            [x - 1, x/(x - 1) + 1/(x - 1),                       (-7*x**3 + 5*sqrt(2)*x**3 - x**2 + sqrt(2)*x**2 - sqrt(2)*x - x - 5*sqrt(2) - 7)/(-3*x**3 + 2*sqrt(2)*x**3 - 2*sqrt(2)*x**2 + 3*x**2 + 2*sqrt(2)*x + 3*x - 3 - 2*sqrt(2)),                       (7*x**3 + 5*sqrt(2)*x**3 + x**2 + sqrt(2)*x**2 - sqrt(2)*x + x - 5*sqrt(2) + 7)/(2*sqrt(2)*x**3 + 3*x**3 - 3*x**2 - 2*sqrt(2)*x**2 - 3*x + 2*sqrt(2)*x - 2*sqrt(2) + 3)],
            [    0,                     1,                                                                                            -(-3*x**2 + 2*sqrt(2)*x**2 + 2*x - 3 - 2*sqrt(2))/(-x**2 + sqrt(2)*x**2 - 2*sqrt(2)*x + 1 + sqrt(2)),                                                                                            -(2*sqrt(2)*x**2 + 3*x**2 - 2*x - 2*sqrt(2) + 3)/(x**2 + sqrt(2)*x**2 - 2*sqrt(2)*x - 1 + sqrt(2))],
            [1 - x,                     0,                                                                                                                                                                                               1,                                                                                                                                                                                             1]]''')).expand()
        assert J == Matrix(S('''[
            [0, 1,                       0,                       0],
            [0, 0,                       0,                       0],
            [0, 0, x - sqrt(2)*(x - 1) + 1,                       0],
            [0, 0,                       0, x + sqrt(2)*(x - 1) + 1]]'''))


def test_issue_17247_expression_blowup_28():
    M = Matrix(S('''[
        [             -3/4,       45/32 - 37*I/16,                   0,                     0],
        [-149/64 + 49*I/32, -177/128 - 1369*I/128,                   0, -2063/256 + 541*I/128],
        [                0,         9/4 + 55*I/16, 2473/256 + 137*I/64,                     0],
        [                0,                     0,                   0, -177/128 - 1369*I/128]]'''))
    with dotprodsimp(True):
        assert M.singular_values() == S('''[
            sqrt(14609315/131072 + sqrt(64789115132571/2147483648 - 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3) + 76627253330829751075/(35184372088832*sqrt(64789115132571/4294967296 + 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)) + 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3))) - 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)))/2 + sqrt(64789115132571/4294967296 + 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)) + 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3))/2),
            sqrt(14609315/131072 - sqrt(64789115132571/2147483648 - 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3) + 76627253330829751075/(35184372088832*sqrt(64789115132571/4294967296 + 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)) + 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3))) - 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)))/2 + sqrt(64789115132571/4294967296 + 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)) + 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3))/2),
            sqrt(14609315/131072 - sqrt(64789115132571/4294967296 + 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)) + 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3))/2 + sqrt(64789115132571/2147483648 - 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3) - 76627253330829751075/(35184372088832*sqrt(64789115132571/4294967296 + 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)) + 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3))) - 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)))/2),
            sqrt(14609315/131072 - sqrt(64789115132571/4294967296 + 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)) + 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3))/2 - sqrt(64789115132571/2147483648 - 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3) - 76627253330829751075/(35184372088832*sqrt(64789115132571/4294967296 + 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)) + 2*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3))) - 3546944054712886603889144627/(110680464442257309696*(25895222463957462655758224991455280215303/633825300114114700748351602688 + sqrt(1213909058710955930446995195883114969038524625997915131236390724543989220134670)*I/22282920707136844948184236032)**(1/3)))/2)]''')


def test_issue_16823():
    # This still needs to be fixed if not using dotprodsimp.
    M = Matrix(S('''[
        [1+I,-19/4+5/4*I,1/2-I,9/4+55/16*I,-3/4,45/32-37/16*I,1/4+1/2*I,-129/64-9/64*I,1/4-5/16*I,65/128+87/64*I,-9/32-1/16*I,183/256-97/128*I,3/64+13/64*I,-23/32-59/256*I,15/128-3/32*I,19/256+551/1024*I],
        [21/8+I,-537/64+143/16*I,-5/8-39/16*I,2473/256+137/64*I,-149/64+49/32*I,-177/128-1369/128*I,125/64+87/64*I,-2063/256+541/128*I,85/256-33/16*I,805/128+2415/512*I,-219/128+115/256*I,6301/4096-6609/1024*I,119/128+143/128*I,-10879/2048+4343/4096*I,129/256-549/512*I,42533/16384+29103/8192*I],
        [-2,17/4-13/2*I,1+I,-19/4+5/4*I,1/2-I,9/4+55/16*I,-3/4,45/32-37/16*I,1/4+1/2*I,-129/64-9/64*I,1/4-5/16*I,65/128+87/64*I,-9/32-1/16*I,183/256-97/128*I,3/64+13/64*I,-23/32-59/256*I],
        [1/4+13/4*I,-825/64-147/32*I,21/8+I,-537/64+143/16*I,-5/8-39/16*I,2473/256+137/64*I,-149/64+49/32*I,-177/128-1369/128*I,125/64+87/64*I,-2063/256+541/128*I,85/256-33/16*I,805/128+2415/512*I,-219/128+115/256*I,6301/4096-6609/1024*I,119/128+143/128*I,-10879/2048+4343/4096*I],
        [-4*I,27/2+6*I,-2,17/4-13/2*I,1+I,-19/4+5/4*I,1/2-I,9/4+55/16*I,-3/4,45/32-37/16*I,1/4+1/2*I,-129/64-9/64*I,1/4-5/16*I,65/128+87/64*I,-9/32-1/16*I,183/256-97/128*I],
        [1/4+5/2*I,-23/8-57/16*I,1/4+13/4*I,-825/64-147/32*I,21/8+I,-537/64+143/16*I,-5/8-39/16*I,2473/256+137/64*I,-149/64+49/32*I,-177/128-1369/128*I,125/64+87/64*I,-2063/256+541/128*I,85/256-33/16*I,805/128+2415/512*I,-219/128+115/256*I,6301/4096-6609/1024*I],
        [-4,9-5*I,-4*I,27/2+6*I,-2,17/4-13/2*I,1+I,-19/4+5/4*I,1/2-I,9/4+55/16*I,-3/4,45/32-37/16*I,1/4+1/2*I,-129/64-9/64*I,1/4-5/16*I,65/128+87/64*I],
        [-2*I,119/8+29/4*I,1/4+5/2*I,-23/8-57/16*I,1/4+13/4*I,-825/64-147/32*I,21/8+I,-537/64+143/16*I,-5/8-39/16*I,2473/256+137/64*I,-149/64+49/32*I,-177/128-1369/128*I,125/64+87/64*I,-2063/256+541/128*I,85/256-33/16*I,805/128+2415/512*I],
        [0,-6,-4,9-5*I,-4*I,27/2+6*I,-2,17/4-13/2*I,1+I,-19/4+5/4*I,1/2-I,9/4+55/16*I,-3/4,45/32-37/16*I,1/4+1/2*I,-129/64-9/64*I],
        [1,-9/4+3*I,-2*I,119/8+29/4*I,1/4+5/2*I,-23/8-57/16*I,1/4+13/4*I,-825/64-147/32*I,21/8+I,-537/64+143/16*I,-5/8-39/16*I,2473/256+137/64*I,-149/64+49/32*I,-177/128-1369/128*I,125/64+87/64*I,-2063/256+541/128*I],
        [0,-4*I,0,-6,-4,9-5*I,-4*I,27/2+6*I,-2,17/4-13/2*I,1+I,-19/4+5/4*I,1/2-I,9/4+55/16*I,-3/4,45/32-37/16*I],
        [0,1/4+1/2*I,1,-9/4+3*I,-2*I,119/8+29/4*I,1/4+5/2*I,-23/8-57/16*I,1/4+13/4*I,-825/64-147/32*I,21/8+I,-537/64+143/16*I,-5/8-39/16*I,2473/256+137/64*I,-149/64+49/32*I,-177/128-1369/128*I]]'''))
    with dotprodsimp(True):
        assert M.rank() == 8


def test_issue_18531():
    # solve_linear_system still needs fixing but the rref works.
    M = Matrix([
        [1, 1, 1, 1, 1, 0, 1, 0, 0],
        [1 + sqrt(2), -1 + sqrt(2), 1 - sqrt(2), -sqrt(2) - 1, 1, 1, -1, 1, 1],
        [-5 + 2*sqrt(2), -5 - 2*sqrt(2), -5 - 2*sqrt(2), -5 + 2*sqrt(2), -7, 2, -7, -2, 0],
        [-3*sqrt(2) - 1, 1 - 3*sqrt(2), -1 + 3*sqrt(2), 1 + 3*sqrt(2), -7, -5, 7, -5, 3],
        [7 - 4*sqrt(2), 4*sqrt(2) + 7, 4*sqrt(2) + 7, 7 - 4*sqrt(2), 7, -12, 7, 12, 0],
        [-1 + 3*sqrt(2), 1 + 3*sqrt(2), -3*sqrt(2) - 1, 1 - 3*sqrt(2), 7, -5, -7, -5, 3],
        [-3 + 2*sqrt(2), -3 - 2*sqrt(2), -3 - 2*sqrt(2), -3 + 2*sqrt(2), -1, 2, -1, -2, 0],
        [1 - sqrt(2), -sqrt(2) - 1, 1 + sqrt(2), -1 + sqrt(2), -1, 1, 1, 1, 1]
        ])
    with dotprodsimp(True):
        assert M.rref() == (Matrix([
            [1, 0, 0, 0, 0, 0, 0, 0,  S(1)/2],
            [0, 1, 0, 0, 0, 0, 0, 0, -S(1)/2],
            [0, 0, 1, 0, 0, 0, 0, 0,  S(1)/2],
            [0, 0, 0, 1, 0, 0, 0, 0, -S(1)/2],
            [0, 0, 0, 0, 1, 0, 0, 0,    0],
            [0, 0, 0, 0, 0, 1, 0, 0, -S(1)/2],
            [0, 0, 0, 0, 0, 0, 1, 0,    0],
            [0, 0, 0, 0, 0, 0, 0, 1, -S(1)/2]]), (0, 1, 2, 3, 4, 5, 6, 7))


def test_creation():
    raises(ValueError, lambda: Matrix(5, 5, range(20)))
    raises(ValueError, lambda: Matrix(5, -1, []))
    raises(IndexError, lambda: Matrix((1, 2))[2])
    with raises(IndexError):
        Matrix((1, 2))[3] = 5

    assert Matrix() == Matrix([]) == Matrix([[]]) == Matrix(0, 0, [])
    # anything used to be allowed in a matrix
    with warns_deprecated_sympy():
        assert Matrix([[[1], (2,)]]).tolist() == [[[1], (2,)]]
    with warns_deprecated_sympy():
        assert Matrix([[[1], (2,)]]).T.tolist() == [[[1]], [(2,)]]
    M = Matrix([[0]])
    with warns_deprecated_sympy():
        M[0, 0] = S.EmptySet

    a = Matrix([[x, 0], [0, 0]])
    m = a
    assert m.cols == m.rows
    assert m.cols == 2
    assert m[:] == [x, 0, 0, 0]

    b = Matrix(2, 2, [x, 0, 0, 0])
    m = b
    assert m.cols == m.rows
    assert m.cols == 2
    assert m[:] == [x, 0, 0, 0]

    assert a == b

    assert Matrix(b) == b

    c23 = Matrix(2, 3, range(1, 7))
    c13 = Matrix(1, 3, range(7, 10))
    c = Matrix([c23, c13])
    assert c.cols == 3
    assert c.rows == 3
    assert c[:] == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    assert Matrix(eye(2)) == eye(2)
    assert ImmutableMatrix(ImmutableMatrix(eye(2))) == ImmutableMatrix(eye(2))
    assert ImmutableMatrix(c) == c.as_immutable()
    assert Matrix(ImmutableMatrix(c)) == ImmutableMatrix(c).as_mutable()

    assert c is not Matrix(c)

    dat = [[ones(3,2), ones(3,3)*2], [ones(2,3)*3, ones(2,2)*4]]
    M = Matrix(dat)
    assert M == Matrix([
        [1, 1, 2, 2, 2],
        [1, 1, 2, 2, 2],
        [1, 1, 2, 2, 2],
        [3, 3, 3, 4, 4],
        [3, 3, 3, 4, 4]])
    assert M.tolist() != dat
    # keep block form if evaluate=False
    assert Matrix(dat, evaluate=False).tolist() == dat
    A = MatrixSymbol("A", 2, 2)
    dat = [ones(2), A]
    assert Matrix(dat) == Matrix([
    [      1,       1],
    [      1,       1],
    [A[0, 0], A[0, 1]],
    [A[1, 0], A[1, 1]]])
    with warns_deprecated_sympy():
        assert Matrix(dat, evaluate=False).tolist() == [[i] for i in dat]

    # 0-dim tolerance
    assert Matrix([ones(2), ones(0)]) == Matrix([ones(2)])
    raises(ValueError, lambda: Matrix([ones(2), ones(0, 3)]))
    raises(ValueError, lambda: Matrix([ones(2), ones(3, 0)]))

    # mix of Matrix and iterable
    M = Matrix([[1, 2], [3, 4]])
    M2 = Matrix([M, (5, 6)])
    assert M2 == Matrix([[1, 2], [3, 4], [5, 6]])


def test_irregular_block():
    assert Matrix.irregular(3, ones(2,1), ones(3,3)*2, ones(2,2)*3,
        ones(1,1)*4, ones(2,2)*5, ones(1,2)*6, ones(1,2)*7) == Matrix([
        [1, 2, 2, 2, 3, 3],
        [1, 2, 2, 2, 3, 3],
        [4, 2, 2, 2, 5, 5],
        [6, 6, 7, 7, 5, 5]])


def test_slicing():
    m0 = eye(4)
    assert m0[:3, :3] == eye(3)
    assert m0[2:4, 0:2] == zeros(2)

    m1 = Matrix(3, 3, lambda i, j: i + j)
    assert m1[0, :] == Matrix(1, 3, (0, 1, 2))
    assert m1[1:3, 1] == Matrix(2, 1, (2, 3))

    m2 = Matrix([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]])
    assert m2[:, -1] == Matrix(4, 1, [3, 7, 11, 15])
    assert m2[-2:, :] == Matrix([[8, 9, 10, 11], [12, 13, 14, 15]])


def test_submatrix_assignment():
    m = zeros(4)
    m[2:4, 2:4] = eye(2)
    assert m == Matrix(((0, 0, 0, 0),
                        (0, 0, 0, 0),
                        (0, 0, 1, 0),
                        (0, 0, 0, 1)))
    m[:2, :2] = eye(2)
    assert m == eye(4)
    m[:, 0] = Matrix(4, 1, (1, 2, 3, 4))
    assert m == Matrix(((1, 0, 0, 0),
                        (2, 1, 0, 0),
                        (3, 0, 1, 0),
                        (4, 0, 0, 1)))
    m[:, :] = zeros(4)
    assert m == zeros(4)
    m[:, :] = [(1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16)]
    assert m == Matrix(((1, 2, 3, 4),
                        (5, 6, 7, 8),
                        (9, 10, 11, 12),
                        (13, 14, 15, 16)))
    m[:2, 0] = [0, 0]
    assert m == Matrix(((0, 2, 3, 4),
                        (0, 6, 7, 8),
                        (9, 10, 11, 12),
                        (13, 14, 15, 16)))


def test_reshape():
    m0 = eye(3)
    assert m0.reshape(1, 9) == Matrix(1, 9, (1, 0, 0, 0, 1, 0, 0, 0, 1))
    m1 = Matrix(3, 4, lambda i, j: i + j)
    assert m1.reshape(
        4, 3) == Matrix(((0, 1, 2), (3, 1, 2), (3, 4, 2), (3, 4, 5)))
    assert m1.reshape(2, 6) == Matrix(((0, 1, 2, 3, 1, 2), (3, 4, 2, 3, 4, 5)))


def test_applyfunc():
    m0 = eye(3)
    assert m0.applyfunc(lambda x: 2*x) == eye(3)*2
    assert m0.applyfunc(lambda x: 0) == zeros(3)


def test_expand():
    m0 = Matrix([[x*(x + y), 2], [((x + y)*y)*x, x*(y + x*(x + y))]])
    # Test if expand() returns a matrix
    m1 = m0.expand()
    assert m1 == Matrix(
        [[x*y + x**2, 2], [x*y**2 + y*x**2, x*y + y*x**2 + x**3]])

    a = Symbol('a', real=True)

    assert Matrix([exp(I*a)]).expand(complex=True) == \
        Matrix([cos(a) + I*sin(a)])

    assert Matrix([[0, 1, 2], [0, 0, -1], [0, 0, 0]]).exp() == Matrix([
        [1, 1, Rational(3, 2)],
        [0, 1, -1],
        [0, 0, 1]]
    )


def test_refine():
    m0 = Matrix([[Abs(x)**2, sqrt(x**2)],
                [sqrt(x**2)*Abs(y)**2, sqrt(y**2)*Abs(x)**2]])
    m1 = m0.refine(Q.real(x) & Q.real(y))
    assert m1 == Matrix([[x**2, Abs(x)], [y**2*Abs(x), x**2*Abs(y)]])

    m1 = m0.refine(Q.positive(x) & Q.positive(y))
    assert m1 == Matrix([[x**2, x], [x*y**2, x**2*y]])

    m1 = m0.refine(Q.negative(x) & Q.negative(y))
    assert m1 == Matrix([[x**2, -x], [-x*y**2, -x**2*y]])


def test_random():
    M = randMatrix(3, 3)
    M = randMatrix(3, 3, seed=3)
    assert M == randMatrix(3, 3, seed=3)

    M = randMatrix(3, 4, 0, 150)
    M = randMatrix(3, seed=4, symmetric=True)
    assert M == randMatrix(3, seed=4, symmetric=True)

    S = M.copy()
    S.simplify()
    assert S == M  # doesn't fail when elements are Numbers, not int

    rng = random.Random(4)
    assert M == randMatrix(3, symmetric=True, prng=rng)

    # Ensure symmetry
    for size in (10, 11): # Test odd and even
        for percent in (100, 70, 30):
            M = randMatrix(size, symmetric=True, percent=percent, prng=rng)
            assert M == M.T

    M = randMatrix(10, min=1, percent=70)
    zero_count = 0
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if M[i, j] == 0:
                zero_count += 1
    assert zero_count == 30


def test_inverse():
    A = eye(4)
    assert A.inv() == eye(4)
    assert A.inv(method="LU") == eye(4)
    assert A.inv(method="ADJ") == eye(4)
    assert A.inv(method="CH") == eye(4)
    assert A.inv(method="LDL") == eye(4)
    assert A.inv(method="QR") == eye(4)
    A = Matrix([[2, 3, 5],
                [3, 6, 2],
                [8, 3, 6]])
    Ainv = A.inv()
    assert A*Ainv == eye(3)
    assert A.inv(method="LU") == Ainv
    assert A.inv(method="ADJ") == Ainv
    assert A.inv(method="CH") == Ainv
    assert A.inv(method="LDL") == Ainv
    assert A.inv(method="QR") == Ainv

    AA = Matrix([[0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
            [1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0],
            [1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
            [1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
            [1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1],
            [0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1],
            [0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0],
            [1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0],
            [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1],
            [1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0],
            [0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0],
            [1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1],
            [0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1],
            [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1],
            [0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
            [0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1],
            [0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0],
            [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0]])
    assert AA.inv(method="BLOCK") * AA == eye(AA.shape[0])
    # test that immutability is not a problem
    cls = ImmutableMatrix
    m = cls([[48, 49, 31],
             [ 9, 71, 94],
             [59, 28, 65]])
    assert all(type(m.inv(s)) is cls for s in 'GE ADJ LU CH LDL QR'.split())
    cls = ImmutableSparseMatrix
    m = cls([[48, 49, 31],
             [ 9, 71, 94],
             [59, 28, 65]])
    assert all(type(m.inv(s)) is cls for s in 'GE ADJ LU CH LDL QR'.split())


def test_jacobian_hessian():
    L = Matrix(1, 2, [x**2*y, 2*y**2 + x*y])
    syms = [x, y]
    assert L.jacobian(syms) == Matrix([[2*x*y, x**2], [y, 4*y + x]])

    L = Matrix(1, 2, [x, x**2*y**3])
    assert L.jacobian(syms) == Matrix([[1, 0], [2*x*y**3, x**2*3*y**2]])

    f = x**2*y
    syms = [x, y]
    assert hessian(f, syms) == Matrix([[2*y, 2*x], [2*x, 0]])

    f = x**2*y**3
    assert hessian(f, syms) == \
        Matrix([[2*y**3, 6*x*y**2], [6*x*y**2, 6*x**2*y]])

    f = z + x*y**2
    g = x**2 + 2*y**3
    ans = Matrix([[0,   2*y],
                  [2*y, 2*x]])
    assert ans == hessian(f, Matrix([x, y]))
    assert ans == hessian(f, Matrix([x, y]).T)
    assert hessian(f, (y, x), [g]) == Matrix([
        [     0, 6*y**2, 2*x],
        [6*y**2,    2*x, 2*y],
        [   2*x,    2*y,   0]])


def test_wronskian():
    assert wronskian([cos(x), sin(x)], x) == cos(x)**2 + sin(x)**2
    assert wronskian([exp(x), exp(2*x)], x) == exp(3*x)
    assert wronskian([exp(x), x], x) == exp(x) - x*exp(x)
    assert wronskian([1, x, x**2], x) == 2
    w1 = -6*exp(x)*sin(x)*x + 6*cos(x)*exp(x)*x**2 - 6*exp(x)*cos(x)*x - \
        exp(x)*cos(x)*x**3 + exp(x)*sin(x)*x**3
    assert wronskian([exp(x), cos(x), x**3], x).expand() == w1
    assert wronskian([exp(x), cos(x), x**3], x, method='berkowitz').expand() \
        == w1
    w2 = -x**3*cos(x)**2 - x**3*sin(x)**2 - 6*x*cos(x)**2 - 6*x*sin(x)**2
    assert wronskian([sin(x), cos(x), x**3], x).expand() == w2
    assert wronskian([sin(x), cos(x), x**3], x, method='berkowitz').expand() \
        == w2
    assert wronskian([], x) == 1


def test_xreplace():
    assert Matrix([[1, x], [x, 4]]).xreplace({x: 5}) == \
        Matrix([[1, 5], [5, 4]])
    assert Matrix([[x, 2], [x + y, 4]]).xreplace({x: -1, y: -2}) == \
        Matrix([[-1, 2], [-3, 4]])
    for cls in all_classes:
        assert Matrix([[2, 0], [0, 2]]) == cls.eye(2).xreplace({1: 2})


def test_simplify():
    n = Symbol('n')
    f = Function('f')

    M = Matrix([[            1/x + 1/y,                 (x + x*y) / x  ],
                [ (f(x) + y*f(x))/f(x), 2 * (1/n - cos(n * pi)/n) / pi ]])
    M.simplify()
    assert M == Matrix([[ (x + y)/(x * y),                        1 + y ],
                        [           1 + y, 2*((1 - 1*cos(pi*n))/(pi*n)) ]])
    eq = (1 + x)**2
    M = Matrix([[eq]])
    M.simplify()
    assert M == Matrix([[eq]])
    M.simplify(ratio=oo)
    assert M == Matrix([[eq.simplify(ratio=oo)]])

    n = Symbol('n')
    f = Function('f')

    M = ImmutableMatrix([
        [            1/x + 1/y,                 (x + x*y) / x  ],
        [ (f(x) + y*f(x))/f(x), 2 * (1/n - cos(n * pi)/n) / pi ]
    ])
    assert M.simplify() == Matrix([
        [ (x + y)/(x * y),                        1 + y ],
        [           1 + y, 2*((1 - 1*cos(pi*n))/(pi*n)) ]
    ])

    eq = (1 + x)**2
    M = ImmutableMatrix([[eq]])
    assert M.simplify() == Matrix([[eq]])
    assert M.simplify(ratio=oo) == Matrix([[eq.simplify(ratio=oo)]])

    assert simplify(ImmutableMatrix([[sin(x)**2 + cos(x)**2]])) == \
                    ImmutableMatrix([[1]])

    # https://github.com/sympy/sympy/issues/19353
    m = Matrix([[30, 2], [3, 4]])
    assert (1/(m.trace())).simplify() == Rational(1, 34)

def test_transpose():
    M = Matrix([[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]])
    assert M.T == Matrix( [ [1, 1],
                            [2, 2],
                            [3, 3],
                            [4, 4],
                            [5, 5],
                            [6, 6],
                            [7, 7],
                            [8, 8],
                            [9, 9],
                            [0, 0] ])
    assert M.T.T == M
    assert M.T == M.transpose()


def test_conj_dirac():
    raises(AttributeError, lambda: eye(3).D)

    M = Matrix([[1, I, I, I],
                [0, 1, I, I],
                [0, 0, 1, I],
                [0, 0, 0, 1]])

    assert M.D == Matrix([[ 1,  0,  0,  0],
                          [-I,  1,  0,  0],
                          [-I, -I, -1,  0],
                          [-I, -I,  I, -1]])


def test_trace():
    M = Matrix([[1, 0, 0],
                [0, 5, 0],
                [0, 0, 8]])
    assert M.trace() == 14


def test_shape():
    m = Matrix(1, 2, [0, 0])
    assert m.shape == (1, 2)
    M = Matrix([[x, 0, 0],
                [0, y, 0]])
    assert M.shape == (2, 3)


def test_col_row_op():
    M = Matrix([[x, 0, 0],
                [0, y, 0]])
    M.row_op(1, lambda r, j: r + j + 1)
    assert M == Matrix([[x,     0, 0],
                        [1, y + 2, 3]])

    M.col_op(0, lambda c, j: c + y**j)
    assert M == Matrix([[x + 1,     0, 0],
                        [1 + y, y + 2, 3]])

    # neither row nor slice give copies that allow the original matrix to
    # be changed
    assert M.row(0) == Matrix([[x + 1, 0, 0]])
    r1 = M.row(0)
    r1[0] = 42
    assert M[0, 0] == x + 1
    r1 = M[0, :-1]  # also testing negative slice
    r1[0] = 42
    assert M[0, 0] == x + 1
    c1 = M.col(0)
    assert c1 == Matrix([x + 1, 1 + y])
    c1[0] = 0
    assert M[0, 0] == x + 1
    c1 = M[:, 0]
    c1[0] = 42
    assert M[0, 0] == x + 1


def test_row_mult():
    M = Matrix([[1,2,3],
               [4,5,6]])
    M.row_mult(1,3)
    assert M[1,0] == 12
    assert M[0,0] == 1
    assert M[1,2] == 18


def test_row_add():
    M = Matrix([[1,2,3],
               [4,5,6],
               [1,1,1]])
    M.row_add(2,0,5)
    assert M[0,0] == 6
    assert M[1,0] == 4
    assert M[0,2] == 8


def test_zip_row_op():
    for cls in mutable_classes: # XXX: immutable matrices don't support row ops
        M = cls.eye(3)
        M.zip_row_op(1, 0, lambda v, u: v + 2*u)
        assert M == cls([[1, 0, 0],
                         [2, 1, 0],
                         [0, 0, 1]])

        M = cls.eye(3)*2
        M[0, 1] = -1
        M.zip_row_op(1, 0, lambda v, u: v + 2*u); M
        assert M == cls([[2, -1, 0],
                         [4,  0, 0],
                         [0,  0, 2]])


def test_issue_3950():
    m = Matrix([1, 2, 3])
    a = Matrix([1, 2, 3])
    b = Matrix([2, 2, 3])
    assert not (m in [])
    assert not (m in [1])
    assert m != 1
    assert m == a
    assert m != b


def test_issue_3981():
    class Index1:
        def __index__(self):
            return 1

    class Index2:
        def __index__(self):
            return 2
    index1 = Index1()
    index2 = Index2()

    m = Matrix([1, 2, 3])

    assert m[index2] == 3

    m[index2] = 5
    assert m[2] == 5

    m = Matrix([[1, 2, 3], [4, 5, 6]])
    assert m[index1, index2] == 6
    assert m[1, index2] == 6
    assert m[index1, 2] == 6

    m[index1, index2] = 4
    assert m[1, 2] == 4
    m[1, index2] = 6
    assert m[1, 2] == 6
    m[index1, 2] = 8
    assert m[1, 2] == 8


def test_is_upper():
    a = Matrix([[1, 2, 3]])
    assert a.is_upper is True
    a = Matrix([[1], [2], [3]])
    assert a.is_upper is False
    a = zeros(4, 2)
    assert a.is_upper is True


def test_is_lower():
    a = Matrix([[1, 2, 3]])
    assert a.is_lower is False
    a = Matrix([[1], [2], [3]])
    assert a.is_lower is True


def test_is_nilpotent():
    a = Matrix(4, 4, [0, 2, 1, 6, 0, 0, 1, 2, 0, 0, 0, 3, 0, 0, 0, 0])
    assert a.is_nilpotent()
    a = Matrix([[1, 0], [0, 1]])
    assert not a.is_nilpotent()
    a = Matrix([])
    assert a.is_nilpotent()


def test_zeros_ones_fill():
    n, m = 3, 5

    a = zeros(n, m)
    a.fill( 5 )

    b = 5 * ones(n, m)

    assert a == b
    assert a.rows == b.rows == 3
    assert a.cols == b.cols == 5
    assert a.shape == b.shape == (3, 5)
    assert zeros(2) == zeros(2, 2)
    assert ones(2) == ones(2, 2)
    assert zeros(2, 3) == Matrix(2, 3, [0]*6)
    assert ones(2, 3) == Matrix(2, 3, [1]*6)

    a.fill(0)
    assert a == zeros(n, m)


def test_empty_zeros():
    a = zeros(0)
    assert a == Matrix()
    a = zeros(0, 2)
    assert a.rows == 0
    assert a.cols == 2
    a = zeros(2, 0)
    assert a.rows == 2
    assert a.cols == 0


def test_issue_3749():
    a = Matrix([[x**2, x*y], [x*sin(y), x*cos(y)]])
    assert a.diff(x) == Matrix([[2*x, y], [sin(y), cos(y)]])
    assert Matrix([
        [x, -x, x**2],
        [exp(x), 1/x - exp(-x), x + 1/x]]).limit(x, oo) == \
        Matrix([[oo, -oo, oo], [oo, 0, oo]])
    assert Matrix([
        [(exp(x) - 1)/x, 2*x + y*x, x**x ],
        [1/x, abs(x), abs(sin(x + 1))]]).limit(x, 0) == \
        Matrix([[1, 0, 1], [oo, 0, sin(1)]])
    assert a.integrate(x) == Matrix([
        [Rational(1, 3)*x**3, y*x**2/2],
        [x**2*sin(y)/2, x**2*cos(y)/2]])


def test_inv_iszerofunc():
    A = eye(4)
    A.col_swap(0, 1)
    for method in "GE", "LU":
        assert A.inv(method=method, iszerofunc=lambda x: x == 0) == \
            A.inv(method="ADJ")


def test_jacobian_metrics():
    rho, phi = symbols("rho,phi")
    X = Matrix([rho*cos(phi), rho*sin(phi)])
    Y = Matrix([rho, phi])
    J = X.jacobian(Y)
    assert J == X.jacobian(Y.T)
    assert J == (X.T).jacobian(Y)
    assert J == (X.T).jacobian(Y.T)
    g = J.T*eye(J.shape[0])*J
    g = g.applyfunc(trigsimp)
    assert g == Matrix([[1, 0], [0, rho**2]])


def test_jacobian2():
    rho, phi = symbols("rho,phi")
    X = Matrix([rho*cos(phi), rho*sin(phi), rho**2])
    Y = Matrix([rho, phi])
    J = Matrix([
        [cos(phi), -rho*sin(phi)],
        [sin(phi),  rho*cos(phi)],
        [   2*rho,             0],
    ])
    assert X.jacobian(Y) == J


def test_issue_4564():
    X = Matrix([exp(x + y + z), exp(x + y + z), exp(x + y + z)])
    Y = Matrix([x, y, z])
    for i in range(1, 3):
        for j in range(1, 3):
            X_slice = X[:i, :]
            Y_slice = Y[:j, :]
            J = X_slice.jacobian(Y_slice)
            assert J.rows == i
            assert J.cols == j
            for k in range(j):
                assert J[:, k] == X_slice


def test_nonvectorJacobian():
    X = Matrix([[exp(x + y + z), exp(x + y + z)],
                [exp(x + y + z), exp(x + y + z)]])
    raises(TypeError, lambda: X.jacobian(Matrix([x, y, z])))
    X = X[0, :]
    Y = Matrix([[x, y], [x, z]])
    raises(TypeError, lambda: X.jacobian(Y))
    raises(TypeError, lambda: X.jacobian(Matrix([ [x, y], [x, z] ])))


def test_vec():
    m = Matrix([[1, 3], [2, 4]])
    m_vec = m.vec()
    assert m_vec.cols == 1
    for i in range(4):
        assert m_vec[i] == i + 1


def test_vech():
    m = Matrix([[1, 2], [2, 3]])
    m_vech = m.vech()
    assert m_vech.cols == 1
    for i in range(3):
        assert m_vech[i] == i + 1
    m_vech = m.vech(diagonal=False)
    assert m_vech[0] == 2

    m = Matrix([[1, x*(x + y)], [y*x + x**2, 1]])
    m_vech = m.vech(diagonal=False)
    assert m_vech[0] == y*x + x**2

    m = Matrix([[1, x*(x + y)], [y*x, 1]])
    m_vech = m.vech(diagonal=False, check_symmetry=False)
    assert m_vech[0] == y*x

    raises(ShapeError, lambda: Matrix([[1, 3]]).vech())
    raises(ValueError, lambda: Matrix([[1, 3], [2, 4]]).vech())
    raises(ShapeError, lambda: Matrix([[1, 3]]).vech())
    raises(ValueError, lambda: Matrix([[1, 3], [2, 4]]).vech())


def test_diag():
    # mostly tested in testcommonmatrix.py
    assert diag([1, 2, 3]) == Matrix([1, 2, 3])
    m = [1, 2, [3]]
    raises(ValueError, lambda: diag(m))
    assert diag(m, strict=False) == Matrix([1, 2, 3])


def test_inv_block():
    a = Matrix([[1, 2], [2, 3]])
    b = Matrix([[3, x], [y, 3]])
    c = Matrix([[3, x, 3], [y, 3, z], [x, y, z]])
    A = diag(a, b, b)
    assert A.inv(try_block_diag=True) == diag(a.inv(), b.inv(), b.inv())
    A = diag(a, b, c)
    assert A.inv(try_block_diag=True) == diag(a.inv(), b.inv(), c.inv())
    A = diag(a, c, b)
    assert A.inv(try_block_diag=True) == diag(a.inv(), c.inv(), b.inv())
    A = diag(a, a, b, a, c, a)
    assert A.inv(try_block_diag=True) == diag(
        a.inv(), a.inv(), b.inv(), a.inv(), c.inv(), a.inv())
    assert A.inv(try_block_diag=True, method="ADJ") == diag(
        a.inv(method="ADJ"), a.inv(method="ADJ"), b.inv(method="ADJ"),
        a.inv(method="ADJ"), c.inv(method="ADJ"), a.inv(method="ADJ"))


def test_creation_args():
    """
    Check that matrix dimensions can be specified using any reasonable type
    (see issue 4614).
    """
    raises(ValueError, lambda: zeros(3, -1))
    raises(TypeError, lambda: zeros(1, 2, 3, 4))
    assert zeros(int(3)) == zeros(3)
    assert zeros(Integer(3)) == zeros(3)
    raises(ValueError, lambda: zeros(3.))
    assert eye(int(3)) == eye(3)
    assert eye(Integer(3)) == eye(3)
    raises(ValueError, lambda: eye(3.))
    assert ones(int(3), Integer(4)) == ones(3, 4)
    raises(TypeError, lambda: Matrix(5))
    raises(TypeError, lambda: Matrix(1, 2))
    raises(ValueError, lambda: Matrix([1, [2]]))


def test_diagonal_symmetrical():
    m = Matrix(2, 2, [0, 1, 1, 0])
    assert not m.is_diagonal()
    assert m.is_symmetric()
    assert m.is_symmetric(simplify=False)

    m = Matrix(2, 2, [1, 0, 0, 1])
    assert m.is_diagonal()

    m = diag(1, 2, 3)
    assert m.is_diagonal()
    assert m.is_symmetric()

    m = Matrix(3, 3, [1, 0, 0, 0, 2, 0, 0, 0, 3])
    assert m == diag(1, 2, 3)

    m = Matrix(2, 3, zeros(2, 3))
    assert not m.is_symmetric()
    assert m.is_diagonal()

    m = Matrix(((5, 0), (0, 6), (0, 0)))
    assert m.is_diagonal()

    m = Matrix(((5, 0, 0), (0, 6, 0)))
    assert m.is_diagonal()

    m = Matrix(3, 3, [1, x**2 + 2*x + 1, y, (x + 1)**2, 2, 0, y, 0, 3])
    assert m.is_symmetric()
    assert not m.is_symmetric(simplify=False)
    assert m.expand().is_symmetric(simplify=False)


def test_diagonalization():
    m = Matrix([[1, 2+I], [2-I, 3]])
    assert m.is_diagonalizable()

    m = Matrix(3, 2, [-3, 1, -3, 20, 3, 10])
    assert not m.is_diagonalizable()
    assert not m.is_symmetric()
    raises(NonSquareMatrixError, lambda: m.diagonalize())

    # diagonalizable
    m = diag(1, 2, 3)
    (P, D) = m.diagonalize()
    assert P == eye(3)
    assert D == m

    m = Matrix(2, 2, [0, 1, 1, 0])
    assert m.is_symmetric()
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D

    m = Matrix(2, 2, [1, 0, 0, 3])
    assert m.is_symmetric()
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D
    assert P == eye(2)
    assert D == m

    m = Matrix(2, 2, [1, 1, 0, 0])
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D

    m = Matrix(3, 3, [1, 2, 0, 0, 3, 0, 2, -4, 2])
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D
    for i in P:
        assert i.as_numer_denom()[1] == 1

    m = Matrix(2, 2, [1, 0, 0, 0])
    assert m.is_diagonal()
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D
    assert P == Matrix([[0, 1], [1, 0]])

    # diagonalizable, complex only
    m = Matrix(2, 2, [0, 1, -1, 0])
    assert not m.is_diagonalizable(True)
    raises(MatrixError, lambda: m.diagonalize(True))
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D

    # not diagonalizable
    m = Matrix(2, 2, [0, 1, 0, 0])
    assert not m.is_diagonalizable()
    raises(MatrixError, lambda: m.diagonalize())

    m = Matrix(3, 3, [-3, 1, -3, 20, 3, 10, 2, -2, 4])
    assert not m.is_diagonalizable()
    raises(MatrixError, lambda: m.diagonalize())

    # symbolic
    a, b, c, d = symbols('a b c d')
    m = Matrix(2, 2, [a, c, c, b])
    assert m.is_symmetric()
    assert m.is_diagonalizable()


def test_issue_15887():
    # Mutable matrix should not use cache
    a = MutableDenseMatrix([[0, 1], [1, 0]])
    assert a.is_diagonalizable() is True
    a[1, 0] = 0
    assert a.is_diagonalizable() is False

    a = MutableDenseMatrix([[0, 1], [1, 0]])
    a.diagonalize()
    a[1, 0] = 0
    raises(MatrixError, lambda: a.diagonalize())


def test_jordan_form():

    m = Matrix(3, 2, [-3, 1, -3, 20, 3, 10])
    raises(NonSquareMatrixError, lambda: m.jordan_form())

    # diagonalizable
    m = Matrix(3, 3, [7, -12, 6, 10, -19, 10, 12, -24, 13])
    Jmust = Matrix(3, 3, [-1, 0, 0, 0, 1, 0, 0, 0, 1])
    P, J = m.jordan_form()
    assert Jmust == J
    assert Jmust == m.diagonalize()[1]

    # m = Matrix(3, 3, [0, 6, 3, 1, 3, 1, -2, 2, 1])
    # m.jordan_form()  # very long
    # m.jordan_form()  #

    # diagonalizable, complex only

    # Jordan cells
    # complexity: one of eigenvalues is zero
    m = Matrix(3, 3, [0, 1, 0, -4, 4, 0, -2, 1, 2])
    # The blocks are ordered according to the value of their eigenvalues,
    # in order to make the matrix compatible with .diagonalize()
    Jmust = Matrix(3, 3, [2, 1, 0, 0, 2, 0, 0, 0, 2])
    P, J = m.jordan_form()
    assert Jmust == J

    # complexity: all of eigenvalues are equal
    m = Matrix(3, 3, [2, 6, -15, 1, 1, -5, 1, 2, -6])
    # Jmust = Matrix(3, 3, [-1, 0, 0, 0, -1, 1, 0, 0, -1])
    # same here see 1456ff
    Jmust = Matrix(3, 3, [-1, 1, 0, 0, -1, 0, 0, 0, -1])
    P, J = m.jordan_form()
    assert Jmust == J

    # complexity: two of eigenvalues are zero
    m = Matrix(3, 3, [4, -5, 2, 5, -7, 3, 6, -9, 4])
    Jmust = Matrix(3, 3, [0, 1, 0, 0, 0, 0, 0, 0, 1])
    P, J = m.jordan_form()
    assert Jmust == J

    m = Matrix(4, 4, [6, 5, -2, -3, -3, -1, 3, 3, 2, 1, -2, -3, -1, 1, 5, 5])
    Jmust = Matrix(4, 4, [2, 1, 0, 0,
                          0, 2, 0, 0,
              0, 0, 2, 1,
              0, 0, 0, 2]
              )
    P, J = m.jordan_form()
    assert Jmust == J

    m = Matrix(4, 4, [6, 2, -8, -6, -3, 2, 9, 6, 2, -2, -8, -6, -1, 0, 3, 4])
    # Jmust = Matrix(4, 4, [2, 0, 0, 0, 0, 2, 1, 0, 0, 0, 2, 0, 0, 0, 0, -2])
    # same here see 1456ff
    Jmust = Matrix(4, 4, [-2, 0, 0, 0,
                           0, 2, 1, 0,
                           0, 0, 2, 0,
                           0, 0, 0, 2])
    P, J = m.jordan_form()
    assert Jmust == J

    m = Matrix(4, 4, [5, 4, 2, 1, 0, 1, -1, -1, -1, -1, 3, 0, 1, 1, -1, 2])
    assert not m.is_diagonalizable()
    Jmust = Matrix(4, 4, [1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 4, 1, 0, 0, 0, 4])
    P, J = m.jordan_form()
    assert Jmust == J

    # checking for maximum precision to remain unchanged
    m = Matrix([[Float('1.0', precision=110), Float('2.0', precision=110)],
                [Float('3.14159265358979323846264338327', precision=110), Float('4.0', precision=110)]])
    P, J = m.jordan_form()
    for term in J.values():
        if isinstance(term, Float):
            assert term._prec == 110


def test_jordan_form_complex_issue_9274():
    A = Matrix([[ 2,  4,  1,  0],
                [-4,  2,  0,  1],
                [ 0,  0,  2,  4],
                [ 0,  0, -4,  2]])
    p = 2 - 4*I;
    q = 2 + 4*I;
    Jmust1 = Matrix([[p, 1, 0, 0],
                     [0, p, 0, 0],
                     [0, 0, q, 1],
                     [0, 0, 0, q]])
    Jmust2 = Matrix([[q, 1, 0, 0],
                     [0, q, 0, 0],
                     [0, 0, p, 1],
                     [0, 0, 0, p]])
    P, J = A.jordan_form()
    assert J == Jmust1 or J == Jmust2
    assert simplify(P*J*P.inv()) == A


def test_issue_10220():
    # two non-orthogonal Jordan blocks with eigenvalue 1
    M = Matrix([[1, 0, 0, 1],
                [0, 1, 1, 0],
                [0, 0, 1, 1],
                [0, 0, 0, 1]])
    P, J = M.jordan_form()
    assert P == Matrix([[0, 1, 0, 1],
                        [1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0]])
    assert J == Matrix([
                        [1, 1, 0, 0],
                        [0, 1, 1, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])


def test_jordan_form_issue_15858():
    A = Matrix([
        [1, 1, 1, 0],
        [-2, -1, 0, -1],
        [0, 0, -1, -1],
        [0, 0, 2, 1]])
    (P, J) = A.jordan_form()
    assert P.expand() == Matrix([
        [    -I,          -I/2,      I,           I/2],
        [-1 + I,             0, -1 - I,             0],
        [     0, -S(1)/2 - I/2,      0, -S(1)/2 + I/2],
        [     0,             1,      0,             1]])
    assert J == Matrix([
        [-I, 1, 0, 0],
        [0, -I, 0, 0],
        [0, 0, I, 1],
        [0, 0, 0, I]])


def test_Matrix_berkowitz_charpoly():
    UA, K_i, K_w = symbols('UA K_i K_w')

    A = Matrix([[-K_i - UA + K_i**2/(K_i + K_w),       K_i*K_w/(K_i + K_w)],
                [           K_i*K_w/(K_i + K_w), -K_w + K_w**2/(K_i + K_w)]])

    charpoly = A.charpoly(x)

    assert charpoly == \
        Poly(x**2 + (K_i*UA + K_w*UA + 2*K_i*K_w)/(K_i + K_w)*x +
        K_i*K_w*UA/(K_i + K_w), x, domain='ZZ(K_i,K_w,UA)')

    assert type(charpoly) is PurePoly

    A = Matrix([[1, 3], [2, 0]])
    assert A.charpoly() == A.charpoly(x) == PurePoly(x**2 - x - 6)

    A = Matrix([[1, 2], [x, 0]])
    p = A.charpoly(x)
    assert p.gen != x
    assert p.as_expr().subs(p.gen, x) == x**2 - 3*x


def test_exp_jordan_block():
    l = Symbol('lamda')

    m = Matrix.jordan_block(1, l)
    assert m._eval_matrix_exp_jblock() == Matrix([[exp(l)]])

    m = Matrix.jordan_block(3, l)
    assert m._eval_matrix_exp_jblock() == \
        Matrix([
            [exp(l), exp(l), exp(l)/2],
            [0, exp(l), exp(l)],
            [0, 0, exp(l)]])


def test_exp():
    m = Matrix([[3, 4], [0, -2]])
    m_exp = Matrix([[exp(3), -4*exp(-2)/5 + 4*exp(3)/5], [0, exp(-2)]])
    assert m.exp() == m_exp
    assert exp(m) == m_exp

    m = Matrix([[1, 0], [0, 1]])
    assert m.exp() == Matrix([[E, 0], [0, E]])
    assert exp(m) == Matrix([[E, 0], [0, E]])

    m = Matrix([[1, -1], [1, 1]])
    assert m.exp() == Matrix([[E*cos(1), -E*sin(1)], [E*sin(1), E*cos(1)]])


def test_log():
    l = Symbol('lamda')

    m = Matrix.jordan_block(1, l)
    assert m._eval_matrix_log_jblock() == Matrix([[log(l)]])

    m = Matrix.jordan_block(4, l)
    assert m._eval_matrix_log_jblock() == \
        Matrix(
            [
                [log(l), 1/l, -1/(2*l**2), 1/(3*l**3)],
                [0, log(l), 1/l, -1/(2*l**2)],
                [0, 0, log(l), 1/l],
                [0, 0, 0, log(l)]
            ]
        )

    m = Matrix(
        [[0, 0, 1],
        [0, 0, 0],
        [-1, 0, 0]]
    )
    raises(MatrixError, lambda: m.log())


def test_find_reasonable_pivot_naive_finds_guaranteed_nonzero1():
    # Test if matrices._find_reasonable_pivot_naive()
    # finds a guaranteed non-zero pivot when the
    # some of the candidate pivots are symbolic expressions.
    # Keyword argument: simpfunc=None indicates that no simplifications
    # should be performed during the search.
    x = Symbol('x')
    column = Matrix(3, 1, [x, cos(x)**2 + sin(x)**2, S.Half])
    pivot_offset, pivot_val, pivot_assumed_nonzero, simplified =\
        _find_reasonable_pivot_naive(column)
    assert pivot_val == S.Half


def test_find_reasonable_pivot_naive_finds_guaranteed_nonzero2():
    # Test if matrices._find_reasonable_pivot_naive()
    # finds a guaranteed non-zero pivot when the
    # some of the candidate pivots are symbolic expressions.
    # Keyword argument: simpfunc=_simplify indicates that the search
    # should attempt to simplify candidate pivots.
    x = Symbol('x')
    column = Matrix(3, 1,
                    [x,
                     cos(x)**2+sin(x)**2+x**2,
                     cos(x)**2+sin(x)**2])
    pivot_offset, pivot_val, pivot_assumed_nonzero, simplified =\
        _find_reasonable_pivot_naive(column, simpfunc=_simplify)
    assert pivot_val == 1


def test_find_reasonable_pivot_naive_simplifies():
    # Test if matrices._find_reasonable_pivot_naive()
    # simplifies candidate pivots, and reports
    # their offsets correctly.
    x = Symbol('x')
    column = Matrix(3, 1,
                    [x,
                     cos(x)**2+sin(x)**2+x,
                     cos(x)**2+sin(x)**2])
    pivot_offset, pivot_val, pivot_assumed_nonzero, simplified =\
        _find_reasonable_pivot_naive(column, simpfunc=_simplify)

    assert len(simplified) == 2
    assert simplified[0][0] == 1
    assert simplified[0][1] == 1+x
    assert simplified[1][0] == 2
    assert simplified[1][1] == 1


def test_errors():
    raises(ValueError, lambda: Matrix([[1, 2], [1]]))
    raises(IndexError, lambda: Matrix([[1, 2]])[1.2, 5])
    raises(IndexError, lambda: Matrix([[1, 2]])[1, 5.2])
    raises(ValueError, lambda: randMatrix(3, c=4, symmetric=True))
    raises(ValueError, lambda: Matrix([1, 2]).reshape(4, 6))
    raises(ShapeError,
        lambda: Matrix([[1, 2], [3, 4]]).copyin_matrix([1, 0], Matrix([1, 2])))
    raises(TypeError, lambda: Matrix([[1, 2], [3, 4]]).copyin_list([0,
           1], set()))
    raises(NonSquareMatrixError, lambda: Matrix([[1, 2, 3], [2, 3, 0]]).inv())
    raises(ShapeError,
        lambda: Matrix(1, 2, [1, 2]).row_join(Matrix([[1, 2], [3, 4]])))
    raises(
        ShapeError, lambda: Matrix([1, 2]).col_join(Matrix([[1, 2], [3, 4]])))
    raises(ShapeError, lambda: Matrix([1]).row_insert(1, Matrix([[1,
           2], [3, 4]])))
    raises(ShapeError, lambda: Matrix([1]).col_insert(1, Matrix([[1,
           2], [3, 4]])))
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).trace())
    raises(TypeError, lambda: Matrix([1]).applyfunc(1))
    raises(ValueError, lambda: Matrix([[1, 2], [3, 4]]).minor(4, 5))
    raises(ValueError, lambda: Matrix([[1, 2], [3, 4]]).minor_submatrix(4, 5))
    raises(TypeError, lambda: Matrix([1, 2, 3]).cross(1))
    raises(TypeError, lambda: Matrix([1, 2, 3]).dot(1))
    raises(ShapeError, lambda: Matrix([1, 2, 3]).dot(Matrix([1, 2])))
    raises(ShapeError, lambda: Matrix([1, 2]).dot([]))
    raises(TypeError, lambda: Matrix([1, 2]).dot('a'))
    raises(ShapeError, lambda: Matrix([1, 2]).dot([1, 2, 3]))
    raises(NonSquareMatrixError, lambda: Matrix([1, 2, 3]).exp())
    raises(ShapeError, lambda: Matrix([[1, 2], [3, 4]]).normalized())
    raises(ValueError, lambda: Matrix([1, 2]).inv(method='not a method'))
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).inverse_GE())
    raises(ValueError, lambda: Matrix([[1, 2], [1, 2]]).inverse_GE())
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).inverse_ADJ())
    raises(ValueError, lambda: Matrix([[1, 2], [1, 2]]).inverse_ADJ())
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).inverse_LU())
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).is_nilpotent())
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).det())
    raises(ValueError,
        lambda: Matrix([[1, 2], [3, 4]]).det(method='Not a real method'))
    raises(ValueError,
        lambda: Matrix([[1, 2, 3, 4], [5, 6, 7, 8],
        [9, 10, 11, 12], [13, 14, 15, 16]]).det(iszerofunc="Not function"))
    raises(ValueError,
        lambda: Matrix([[1, 2, 3, 4], [5, 6, 7, 8],
        [9, 10, 11, 12], [13, 14, 15, 16]]).det(iszerofunc=False))
    raises(ValueError,
        lambda: hessian(Matrix([[1, 2], [3, 4]]), Matrix([[1, 2], [2, 1]])))
    raises(ValueError, lambda: hessian(Matrix([[1, 2], [3, 4]]), []))
    raises(ValueError, lambda: hessian(Symbol('x')**2, 'a'))
    raises(IndexError, lambda: eye(3)[5, 2])
    raises(IndexError, lambda: eye(3)[2, 5])
    M = Matrix(((1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16)))
    raises(ValueError, lambda: M.det('method=LU_decomposition()'))
    V = Matrix([[10, 10, 10]])
    M = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(ValueError, lambda: M.row_insert(4.7, V))
    M = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(ValueError, lambda: M.col_insert(-4.2, V))


def test_len():
    assert len(Matrix()) == 0
    assert len(Matrix([[1, 2]])) == len(Matrix([[1], [2]])) == 2
    assert len(Matrix(0, 2, lambda i, j: 0)) == \
        len(Matrix(2, 0, lambda i, j: 0)) == 0
    assert len(Matrix([[0, 1, 2], [3, 4, 5]])) == 6
    assert Matrix([1]) == Matrix([[1]])
    assert not Matrix()
    assert Matrix() == Matrix([])


def test_integrate():
    A = Matrix(((1, 4, x), (y, 2, 4), (10, 5, x**2)))
    assert A.integrate(x) == \
        Matrix(((x, 4*x, x**2/2), (x*y, 2*x, 4*x), (10*x, 5*x, x**3/3)))
    assert A.integrate(y) == \
        Matrix(((y, 4*y, x*y), (y**2/2, 2*y, 4*y), (10*y, 5*y, y*x**2)))
    m = Matrix(2, 1, [x, y])
    assert m.integrate(x) == Matrix(2, 1, [x**2/2, y*x])


def test_diff():
    A = MutableDenseMatrix(((1, 4, x), (y, 2, 4), (10, 5, x**2 + 1)))
    assert isinstance(A.diff(x), type(A))
    assert A.diff(x) == MutableDenseMatrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))
    assert A.diff(y) == MutableDenseMatrix(((0, 0, 0), (1, 0, 0), (0, 0, 0)))

    assert diff(A, x) == MutableDenseMatrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))
    assert diff(A, y) == MutableDenseMatrix(((0, 0, 0), (1, 0, 0), (0, 0, 0)))

    A_imm = A.as_immutable()
    assert isinstance(A_imm.diff(x), type(A_imm))
    assert A_imm.diff(x) == ImmutableDenseMatrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))
    assert A_imm.diff(y) == ImmutableDenseMatrix(((0, 0, 0), (1, 0, 0), (0, 0, 0)))

    assert diff(A_imm, x) == ImmutableDenseMatrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))
    assert diff(A_imm, y) == ImmutableDenseMatrix(((0, 0, 0), (1, 0, 0), (0, 0, 0)))

    assert A.diff(x, evaluate=False) == ArrayDerivative(A, x, evaluate=False)
    assert diff(A, x, evaluate=False) == ArrayDerivative(A, x, evaluate=False)


def test_diff_by_matrix():

    # Derive matrix by matrix:

    A = MutableDenseMatrix([[x, y], [z, t]])
    assert A.diff(A) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])
    assert diff(A, A) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])

    A_imm = A.as_immutable()
    assert A_imm.diff(A_imm) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])
    assert diff(A_imm, A_imm) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])

    # Derive a constant matrix:
    assert A.diff(a) == MutableDenseMatrix([[0, 0], [0, 0]])

    B = ImmutableDenseMatrix([a, b])
    assert A.diff(B) == Array.zeros(2, 1, 2, 2)
    assert A.diff(A) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])

    # Test diff with tuples:

    dB = B.diff([[a, b]])
    assert dB.shape == (2, 2, 1)
    assert dB == Array([[[1], [0]], [[0], [1]]])

    f = Function("f")
    fxyz = f(x, y, z)
    assert fxyz.diff([[x, y, z]]) == Array([fxyz.diff(x), fxyz.diff(y), fxyz.diff(z)])
    assert fxyz.diff(([x, y, z], 2)) == Array([
        [fxyz.diff(x, 2), fxyz.diff(x, y), fxyz.diff(x, z)],
        [fxyz.diff(x, y), fxyz.diff(y, 2), fxyz.diff(y, z)],
        [fxyz.diff(x, z), fxyz.diff(z, y), fxyz.diff(z, 2)],
    ])

    expr = sin(x)*exp(y)
    assert expr.diff([[x, y]]) == Array([cos(x)*exp(y), sin(x)*exp(y)])
    assert expr.diff(y, ((x, y),)) == Array([cos(x)*exp(y), sin(x)*exp(y)])
    assert expr.diff(x, ((x, y),)) == Array([-sin(x)*exp(y), cos(x)*exp(y)])
    assert expr.diff(((y, x),), [[x, y]]) == Array([[cos(x)*exp(y), -sin(x)*exp(y)], [sin(x)*exp(y), cos(x)*exp(y)]])

    # Test different notations:

    assert fxyz.diff(x).diff(y).diff(x) == fxyz.diff(((x, y, z),), 3)[0, 1, 0]
    assert fxyz.diff(z).diff(y).diff(x) == fxyz.diff(((x, y, z),), 3)[2, 1, 0]
    assert fxyz.diff([[x, y, z]], ((z, y, x),)) == Array([[fxyz.diff(i).diff(j) for i in (x, y, z)] for j in (z, y, x)])

    # Test scalar derived by matrix remains matrix:
    res = x.diff(Matrix([[x, y]]))
    assert isinstance(res, ImmutableDenseMatrix)
    assert res == Matrix([[1, 0]])
    res = (x**3).diff(Matrix([[x, y]]))
    assert isinstance(res, ImmutableDenseMatrix)
    assert res == Matrix([[3*x**2, 0]])


def test_getattr():
    A = Matrix(((1, 4, x), (y, 2, 4), (10, 5, x**2 + 1)))
    raises(AttributeError, lambda: A.nonexistantattribute)
    assert getattr(A, 'diff')(x) == Matrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))


def test_hessenberg():
    A = Matrix([[3, 4, 1], [2, 4, 5], [0, 1, 2]])
    assert A.is_upper_hessenberg
    A = A.T
    assert A.is_lower_hessenberg
    A[0, -1] = 1
    assert A.is_lower_hessenberg is False

    A = Matrix([[3, 4, 1], [2, 4, 5], [3, 1, 2]])
    assert not A.is_upper_hessenberg

    A = zeros(5, 2)
    assert A.is_upper_hessenberg


def test_cholesky():
    raises(NonSquareMatrixError, lambda: Matrix((1, 2)).cholesky())
    raises(ValueError, lambda: Matrix(((1, 2), (3, 4))).cholesky())
    raises(ValueError, lambda: Matrix(((5 + I, 0), (0, 1))).cholesky())
    raises(ValueError, lambda: Matrix(((1, 5), (5, 1))).cholesky())
    raises(ValueError, lambda: Matrix(((1, 2), (3, 4))).cholesky(hermitian=False))
    assert Matrix(((5 + I, 0), (0, 1))).cholesky(hermitian=False) == Matrix([
        [sqrt(5 + I), 0], [0, 1]])
    A = Matrix(((1, 5), (5, 1)))
    L = A.cholesky(hermitian=False)
    assert L == Matrix([[1, 0], [5, 2*sqrt(6)*I]])
    assert L*L.T == A
    A = Matrix(((25, 15, -5), (15, 18, 0), (-5, 0, 11)))
    L = A.cholesky()
    assert L * L.T == A
    assert L.is_lower
    assert L == Matrix([[5, 0, 0], [3, 3, 0], [-1, 1, 3]])
    A = Matrix(((4, -2*I, 2 + 2*I), (2*I, 2, -1 + I), (2 - 2*I, -1 - I, 11)))
    assert A.cholesky().expand() == Matrix(((2, 0, 0), (I, 1, 0), (1 - I, 0, 3)))

    raises(NonSquareMatrixError, lambda: SparseMatrix((1, 2)).cholesky())
    raises(ValueError, lambda: SparseMatrix(((1, 2), (3, 4))).cholesky())
    raises(ValueError, lambda: SparseMatrix(((5 + I, 0), (0, 1))).cholesky())
    raises(ValueError, lambda: SparseMatrix(((1, 5), (5, 1))).cholesky())
    raises(ValueError, lambda: SparseMatrix(((1, 2), (3, 4))).cholesky(hermitian=False))
    assert SparseMatrix(((5 + I, 0), (0, 1))).cholesky(hermitian=False) == Matrix([
        [sqrt(5 + I), 0], [0, 1]])
    A = SparseMatrix(((1, 5), (5, 1)))
    L = A.cholesky(hermitian=False)
    assert L == Matrix([[1, 0], [5, 2*sqrt(6)*I]])
    assert L*L.T == A
    A = SparseMatrix(((25, 15, -5), (15, 18, 0), (-5, 0, 11)))
    L = A.cholesky()
    assert L * L.T == A
    assert L.is_lower
    assert L == Matrix([[5, 0, 0], [3, 3, 0], [-1, 1, 3]])
    A = SparseMatrix(((4, -2*I, 2 + 2*I), (2*I, 2, -1 + I), (2 - 2*I, -1 - I, 11)))
    assert A.cholesky() == Matrix(((2, 0, 0), (I, 1, 0), (1 - I, 0, 3)))


def test_matrix_norm():
    # Vector Tests
    # Test columns and symbols
    x = Symbol('x', real=True)
    v = Matrix([cos(x), sin(x)])
    assert trigsimp(v.norm(2)) == 1
    assert v.norm(10) == Pow(cos(x)**10 + sin(x)**10, Rational(1, 10))

    # Test Rows
    A = Matrix([[5, Rational(3, 2)]])
    assert A.norm() == Pow(25 + Rational(9, 4), S.Half)
    assert A.norm(oo) == max(A)
    assert A.norm(-oo) == min(A)

    # Matrix Tests
    # Intuitive test
    A = Matrix([[1, 1], [1, 1]])
    assert A.norm(2) == 2
    assert A.norm(-2) == 0
    assert A.norm('frobenius') == 2
    assert eye(10).norm(2) == eye(10).norm(-2) == 1
    assert A.norm(oo) == 2

    # Test with Symbols and more complex entries
    A = Matrix([[3, y, y], [x, S.Half, -pi]])
    assert (A.norm('fro')
           == sqrt(Rational(37, 4) + 2*abs(y)**2 + pi**2 + x**2))

    # Check non-square
    A = Matrix([[1, 2, -3], [4, 5, Rational(13, 2)]])
    assert A.norm(2) == sqrt(Rational(389, 8) + sqrt(78665)/8)
    assert A.norm(-2) is S.Zero
    assert A.norm('frobenius') == sqrt(389)/2

    # Test properties of matrix norms
    # https://en.wikipedia.org/wiki/Matrix_norm#Definition
    # Two matrices
    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[5, 5], [-2, 2]])
    C = Matrix([[0, -I], [I, 0]])
    D = Matrix([[1, 0], [0, -1]])
    L = [A, B, C, D]
    alpha = Symbol('alpha', real=True)

    for order in ['fro', 2, -2]:
        # Zero Check
        assert zeros(3).norm(order) is S.Zero
        # Check Triangle Inequality for all Pairs of Matrices
        for X in L:
            for Y in L:
                dif = (X.norm(order) + Y.norm(order) -
                    (X + Y).norm(order))
                assert (dif >= 0)
        # Scalar multiplication linearity
        for M in [A, B, C, D]:
            dif = simplify((alpha*M).norm(order) -
                    abs(alpha) * M.norm(order))
            assert dif == 0

    # Test Properties of Vector Norms
    # https://en.wikipedia.org/wiki/Vector_norm
    # Two column vectors
    a = Matrix([1, 1 - 1*I, -3])
    b = Matrix([S.Half, 1*I, 1])
    c = Matrix([-1, -1, -1])
    d = Matrix([3, 2, I])
    e = Matrix([Integer(1e2), Rational(1, 1e2), 1])
    L = [a, b, c, d, e]
    alpha = Symbol('alpha', real=True)

    for order in [1, 2, -1, -2, S.Infinity, S.NegativeInfinity, pi]:
        # Zero Check
        if order > 0:
            assert Matrix([0, 0, 0]).norm(order) is S.Zero
        # Triangle inequality on all pairs
        if order >= 1:  # Triangle InEq holds only for these norms
            for X in L:
                for Y in L:
                    dif = (X.norm(order) + Y.norm(order) -
                        (X + Y).norm(order))
                    assert simplify(dif >= 0) is S.true
        # Linear to scalar multiplication
        if order in [1, 2, -1, -2, S.Infinity, S.NegativeInfinity]:
            for X in L:
                dif = simplify((alpha*X).norm(order) -
                    (abs(alpha) * X.norm(order)))
                assert dif == 0

    # ord=1
    M = Matrix(3, 3, [1, 3, 0, -2, -1, 0, 3, 9, 6])
    assert M.norm(1) == 13


def test_condition_number():
    x = Symbol('x', real=True)
    A = eye(3)
    A[0, 0] = 10
    A[2, 2] = Rational(1, 10)
    assert A.condition_number() == 100

    A[1, 1] = x
    assert A.condition_number() == Max(10, Abs(x)) / Min(Rational(1, 10), Abs(x))

    M = Matrix([[cos(x), sin(x)], [-sin(x), cos(x)]])
    Mc = M.condition_number()
    assert all(Float(1.).epsilon_eq(Mc.subs(x, val).evalf()) for val in
        [Rational(1, 5), S.Half, Rational(1, 10), pi/2, pi, pi*Rational(7, 4) ])

    #issue 10782
    assert Matrix([]).condition_number() == 0


def test_equality():
    A = Matrix(((1, 2, 3), (4, 5, 6), (7, 8, 9)))
    B = Matrix(((9, 8, 7), (6, 5, 4), (3, 2, 1)))
    assert A == A[:, :]
    assert not A != A[:, :]
    assert not A == B
    assert A != B
    assert A != 10
    assert not A == 10

    # A SparseMatrix can be equal to a Matrix
    C = SparseMatrix(((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    D = Matrix(((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    assert C == D
    assert not C != D


def test_normalized():
    assert Matrix([3, 4]).normalized() == \
        Matrix([Rational(3, 5), Rational(4, 5)])

    # Zero vector trivial cases
    assert Matrix([0, 0, 0]).normalized() == Matrix([0, 0, 0])

    # Machine precision error truncation trivial cases
    m = Matrix([0,0,1.e-100])
    assert m.normalized(
    iszerofunc=lambda x: x.evalf(n=10, chop=True).is_zero
    ) == Matrix([0, 0, 0])


def test_print_nonzero():
    assert capture(lambda: eye(3).print_nonzero()) == \
        '[X  ]\n[ X ]\n[  X]\n'
    assert capture(lambda: eye(3).print_nonzero('.')) == \
        '[.  ]\n[ . ]\n[  .]\n'


def test_zeros_eye():
    assert Matrix.eye(3) == eye(3)
    assert Matrix.zeros(3) == zeros(3)
    assert ones(3, 4) == Matrix(3, 4, [1]*12)

    i = Matrix([[1, 0], [0, 1]])
    z = Matrix([[0, 0], [0, 0]])
    for cls in all_classes:
        m = cls.eye(2)
        assert i == m  # but m == i will fail if m is immutable
        assert i == eye(2, cls=cls)
        assert type(m) == cls
        m = cls.zeros(2)
        assert z == m
        assert z == zeros(2, cls=cls)
        assert type(m) == cls


def test_is_zero():
    assert Matrix().is_zero_matrix
    assert Matrix([[0, 0], [0, 0]]).is_zero_matrix
    assert zeros(3, 4).is_zero_matrix
    assert not eye(3).is_zero_matrix
    assert Matrix([[x, 0], [0, 0]]).is_zero_matrix == None
    assert SparseMatrix([[x, 0], [0, 0]]).is_zero_matrix == None
    assert ImmutableMatrix([[x, 0], [0, 0]]).is_zero_matrix == None
    assert ImmutableSparseMatrix([[x, 0], [0, 0]]).is_zero_matrix == None
    assert Matrix([[x, 1], [0, 0]]).is_zero_matrix == False
    a = Symbol('a', nonzero=True)
    assert Matrix([[a, 0], [0, 0]]).is_zero_matrix == False


def test_rotation_matrices():
    # This tests the rotation matrices by rotating about an axis and back.
    theta = pi/3
    r3_plus = rot_axis3(theta)
    r3_minus = rot_axis3(-theta)
    r2_plus = rot_axis2(theta)
    r2_minus = rot_axis2(-theta)
    r1_plus = rot_axis1(theta)
    r1_minus = rot_axis1(-theta)
    assert r3_minus*r3_plus*eye(3) == eye(3)
    assert r2_minus*r2_plus*eye(3) == eye(3)
    assert r1_minus*r1_plus*eye(3) == eye(3)

    # Check the correctness of the trace of the rotation matrix
    assert r1_plus.trace() == 1 + 2*cos(theta)
    assert r2_plus.trace() == 1 + 2*cos(theta)
    assert r3_plus.trace() == 1 + 2*cos(theta)

    # Check that a rotation with zero angle doesn't change anything.
    assert rot_axis1(0) == eye(3)
    assert rot_axis2(0) == eye(3)
    assert rot_axis3(0) == eye(3)

    # Check left-hand convention
    # see Issue #24529
    q1 = Quaternion.from_axis_angle([1, 0, 0], pi / 2)
    q2 = Quaternion.from_axis_angle([0, 1, 0], pi / 2)
    q3 = Quaternion.from_axis_angle([0, 0, 1], pi / 2)
    assert rot_axis1(- pi / 2) == q1.to_rotation_matrix()
    assert rot_axis2(- pi / 2) == q2.to_rotation_matrix()
    assert rot_axis3(- pi / 2) == q3.to_rotation_matrix()
    # Check right-hand convention
    assert rot_ccw_axis1(+ pi / 2) == q1.to_rotation_matrix()
    assert rot_ccw_axis2(+ pi / 2) == q2.to_rotation_matrix()
    assert rot_ccw_axis3(+ pi / 2) == q3.to_rotation_matrix()


def test_DeferredVector():
    assert str(DeferredVector("vector")[4]) == "vector[4]"
    assert sympify(DeferredVector("d")) == DeferredVector("d")
    raises(IndexError, lambda: DeferredVector("d")[-1])
    assert str(DeferredVector("d")) == "d"
    assert repr(DeferredVector("test")) == "DeferredVector('test')"


def test_DeferredVector_not_iterable():
    assert not iterable(DeferredVector('X'))


def test_DeferredVector_Matrix():
    raises(TypeError, lambda: Matrix(DeferredVector("V")))


def test_GramSchmidt():
    R = Rational
    m1 = Matrix(1, 2, [1, 2])
    m2 = Matrix(1, 2, [2, 3])
    assert GramSchmidt([m1, m2]) == \
        [Matrix(1, 2, [1, 2]), Matrix(1, 2, [R(2)/5, R(-1)/5])]
    assert GramSchmidt([m1.T, m2.T]) == \
        [Matrix(2, 1, [1, 2]), Matrix(2, 1, [R(2)/5, R(-1)/5])]
    # from wikipedia
    assert GramSchmidt([Matrix([3, 1]), Matrix([2, 2])], True) == [
        Matrix([3*sqrt(10)/10, sqrt(10)/10]),
        Matrix([-sqrt(10)/10, 3*sqrt(10)/10])]
    # https://github.com/sympy/sympy/issues/9488
    L = FiniteSet(Matrix([1]))
    assert GramSchmidt(L) == [Matrix([[1]])]


def test_casoratian():
    assert casoratian([1, 2, 3, 4], 1) == 0
    assert casoratian([1, 2, 3, 4], 1, zero=False) == 0


def test_zero_dimension_multiply():
    assert (Matrix()*zeros(0, 3)).shape == (0, 3)
    assert zeros(3, 0)*zeros(0, 3) == zeros(3, 3)
    assert zeros(0, 3)*zeros(3, 0) == Matrix()


def test_slice_issue_2884():
    m = Matrix(2, 2, range(4))
    assert m[1, :] == Matrix([[2, 3]])
    assert m[-1, :] == Matrix([[2, 3]])
    assert m[:, 1] == Matrix([[1, 3]]).T
    assert m[:, -1] == Matrix([[1, 3]]).T
    raises(IndexError, lambda: m[2, :])
    raises(IndexError, lambda: m[2, 2])


def test_slice_issue_3401():
    assert zeros(0, 3)[:, -1].shape == (0, 1)
    assert zeros(3, 0)[0, :] == Matrix(1, 0, [])


def test_copyin():
    s = zeros(3, 3)
    s[3] = 1
    assert s[:, 0] == Matrix([0, 1, 0])
    assert s[3] == 1
    assert s[3: 4] == [1]
    s[1, 1] = 42
    assert s[1, 1] == 42
    assert s[1, 1:] == Matrix([[42, 0]])
    s[1, 1:] = Matrix([[5, 6]])
    assert s[1, :] == Matrix([[1, 5, 6]])
    s[1, 1:] = [[42, 43]]
    assert s[1, :] == Matrix([[1, 42, 43]])
    s[0, 0] = 17
    assert s[:, :1] == Matrix([17, 1, 0])
    s[0, 0] = [1, 1, 1]
    assert s[:, 0] == Matrix([1, 1, 1])
    s[0, 0] = Matrix([1, 1, 1])
    assert s[:, 0] == Matrix([1, 1, 1])
    s[0, 0] = SparseMatrix([1, 1, 1])
    assert s[:, 0] == Matrix([1, 1, 1])


def test_invertible_check():
    # sometimes a singular matrix will have a pivot vector shorter than
    # the number of rows in a matrix...
    assert Matrix([[1, 2], [1, 2]]).rref() == (Matrix([[1, 2], [0, 0]]), (0,))
    raises(ValueError, lambda: Matrix([[1, 2], [1, 2]]).inv())
    m = Matrix([
        [-1, -1,  0],
        [ x,  1,  1],
        [ 1,  x, -1],
    ])
    assert len(m.rref()[1]) != m.rows
    # in addition, unless simplify=True in the call to rref, the identity
    # matrix will be returned even though m is not invertible
    assert m.rref()[0] != eye(3)
    assert m.rref(simplify=signsimp)[0] != eye(3)
    raises(ValueError, lambda: m.inv(method="ADJ"))
    raises(ValueError, lambda: m.inv(method="GE"))
    raises(ValueError, lambda: m.inv(method="LU"))


def test_issue_3959():
    x, y = symbols('x, y')
    e = x*y
    assert e.subs(x, Matrix([3, 5, 3])) == Matrix([3, 5, 3])*y


def test_issue_5964():
    assert str(Matrix([[1, 2], [3, 4]])) == 'Matrix([[1, 2], [3, 4]])'


def test_issue_7604():
    x, y = symbols("x y")
    assert sstr(Matrix([[x, 2*y], [y**2, x + 3]])) == \
        'Matrix([\n[   x,   2*y],\n[y**2, x + 3]])'


def test_is_Identity():
    assert eye(3).is_Identity
    assert eye(3).as_immutable().is_Identity
    assert not zeros(3).is_Identity
    assert not ones(3).is_Identity
    # issue 6242
    assert not Matrix([[1, 0, 0]]).is_Identity
    # issue 8854
    assert SparseMatrix(3,3, {(0,0):1, (1,1):1, (2,2):1}).is_Identity
    assert not SparseMatrix(2,3, range(6)).is_Identity
    assert not SparseMatrix(3,3, {(0,0):1, (1,1):1}).is_Identity
    assert not SparseMatrix(3,3, {(0,0):1, (1,1):1, (2,2):1, (0,1):2, (0,2):3}).is_Identity


def test_dot():
    assert ones(1, 3).dot(ones(3, 1)) == 3
    assert ones(1, 3).dot([1, 1, 1]) == 3
    assert Matrix([1, 2, 3]).dot(Matrix([1, 2, 3])) == 14
    assert Matrix([1, 2, 3*I]).dot(Matrix([I, 2, 3*I])) == -5 + I
    assert Matrix([1, 2, 3*I]).dot(Matrix([I, 2, 3*I]), hermitian=False) == -5 + I
    assert Matrix([1, 2, 3*I]).dot(Matrix([I, 2, 3*I]), hermitian=True) == 13 + I
    assert Matrix([1, 2, 3*I]).dot(Matrix([I, 2, 3*I]), hermitian=True, conjugate_convention="physics") == 13 - I
    assert Matrix([1, 2, 3*I]).dot(Matrix([4, 5*I, 6]), hermitian=True, conjugate_convention="right") == 4 + 8*I
    assert Matrix([1, 2, 3*I]).dot(Matrix([4, 5*I, 6]), hermitian=True, conjugate_convention="left") == 4 - 8*I
    assert Matrix([I, 2*I]).dot(Matrix([I, 2*I]), hermitian=False, conjugate_convention="left") == -5
    assert Matrix([I, 2*I]).dot(Matrix([I, 2*I]), conjugate_convention="left") == 5
    raises(ValueError, lambda: Matrix([1, 2]).dot(Matrix([3, 4]), hermitian=True, conjugate_convention="test"))


def test_dual():
    B_x, B_y, B_z, E_x, E_y, E_z = symbols(
        'B_x B_y B_z E_x E_y E_z', real=True)
    F = Matrix((
        (   0,  E_x,  E_y,  E_z),
        (-E_x,    0,  B_z, -B_y),
        (-E_y, -B_z,    0,  B_x),
        (-E_z,  B_y, -B_x,    0)
    ))
    Fd = Matrix((
        (  0, -B_x, -B_y, -B_z),
        (B_x,    0,  E_z, -E_y),
        (B_y, -E_z,    0,  E_x),
        (B_z,  E_y, -E_x,    0)
    ))
    assert F.dual().equals(Fd)
    assert eye(3).dual().equals(zeros(3))
    assert F.dual().dual().equals(-F)


def test_anti_symmetric():
    assert Matrix([1, 2]).is_anti_symmetric() is False
    m = Matrix(3, 3, [0, x**2 + 2*x + 1, y, -(x + 1)**2, 0, x*y, -y, -x*y, 0])
    assert m.is_anti_symmetric() is True
    assert m.is_anti_symmetric(simplify=False) is False
    assert m.is_anti_symmetric(simplify=lambda x: x) is False

    # tweak to fail
    m[2, 1] = -m[2, 1]
    assert m.is_anti_symmetric() is False
    # untweak
    m[2, 1] = -m[2, 1]

    m = m.expand()
    assert m.is_anti_symmetric(simplify=False) is True
    m[0, 0] = 1
    assert m.is_anti_symmetric() is False


def test_normalize_sort_diogonalization():
    A = Matrix(((1, 2), (2, 1)))
    P, Q = A.diagonalize(normalize=True)
    assert P*P.T == P.T*P == eye(P.cols)
    P, Q = A.diagonalize(normalize=True, sort=True)
    assert P*P.T == P.T*P == eye(P.cols)
    assert P*Q*P.inv() == A


def test_issue_5321():
    raises(ValueError, lambda: Matrix([[1, 2, 3], Matrix(0, 1, [])]))


def test_issue_5320():
    assert Matrix.hstack(eye(2), 2*eye(2)) == Matrix([
        [1, 0, 2, 0],
        [0, 1, 0, 2]
    ])
    assert Matrix.vstack(eye(2), 2*eye(2)) == Matrix([
        [1, 0],
        [0, 1],
        [2, 0],
        [0, 2]
    ])
    cls = SparseMatrix
    assert cls.hstack(cls(eye(2)), cls(2*eye(2))) == Matrix([
        [1, 0, 2, 0],
        [0, 1, 0, 2]
    ])


def test_issue_11944():
    A = Matrix([[1]])
    AIm = sympify(A)
    assert Matrix.hstack(AIm, A) == Matrix([[1, 1]])
    assert Matrix.vstack(AIm, A) == Matrix([[1], [1]])


def test_cross():
    a = [1, 2, 3]
    b = [3, 4, 5]
    col = Matrix([-2, 4, -2])
    row = col.T

    def test(M, ans):
        assert ans == M
        assert type(M) == cls
    for cls in all_classes:
        A = cls(a)
        B = cls(b)
        test(A.cross(B), col)
        test(A.cross(B.T), col)
        test(A.T.cross(B.T), row)
        test(A.T.cross(B), row)
    raises(ShapeError, lambda:
        Matrix(1, 2, [1, 1]).cross(Matrix(1, 2, [1, 1])))


def test_hat_vee():
    v1 = Matrix([x, y, z])
    v2 = Matrix([a, b, c])
    assert v1.hat() * v2 == v1.cross(v2)
    assert v1.hat().is_anti_symmetric()
    assert v1.hat().vee() == v1


def test_hash():
    for cls in immutable_classes:
        s = {cls.eye(1), cls.eye(1)}
        assert len(s) == 1 and s.pop() == cls.eye(1)
    # issue 3979
    for cls in mutable_classes:
        assert not isinstance(cls.eye(1), Hashable)


def test_adjoint():
    dat = [[0, I], [1, 0]]
    ans = Matrix([[0, 1], [-I, 0]])
    for cls in all_classes:
        assert ans == cls(dat).adjoint()


def test_atoms():
    m = Matrix([[1, 2], [x, 1 - 1/x]])
    assert m.atoms() == {S.One,S(2),S.NegativeOne, x}
    assert m.atoms(Symbol) == {x}


def test_pinv():
    # Pseudoinverse of an invertible matrix is the inverse.
    A1 = Matrix([[a, b], [c, d]])
    assert simplify(A1.pinv(method="RD")) == simplify(A1.inv())

    # Test the four properties of the pseudoinverse for various matrices.
    As = [Matrix([[13, 104], [2212, 3], [-3, 5]]),
          Matrix([[1, 7, 9], [11, 17, 19]]),
          Matrix([a, b])]

    for A in As:
        A_pinv = A.pinv(method="RD")
        AAp = A * A_pinv
        ApA = A_pinv * A
        assert simplify(AAp * A) == A
        assert simplify(ApA * A_pinv) == A_pinv
        assert AAp.H == AAp
        assert ApA.H == ApA

    # XXX Pinv with diagonalization makes expression too complicated.
    for A in As:
        A_pinv = simplify(A.pinv(method="ED"))
        AAp = A * A_pinv
        ApA = A_pinv * A
        assert simplify(AAp * A) == A
        assert simplify(ApA * A_pinv) == A_pinv
        assert AAp.H == AAp
        assert ApA.H == ApA

    # XXX Computing pinv using diagonalization makes an expression that
    # is too complicated to simplify.
    # A1 = Matrix([[a, b], [c, d]])
    # assert simplify(A1.pinv(method="ED")) == simplify(A1.inv())
    # so this is tested numerically at a fixed random point

    from sympy.core.numbers import comp
    q = A1.pinv(method="ED")
    w = A1.inv()
    reps = {a: -73633, b: 11362, c: 55486, d: 62570}
    assert all(
        comp(i.n(), j.n())
        for i, j in zip(q.subs(reps), w.subs(reps))
        )


@slow
def test_pinv_rank_deficient_when_diagonalization_fails():
    # Test the four properties of the pseudoinverse for matrices when
    # diagonalization of A.H*A fails.
    As = [
        Matrix([
            [61, 89, 55, 20, 71, 0],
            [62, 96, 85, 85, 16, 0],
            [69, 56, 17,  4, 54, 0],
            [10, 54, 91, 41, 71, 0],
            [ 7, 30, 10, 48, 90, 0],
            [0, 0, 0, 0, 0, 0]])
    ]
    for A in As:
        A_pinv = A.pinv(method="ED")
        AAp = A * A_pinv
        ApA = A_pinv * A
        assert AAp.H == AAp

        # Here ApA.H and ApA are equivalent expressions but they are very
        # complicated expressions involving RootOfs. Using simplify would be
        # too slow and so would evalf so we substitute approximate values for
        # the RootOfs and then evalf which is less accurate but good enough to
        # confirm that these two matrices are equivalent.
        #
        # assert ApA.H == ApA  # <--- would fail (structural equality)
        # assert simplify(ApA.H - ApA).is_zero_matrix  # <--- too slow
        # (ApA.H - ApA).evalf()  # <--- too slow

        def allclose(M1, M2):
            rootofs = M1.atoms(RootOf)
            rootofs_approx = {r: r.evalf() for r in rootofs}
            diff_approx = (M1 - M2).xreplace(rootofs_approx).evalf()
            return all(abs(e) < 1e-10 for e in diff_approx)

        assert allclose(ApA.H, ApA)


def test_issue_7201():
    assert ones(0, 1) + ones(0, 1) == Matrix(0, 1, [])
    assert ones(1, 0) + ones(1, 0) == Matrix(1, 0, [])


def test_free_symbols():
    for M in ImmutableMatrix, ImmutableSparseMatrix, Matrix, SparseMatrix:
        assert M([[x], [0]]).free_symbols == {x}


def test_from_ndarray():
    """See issue 7465."""
    try:
        from numpy import array
    except ImportError:
        skip('NumPy must be available to test creating matrices from ndarrays')

    assert Matrix(array([1, 2, 3])) == Matrix([1, 2, 3])
    assert Matrix(array([[1, 2, 3]])) == Matrix([[1, 2, 3]])
    assert Matrix(array([[1, 2, 3], [4, 5, 6]])) == \
        Matrix([[1, 2, 3], [4, 5, 6]])
    assert Matrix(array([x, y, z])) == Matrix([x, y, z])
    raises(NotImplementedError,
        lambda: Matrix(array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])))
    assert Matrix([array([1, 2]), array([3, 4])]) == Matrix([[1, 2], [3, 4]])
    assert Matrix([array([1, 2]), [3, 4]]) == Matrix([[1, 2], [3, 4]])
    assert Matrix([array([]), array([])]) == Matrix([])


def test_17522_numpy():
    from sympy.matrices.common import _matrixify
    try:
        from numpy import array, matrix
    except ImportError:
        skip('NumPy must be available to test indexing matrixified NumPy ndarrays and matrices')

    m = _matrixify(array([[1, 2], [3, 4]]))
    assert m[3] == 4
    assert list(m) == [1, 2, 3, 4]

    with ignore_warnings(PendingDeprecationWarning):
        m = _matrixify(matrix([[1, 2], [3, 4]]))
    assert m[3] == 4
    assert list(m) == [1, 2, 3, 4]


def test_17522_mpmath():
    from sympy.matrices.common import _matrixify
    try:
        from mpmath import matrix
    except ImportError:
        skip('mpmath must be available to test indexing matrixified mpmath matrices')

    m = _matrixify(matrix([[1, 2], [3, 4]]))
    assert m[3] == 4.0
    assert list(m) == [1.0, 2.0, 3.0, 4.0]


def test_17522_scipy():
    from sympy.matrices.common import _matrixify
    try:
        from scipy.sparse import csr_matrix
    except ImportError:
        skip('SciPy must be available to test indexing matrixified SciPy sparse matrices')

    m = _matrixify(csr_matrix([[1, 2], [3, 4]]))
    assert m[3] == 4
    assert list(m) == [1, 2, 3, 4]


def test_hermitian():
    a = Matrix([[1, I], [-I, 1]])
    assert a.is_hermitian
    a[0, 0] = 2*I
    assert a.is_hermitian is False
    a[0, 0] = x
    assert a.is_hermitian is None
    a[0, 1] = a[1, 0]*I
    assert a.is_hermitian is False


def test_issue_9457_9467_9876():
    # for row_del(index)
    M = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    M.row_del(1)
    assert M == Matrix([[1, 2, 3], [3, 4, 5]])
    N = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    N.row_del(-2)
    assert N == Matrix([[1, 2, 3], [3, 4, 5]])
    O = Matrix([[1, 2, 3], [5, 6, 7], [9, 10, 11]])
    O.row_del(-1)
    assert O == Matrix([[1, 2, 3], [5, 6, 7]])
    P = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(IndexError, lambda: P.row_del(10))
    Q = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(IndexError, lambda: Q.row_del(-10))

    # for col_del(index)
    M = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    M.col_del(1)
    assert M == Matrix([[1, 3], [2, 4], [3, 5]])
    N = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    N.col_del(-2)
    assert N == Matrix([[1, 3], [2, 4], [3, 5]])
    P = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(IndexError, lambda: P.col_del(10))
    Q = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(IndexError, lambda: Q.col_del(-10))


def test_issue_9422():
    x, y = symbols('x y', commutative=False)
    a, b = symbols('a b')
    M = eye(2)
    M1 = Matrix(2, 2, [x, y, y, z])
    assert y*x*M != x*y*M
    assert b*a*M == a*b*M
    assert x*M1 != M1*x
    assert a*M1 == M1*a
    assert y*x*M == Matrix([[y*x, 0], [0, y*x]])


def test_issue_10770():
    M = Matrix([])
    a = ['col_insert', 'row_join'], Matrix([9, 6, 3])
    b = ['row_insert', 'col_join'], a[1].T
    c = ['row_insert', 'col_insert'], Matrix([[1, 2], [3, 4]])
    for ops, m in (a, b, c):
        for op in ops:
            f = getattr(M, op)
            new = f(m) if 'join' in op else f(42, m)
            assert new == m and id(new) != id(m)


def test_issue_10658():
    A = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert A.extract([0, 1, 2], [True, True, False]) == \
        Matrix([[1, 2], [4, 5], [7, 8]])
    assert A.extract([0, 1, 2], [True, False, False]) == Matrix([[1], [4], [7]])
    assert A.extract([True, False, False], [0, 1, 2]) == Matrix([[1, 2, 3]])
    assert A.extract([True, False, True], [0, 1, 2]) == \
        Matrix([[1, 2, 3], [7, 8, 9]])
    assert A.extract([0, 1, 2], [False, False, False]) == Matrix(3, 0, [])
    assert A.extract([False, False, False], [0, 1, 2]) == Matrix(0, 3, [])
    assert A.extract([True, False, True], [False, True, False]) == \
        Matrix([[2], [8]])


def test_opportunistic_simplification():
    # this test relates to issue #10718, #9480, #11434

    # issue #9480
    m = Matrix([[-5 + 5*sqrt(2), -5], [-5*sqrt(2)/2 + 5, -5*sqrt(2)/2]])
    assert m.rank() == 1

    # issue #10781
    m = Matrix([[3+3*sqrt(3)*I, -9],[4,-3+3*sqrt(3)*I]])
    assert simplify(m.rref()[0] - Matrix([[1, -9/(3 + 3*sqrt(3)*I)], [0, 0]])) == zeros(2, 2)

    # issue #11434
    ax,ay,bx,by,cx,cy,dx,dy,ex,ey,t0,t1 = symbols('a_x a_y b_x b_y c_x c_y d_x d_y e_x e_y t_0 t_1')
    m = Matrix([[ax,ay,ax*t0,ay*t0,0],[bx,by,bx*t0,by*t0,0],[cx,cy,cx*t0,cy*t0,1],[dx,dy,dx*t0,dy*t0,1],[ex,ey,2*ex*t1-ex*t0,2*ey*t1-ey*t0,0]])
    assert m.rank() == 4


def test_partial_pivoting():
    # example from https://en.wikipedia.org/wiki/Pivot_element
    # partial pivoting with back substitution gives a perfect result
    # naive pivoting give an error ~1e-13, so anything better than
    # 1e-15 is good
    mm=Matrix([[0.003, 59.14, 59.17], [5.291, -6.13, 46.78]])
    assert (mm.rref()[0] - Matrix([[1.0,   0, 10.0],
                                   [  0, 1.0,  1.0]])).norm() < 1e-15

    # issue #11549
    m_mixed = Matrix([[6e-17, 1.0, 4],
                      [ -1.0,   0, 8],
                      [    0,   0, 1]])
    m_float = Matrix([[6e-17,  1.0, 4.],
                      [ -1.0,   0., 8.],
                      [   0.,   0., 1.]])
    m_inv = Matrix([[  0,    -1.0,  8.0],
                    [1.0, 6.0e-17, -4.0],
                    [  0,       0,    1]])
    # this example is numerically unstable and involves a matrix with a norm >= 8,
    # this comparing the difference of the results with 1e-15 is numerically sound.
    assert (m_mixed.inv() - m_inv).norm() < 1e-15
    assert (m_float.inv() - m_inv).norm() < 1e-15


def test_iszero_substitution():
    """ When doing numerical computations, all elements that pass
    the iszerofunc test should be set to numerically zero if they
    aren't already. """

    # Matrix from issue #9060
    m = Matrix([[0.9, -0.1, -0.2, 0],[-0.8, 0.9, -0.4, 0],[-0.1, -0.8, 0.6, 0]])
    m_rref = m.rref(iszerofunc=lambda x: abs(x)<6e-15)[0]
    m_correct = Matrix([[1.0,   0, -0.301369863013699, 0],[  0, 1.0, -0.712328767123288, 0],[  0,   0,                  0, 0]])
    m_diff = m_rref - m_correct
    assert m_diff.norm() < 1e-15
    # if a zero-substitution wasn't made, this entry will be -1.11022302462516e-16
    assert m_rref[2,2] == 0


def test_issue_11238():
    from sympy.geometry.point import Point
    xx = 8*tan(pi*Rational(13, 45))/(tan(pi*Rational(13, 45)) + sqrt(3))
    yy = (-8*sqrt(3)*tan(pi*Rational(13, 45))**2 + 24*tan(pi*Rational(13, 45)))/(-3 + tan(pi*Rational(13, 45))**2)
    p1 = Point(0, 0)
    p2 = Point(1, -sqrt(3))
    p0 = Point(xx,yy)
    m1 = Matrix([p1 - simplify(p0), p2 - simplify(p0)])
    m2 = Matrix([p1 - p0, p2 - p0])
    m3 = Matrix([simplify(p1 - p0), simplify(p2 - p0)])

    # This system has expressions which are zero and
    # cannot be easily proved to be such, so without
    # numerical testing, these assertions will fail.
    Z = lambda x: abs(x.n()) < 1e-20
    assert m1.rank(simplify=True, iszerofunc=Z) == 1
    assert m2.rank(simplify=True, iszerofunc=Z) == 1
    assert m3.rank(simplify=True, iszerofunc=Z) == 1


def test_as_real_imag():
    m1 = Matrix(2,2,[1,2,3,4])
    m2 = m1*S.ImaginaryUnit
    m3 = m1 + m2

    for kls in all_classes:
        a,b = kls(m3).as_real_imag()
        assert list(a) == list(m1)
        assert list(b) == list(m1)


def test_deprecated():
    # Maintain tests for deprecated functions.  We must capture
    # the deprecation warnings.  When the deprecated functionality is
    # removed, the corresponding tests should be removed.

    m = Matrix(3, 3, [0, 1, 0, -4, 4, 0, -2, 1, 2])
    P, Jcells = m.jordan_cells()
    assert Jcells[1] == Matrix(1, 1, [2])
    assert Jcells[0] == Matrix(2, 2, [2, 1, 0, 2])


def test_issue_14489():
    from sympy.core.mod import Mod
    A = Matrix([-1, 1, 2])
    B = Matrix([10, 20, -15])

    assert Mod(A, 3) == Matrix([2, 1, 2])
    assert Mod(B, 4) == Matrix([2, 0, 1])


def test_issue_14943():
    # Test that __array__ accepts the optional dtype argument
    try:
        from numpy import array
    except ImportError:
        skip('NumPy must be available to test creating matrices from ndarrays')

    M = Matrix([[1,2], [3,4]])
    assert array(M, dtype=float).dtype.name == 'float64'


def test_case_6913():
    m = MatrixSymbol('m', 1, 1)
    a = Symbol("a")
    a = m[0, 0]>0
    assert str(a) == 'm[0, 0] > 0'


def test_issue_11948():
    A = MatrixSymbol('A', 3, 3)
    a = Wild('a')
    assert A.match(a) == {a: A}


def test_gramschmidt_conjugate_dot():
    vecs = [Matrix([1, I]), Matrix([1, -I])]
    assert Matrix.orthogonalize(*vecs) == \
        [Matrix([[1], [I]]), Matrix([[1], [-I]])]

    vecs = [Matrix([1, I, 0]), Matrix([I, 0, -I])]
    assert Matrix.orthogonalize(*vecs) == \
        [Matrix([[1], [I], [0]]), Matrix([[I/2], [S(1)/2], [-I]])]

    mat = Matrix([[1, I], [1, -I]])
    Q, R = mat.QRdecomposition()
    assert Q * Q.H == Matrix.eye(2)


def test_issue_8207():
    a = Matrix(MatrixSymbol('a', 3, 1))
    b = Matrix(MatrixSymbol('b', 3, 1))
    c = a.dot(b)
    d = diff(c, a[0, 0])
    e = diff(d, a[0, 0])
    assert d == b[0, 0]
    assert e == 0


def test_func():
    from sympy.simplify.simplify import nthroot

    A = Matrix([[1, 2],[0, 3]])
    assert A.analytic_func(sin(x*t), x) == Matrix([[sin(t), sin(3*t) - sin(t)], [0, sin(3*t)]])

    A = Matrix([[2, 1],[1, 2]])
    assert (pi * A / 6).analytic_func(cos(x), x) == Matrix([[sqrt(3)/4, -sqrt(3)/4], [-sqrt(3)/4, sqrt(3)/4]])


    raises(ValueError, lambda : zeros(5).analytic_func(log(x), x))
    raises(ValueError, lambda : (A*x).analytic_func(log(x), x))

    A = Matrix([[0, -1, -2, 3], [0, -1, -2, 3], [0, 1, 0, -1], [0, 0, -1, 1]])
    assert A.analytic_func(exp(x), x) == A.exp()
    raises(ValueError, lambda : A.analytic_func(sqrt(x), x))

    A = Matrix([[41, 12],[12, 34]])
    assert simplify(A.analytic_func(sqrt(x), x)**2) == A

    A = Matrix([[3, -12, 4], [-1, 0, -2], [-1, 5, -1]])
    assert simplify(A.analytic_func(nthroot(x, 3), x)**3) == A

    A = Matrix([[2, 0, 0, 0], [1, 2, 0, 0], [0, 1, 3, 0], [0, 0, 1, 3]])
    assert A.analytic_func(exp(x), x) == A.exp()

    A = Matrix([[0, 2, 1, 6], [0, 0, 1, 2], [0, 0, 0, 3], [0, 0, 0, 0]])
    assert A.analytic_func(exp(x*t), x) == expand(simplify((A*t).exp()))


@skip_under_pyodide("Cannot create threads under pyodide.")
def test_issue_19809():

    def f():
        assert _dotprodsimp_state.state == None
        m = Matrix([[1]])
        m = m * m
        return True

    with dotprodsimp(True):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(f)
            assert future.result()


def test_issue_23276():
    M = Matrix([x, y])
    assert integrate(M, (x, 0, 1), (y, 0, 1)) == Matrix([
        [S.Half],
        [S.Half]])
