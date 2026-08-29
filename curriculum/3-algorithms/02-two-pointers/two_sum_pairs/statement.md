# Pair Sums

Implement `pair_sums(numbers, target)`.

Return every **distinct pair of values** from `numbers` that adds up to `target`.

- Each pair is sorted ascending: `[1, 4]`, never `[4, 1]`.
- The list of pairs is sorted.
- A pair is distinct by its **values**, so it appears once however many ways it can be formed.
- A single element cannot pair with itself — but two elements that happen to hold the
  same value can pair with each other.
- Return an empty list when nothing adds up.
- `numbers` belongs to the caller. Do not modify it.

`numbers` may hold up to 50,000 integers, positive, negative or zero.
