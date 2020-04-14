# Example usage

In your `.pre-commit-hooks.yaml` file:

```
repos:
-   repo: https://github.com/CamusEnergy/pre-commit-hooks.git
    hooks:
      -   id: do-not-submit
      -   id: bazel-buildifier
      -   id: clang-format
```

# Notes on clang-format rules

The clang-format rules this repository provides are different from those in most
other pre-commit repositories I've seen.

Rather than using the clang-format binary you might have on your system, this
repository fetches a binary at a fixed version.  This is important because
clang-format's formatting changes between versions!
