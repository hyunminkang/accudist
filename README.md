# accudist

`accudist` exposes R 4.5.2's probability-distribution math library as NumPy
ufuncs, preserving R's tail algorithms and raw floating-point results.

```python
import accudist as ad

ad.ppois(200, 0.1, lower_tail=False, log=True)
```

## Licence

This package and its vendored R nmath sources are licensed under
**GPL-2.0-or-later**. Importing `accudist` makes the importing work subject to
the GPL. Evaluate that implication before installing or distributing it.

Random draws use standalone Rmath's deterministic generator and are not
seed-compatible with an R interpreter session.

