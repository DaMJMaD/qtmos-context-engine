# Body Layout

The modular body set is split by role here:

- `top-level/` preserves the older pre-modular body files.
- `core/` holds the stable shared cortex bodies.
- `leader/` holds leader-owned mirrored bodies.
- `follower/` holds follower-owned mirrored bodies.

This is intentional. The old same-folder doubles existed because Step 1 and Step 2 could need independent access to effectively the same logic while avoiding file-handle collisions.

So the duplicate identity bodies are preserved as:

- `leader/IdentifyThyself.txt`
- `follower/IdentifyThyBody.txt`

That keeps the concurrency reason visible in the structure.
