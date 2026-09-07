# Licence

accudist is licensed under the **GNU General Public License, version 2 or (at
your option) any later version**.

The reason is not a preference: accudist statically links R's `nmath` sources,
which R Core distributes under GPL-2-or-later, so the extension module is a
derivative work and cannot be licensed more permissively. The alternatives, a
clean-room reimplementation or a runtime dependency on an installed R, would each
forfeit the point of the package (R's exact algorithms, `pip install`).

## What this means for you

- **Importing accudist makes the importing work subject to the GPL.** If you
  distribute software that imports accudist, that software must be distributed
  under GPL-compatible terms with source available. This is the same constraint
  users of `rpy2` accept.
- Using accudist in your own analyses, scripts and internal tools that you do not
  distribute imposes no obligation.
- Services that use accudist server-side are not "distribution" under GPL-2.

## Files

- `LICENSE`: GPL-2 text, as shipped with R.
- `NOTICE`: copyright statements for the vendored sources.
- `vendor/nmath/COPYING`: R's own copy of the licence.
- `vendor/nmath/include/Rmath.h` is LGPL-2.1-or-later.
- Per-file copyright headers of The R Core Team, The R Foundation and the
  individual authors are preserved verbatim under `vendor/nmath/`.

The corresponding source is this repository and the sdist on PyPI.
