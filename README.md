# Example usage

In your `.pre-commit-hooks.yaml` file:

```
repos:
-   repo: https://github.com/jlebar/pre-commit-hooks.git
    hooks:
      -   id: do-not-submit
      -   id: bazel-buildifier

      # Yes, multiple rules are required if you want to format (say) C and C++.
      # Do not be tempted to combine them as one rule with types: [c, c++]!
      # That will only match files which are "both" C and C++, i.e. ".h" files.
      -   id: clang-format
          name: clang-format C++
          types: [c++]
      -   id: clang-format
          name: clang-format C
          types: [c]
      -   id: clang-format
          name: clang-format Java
          types: [java]
      -   id: clang-format
          name: clang-format JavaScript
          types: [javascript]
      -   id: clang-format
          name: clang-format Objective-C
          types: [objective-c]
      -   id: clang-format
          name: clang-format Protobuf
          types: [protobuf]
      -   id: clang-format
          name: clang-format C#
          types: [c#]

      # If you're formatting both C and C++ code, perhaps you want don't want to
      # format every header file twice, as the above incantation will do.  In
      # that case, you can use something like the following.
      -   id: clang-format
          name: clang-format C++
          types: [c++]
      -   id: clang-format
          name: clang-format C
          types: [c]
          exclude_types: [c++]
```

# Notes on clang-format rules

The clang-format rules this repository provides are different from those in most
other pre-commit repositories I've seen.

1. Rather than using the clang-format binary you might have on your system, this
   repository fetches a binary at a fixed version.  This is important because
   clang-format's formatting changes between versions!

2. Rather than checking that the whole file is clang-formatted, we only check
   that the part you touched is formatted, using LLVM's git-clang-format tool.
