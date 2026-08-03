"""Designed edge-focused values shared by reference generation and tests."""

REAL_GRID = sorted(set(
    [float("-inf"), -1e10, -1e5, -1e3, -100.0, -20.0, -10.0, -5.0, -2.0, -1.0,
     -0.5, -0.1, -1e-10, 0.0, 1e-300, 1e-100, 1e-15, 1e-10, 1e-6,
     0.001, 0.01, 0.1, 0.25, 0.49, 0.5, 0.51, 0.75, 0.9, 1.0,
     1.000000001, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 1e3, 1e5, 1e10,
     float("inf")]
    + [edge + offset for edge in range(-10, 21) for offset in (-0.500000001, -0.5, -0.499999999, -1e-9, 0.0, 1e-9, 0.499999999, 0.5, 0.500000001)]
))
REAL_GRID.append(float("nan"))
PROBABILITY_GRID = sorted(set(
    [0.0, 5e-324, 1e-300, 1e-200, 1e-100, 1e-50, 1e-20, 1e-15, 1e-12,
     1e-9, 1e-6, 1e-3, 0.01, 0.05, 0.1, 0.25, 0.49, 0.5, 0.51, 0.75,
     0.9, 0.95, 0.99, 1 - 1e-3, 1 - 1e-6, 1 - 1e-9, 1 - 1e-12,
     1 - 1e-15, 1.0]
    + [index / 64 for index in range(1, 64)]
))
PROBABILITY_GRID.extend([-0.1, 1.1, float("inf"), float("nan")])

REFERENCE_VALUES = {
    "x": REAL_GRID,
    "q": REAL_GRID,
    "p": PROBABILITY_GRID,
    "mean": [float("-inf"), -1e10, -2.0, 0.0, 1.5, 1e10, float("inf"), float("nan")],
    "location": [float("-inf"), -1e10, -2.0, 0.0, 1.5, 1e10, float("inf"), float("nan")],
    "sd": [-1.0, 0.0, 1e-10, 0.1, 1.0, 3.0, 1e10, float("inf"), float("nan")],
    "shape": [-1.0, 0.0, 1e-10, 0.1, 0.5, 2.0, 10.0, 1e10, float("inf"), float("nan")],
    "shape1": [-1.0, 0.0, 1e-10, 0.2, 0.5, 2.0, 8.0, 1e10, float("inf"), float("nan")],
    "shape2": [-1.0, 0.0, 1e-10, 0.3, 1.0, 3.0, 10.0, 1e10, float("inf"), float("nan")],
    "rate": [-1.0, 0.0, 1e-10, 0.1, 0.5, 2.0, 10.0, 1e10, float("inf"), float("nan")],
    "scale": [-1.0, 0.0, 1e-10, 0.1, 0.5, 1.0, 3.0, 1e10, float("inf"), float("nan")],
    "df": [-1.0, 0.0, 1e-10, 0.5, 1.0, 5.0, 30.0, 1e10, float("inf"), float("nan")],
    "df1": [-1.0, 0.0, 1e-10, 1.0, 2.0, 5.0, 30.0, 1e10, float("inf"), float("nan")],
    "df2": [-1.0, 0.0, 1e-10, 1.0, 3.0, 10.0, 50.0, 1e10, float("inf"), float("nan")],
    "ncp": [-1.0, 0.0, 1e-10, 0.1, 2.0, 10.0, 1e10, float("inf"), float("nan")],
    "size": [-1.0, 0.0, 1e-10, 1.0, 5.0, 10.0, 100.0, 1e10, float("inf"), float("nan")],
    "prob": [-0.1, 0.0, 1e-10, 0.01, 0.2, 0.5, 0.9, 1.0, 1.1, float("nan")],
    "mu": [-1.0, 0.0, 1e-10, 0.1, 1.0, 7.0, 50.0, 1e10, float("inf"), float("nan")],
    "lambda_": [-1.0, 0.0, 1e-10, 0.001, 0.1, 5.0, 100.0, 1e10, float("inf"), float("nan")],
    "min": [float("-inf"), -1e10, -3.0, 0.0, 4.0, 1e10, float("inf"), float("nan")],
    "max": [float("-inf"), -1e10, -4.0, 0.0, 4.0, 1e10, float("inf"), float("nan")],
    "m": [-1.0, 0.0, 1e-10, 3.0, 5.0, 8.0, 1e10, float("inf"), float("nan")],
    "n": [-1.0, 0.0, 1e-10, 4.0, 6.0, 10.0, 1e10, float("inf"), float("nan")],
    "k": [-1.0, 0.0, 1e-10, 2.0, 3.0, 4.0, 1e10, float("inf"), float("nan")],
    "nmeans": [-1.0, 0.0, 1e-10, 2.0, 5.0, 10.0, 1e10, float("inf"), float("nan")],
    "nranges": [-1.0, 0.0, 1e-10, 1.0, 2.0, 3.0, 1e10, float("inf"), float("nan")],
    "nu": [0.0, 0.5, 2.0, 5.0],
    "a": [float("-inf"), 0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 0.75, 1.0, 1.5,
          2.0, 3.0, 5.0, 8.0, 10.0, 20.0, 100.0, float("inf"), float("nan")],
    "b": [float("-inf"), 0.0, 0.02, 0.08, 0.2, 0.4, 0.8, 1.0, 1.2, 2.0,
          4.0, 6.0, 9.0, 15.0, 30.0, 80.0, 200.0, 1e3, float("inf"), float("nan")],
    "deriv": [0.0, 1.0, 2.0, 3.0], "digits": [-2.0, 0.0, 3.0, 10.0],
    "logx": [float("-inf"), -1e3, -100.0, -50.0, -20.0, -10.0, -5.0, -2.0,
             -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0,
             500.0, 1e3, float("inf"), float("nan")],
    "logy": [float("-inf"), -2e3, -200.0, -80.0, -30.0, -15.0, -8.0, -3.0,
             -1.5, -0.75, -0.1, 0.0, 0.25, 0.75, 1.0, 1.5, 3.0, 8.0, 15.0,
             30.0, 80.0, 200.0, 800.0, 2e3, float("inf"), float("nan")],
    "y": [-3.0, -1.0, 1.0, 4.0], "expon_scaled": [False, True],
}
