# Domain language

- **Reference compatibility** — finite values agree with R within `1e-10` relative
  error and no absolute tolerance; any two IEEE-754 NaN encodings are equivalent.
- **Oracle platform** — a supported operating-system and CPU-architecture pair with
  its own official R and accudist floating-point results.
- **RNG reproducibility scope** — equal seeds reproduce a sequence within one build;
  exact draws and seed-state transitions are not cross-build compatibility promises.
