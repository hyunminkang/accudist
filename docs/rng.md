# Random numbers

Random functions such as `rnorm` and `rpois` accept a draw count as their first
argument and return a `float64` NumPy array.

```python
import accudist as ad

ad.set_seed(1234, 5678)
x = ad.rnorm(5)
assert ad.get_seed() != (1234, 5678)
```

The two integers seed standalone Rmath's deterministic Marsaglia-MultiCarry
generator. This is not R's default Mersenne-Twister generator, so an accudist seed
does **not** reproduce output from R's `set.seed()`.

The same seed reproduces the same draw sequence within one accudist build. Exact draw
values and seed-state transitions are not compatibility guarantees across versions,
operating systems, CPU architectures, or alternative generator implementations.

Use `RNG` for independent streams:

```python
first = ad.RNG(11, 29)
second = ad.RNG(11, 29)

assert (first.rpois(10, 3) == second.rpois(10, 3)).all()
```

The default stream and every `RNG` instance are serialized around the underlying
standalone-Rmath global state. Each object saves and restores its own seed, so
interleaving streams remains deterministic.

Distribution parameter arrays are recycled to the requested draw count. Empty
parameter arrays, parameters longer than the draw count, and invalid draw counts
raise `ValueError`.
