NOTE: I believe the `clang-format` pre-commit in
https://github.com/pre-commit/mirrors-clang-format is better than this package
in all ways.  I recommend using that one unless you have a good reason.

# Example usage

In your `.pre-commit-hooks.yaml` file:

```
repos:
-   repo: https://github.com/jlebar/pre-commit-hooks.git
    hooks:
      -   id: do-not-submit
      -   id: bazel-buildifier

      # pre-commit 2.9.0 and newer should be able to use the following
      # (note: untested).
      - id: clang-format-diff
        types_or: [c++, c, java, javascript, objective-c, protobuf, c#]
```

`types_or` is a pre-commit 2.9.0 feature, so before that you had to do something like the following.

```
# FOR PRE-COMMIT VERSIONS EARLIER THAN 2.9.0
#
# Before pre-commit 2.9.0, multiple rules were required if you want to
# format (say) C and C++.  Do not be tempted to combine them as one rule
# with types: [c, c++]!  That will only match files which are "both" C
# and C++, i.e. ".h" files.
-   id: clang-format-diff
    name: clang-format C++
    types: [c++]
-   id: clang-format-diff
    name: clang-format C
    types: [c]
-   id: clang-format-diff
    name: clang-format Java
    types: [java]
-   id: clang-format-diff
    name: clang-format JavaScript
    types: [javascript]
-   id: clang-format-diff
    name: clang-format Objective-C
    types: [objective-c]
-   id: clang-format-diff
    name: clang-format Protobuf
    types: [protobuf]
-   id: clang-format-diff
    name: clang-format C#
    types: [c#]

# If you're formatting both C and C++ code, perhaps you want don't want to
# format every header file twice, as the above incantation will do.  In
# that case, you can use something like the following.
-   id: clang-format-diff
    name: clang-format C++
    types: [c++]
-   id: clang-format-diff
    name: clang-format C
    types: [c]
    exclude_types: [c++]
```

# Notes on clang-format rules

This repository exposes two different clang-format rules.

 - `clang-format-diff` checks only the lines you've touched in this commit.
 - `clang-format-whole-file` checks the entirety of every file you've touched in
   the commit.

There's an obvious tradeoff between these two, which is that if you're
formatting the whole file and bad formatting slips in, the whole-file check will
cause bigger diffs, but will also catch and fix the formatting error.

But there is a non-obvious tradeoff as well, namely, I haven't figured out how
to integrate `clang-format-diff` with continuous integration (Travis, CircleCI,
etc.) nicely.  If you want to do formatting checks in CI, I recommend using
clang-format-whole-file.

The problem is that pre-commit runs on commits, but CI runs on pull requests,
which may have multiple commits.  If you want to check a PR in CI using
clang-format-diff, all of your options are bad.

 - Fold together all of the PR's changes and check that this whole change is
   formatted correctly.  Unfortunately this sometimes flags changes that do
   not appear when checking the individual commits.  For example,
   clang-format likes to align comments between two lines:

   ```
   int x;    // note the extra indentation on this comment
   int bar;  // baz
   ```

   If you commit these two lines together as a single change,
   clang-format-diff will align the comments, but if you commit them
   separately, it won't.  Thus this method of checking formatting in CI can
   lead to changes that users won't observe while developing locally.  :(

 - Don't fold together all of the PR's changes and check that each commit is
   formatted properly.  The problem with this is that now users can't fix
   formatting issues except by editing history, and many users aren't
   comfortable with this.

If you're running this presubmit in CI, for now I must sadly recommend
clang-format-whole-file.

Note that when you run pre-commit in CI, you still want to run it on all files
modified in the PR, so users will *still* have a version of the above problem,
namely that when they run pre-commit locally, it will by default check only the
files modified in the topmost commit.  Instruct your users to do something like

```
pre-commit run --from-ref $(git merge-base origin/master HEAD) --to-ref HEAD`
```

Note for whole-file mode users: When we upgrade the clang-format binary, it
*will* change style.  You don't want everyone to discover these changes for
themselves the first time they touch a file after the upgrade.  Therefore I
recommend reformatting your whole repository (yup) every time you pull an update
of this pre-commit hook.  You can skip this bulk reformat in git blame by adding
it to `.git-blame-ignore-revs`.
