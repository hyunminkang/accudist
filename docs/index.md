# accudist

**Probability distributions with R-grade numerical precision, as NumPy ufuncs.**

accudist wraps R 4.5.2's `nmath` C library, the code behind R's `pnorm`, `qbeta`,
`ppois` and friends, and exposes it in Python with R's names, argument order and
defaults. Its reason to exist is the tails: R computes upper tails and
log-probabilities directly, where `scipy.stats` computes `1 - cdf` and underflows.

```python
import accudist as ad

ad.ppois(200, 0.1, lower_tail=False, log=True)   # -1331.4544006213939  (scipy.stats: -inf)
ad.qnorm(-1000, log=True)                          # -44.61574773...      (scipy.stats: no log_p)
```

| call | R 4.5.2 | accudist | scipy 1.17 |
|---|---|---|---|
| `ppois(200, 0.1, lower=F, log=T)` | -1331.454401 | -1331.454401 | -inf |
| `pbinom(900, 1000, 1/6, lower=F, log=T)` | -1312.687973 | -1312.687973 | -inf |
| `pgamma(1e5, 2, lower=F, log=T)` | -99988.48706 | -99988.48706 | -inf |
| `qbeta(-1000, 0.5, 0.5, log.p=T)` | 1.11e-308 | 1.11e-308 | 0.0 |

!!! warning "Two things to know before you `pip install`"
    **Licence.** accudist is GPL-2.0-or-later because it links R's GPL sources.
    Importing it makes the importing work subject to the GPL. See [Licence](license.md).

    **Random numbers.** `r*` functions do not reproduce R's default `set.seed()`
    streams. They reproduce R only under `RNGkind("Marsaglia-Multicarry")`. See
    [Random numbers](rng.md).

## Where to go

- [Installation](installation.md): wheels, source builds, uv.
- [Quickstart](quickstart.md): five minutes with the API.
- [R to accudist](r-mapping.md): naming rules, dispatch, argument-order hazards.
- [Precision](precision.md): what "eight significant digits against R" means and how it is tested.
- [API reference](api-reference.md): every function, its R equivalent, and notes.
