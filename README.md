# accudist.design

Design specifications for **accudist** — a Python package providing probability
distribution functions with R-grade numerical precision, by wrapping R's own `nmath`
C library as NumPy ufuncs.

**This repository contains specifications only. It contains no package code.**
The implementation lives in a sibling repo, `../accudist`, which implementing agents
create per [docs/09-build-release.md](docs/09-build-release.md#repo-scaffold).

## Start here

| | |
|---|---|
| **[AGENTS.md](AGENTS.md)** | Entry point. Invariants, hard rules, and the task→document routing table. |
| [docs/README.md](docs/README.md) | Index of all specs, with the settled-decision summary. |
| [docs/functions.toml](docs/functions.toml) | Canonical machine-readable inventory: 106 generated functions, 4 bespoke, 5 RNG primitives, 20 documented exclusions. |

## Why

`scipy.stats` underflows to `-inf` in tail regions where R returns finite, correct
values, and its quantile functions accept no log-scale input at all. Measured on
scipy 1.17.1 against R 4.5.2:

```
                                        R 4.5.2         scipy 1.17.1
pbinom(900, 1000, 1/6, lower=F, log=T)  -1312.687973    -inf
ppois(200, 0.1, lower=F, log=T)         -1331.454401    -inf
pgamma(1e5, 2, lower=F, log=T)          -99988.48706    -inf
qnorm(-1000, log.p=TRUE)                -44.61574773    -inf
qt(-700, 5, log.p=TRUE)                 -9.9238968e+60  +inf   <- wrong sign
```

Target API:

```python
import accudist as ad
ad.ppois(200, 0.1, lower_tail=False, log=True)     # -1331.454401
```

Full measured evidence, including the many cases where scipy is perfectly accurate, is
in [docs/appendix/scipy-gap-evidence.md](docs/appendix/scipy-gap-evidence.md).

## Licensing

- **This repo** is licensed **CC-BY-4.0** ([LICENSE](LICENSE)). It contains prose and a
  TOML inventory — no GPL-derived code.
- **The implementation repo** must be **GPL-2.0-or-later**, because R's `nmath` sources
  are GPL-2-or-later and linking them makes the extension a derivative work. This means
  importing `accudist` subjects the importing work to the GPL. See
  [ADR-0001](docs/adr/0001-license.md).

## Repo contents

```
AGENTS.md                    normative entry point
docs/
  README.md                  index + decision summary
  01..10-*.md                normative specifications
  functions.toml             canonical machine-readable inventory
  adr/0001..0018             decision records, incl. rejected options
  appendix/                  measured evidence and inventories
tools/
  gen_functions_toml.py      regenerates docs/functions.toml
tmp/rmath/                   scratch reference copy of statslabs/rmath (gitignored)
```

`tmp/rmath` is a 2018 snapshot (~R 3.4-era) kept only for reading. accudist vendors
`src/nmath` fresh from the R 4.5.2 tarball — see
[ADR-0003](docs/adr/0003-c-source-vintage.md).
