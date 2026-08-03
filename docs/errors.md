# Numerical errors

R's nmath routines report domain, range, convergence, precision, and underflow
conditions. `accudist` captures those conditions without allowing the C library to
print or terminate the process.

By default, domain, range, and convergence conditions issue Python warnings.
Precision and underflow conditions are ignored because they commonly accompany
usable tail results.

Use `errstate` as a context manager or decorator to select `"ignore"`, `"warn"`,
or `"raise"` independently for each category:

```python
import accudist as ad

with ad.errstate(domain="raise"):
    ad.dnorm(0, sd=-1)

with ad.errstate(all="raise"):
    ad.ppois(200, 0.1, lower_tail=False, log=True)
```

The keyword names are `domain`, `range`, `noconv`, `precision`, and `underflow`.
Policies are local to the current thread and nested contexts restore the preceding
policy when they exit. Raised exceptions and warning classes are exported from the
top-level `accudist` package.
