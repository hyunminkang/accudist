# Domain language

- **Oracle equality** — exact binary64 equality for finite values, signed zero, and
  infinities; any two IEEE-754 NaN encodings are the same oracle result.
- **Oracle platform** — a supported operating-system and CPU-architecture pair with
  its own official R and accudist floating-point results.
- **RNG reproducibility scope** — a seed and oracle platform determine the exact draw
  sequence. Seed-state transitions remain exact on every platform.
