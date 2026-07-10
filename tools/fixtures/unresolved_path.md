# check_c9_path_resolution FAIL Fixture

This body names exactly one concrete, directory-qualified,
non-placeholder, shipped-extension reference to a file that does not
exist on disk: docs/architecture/ADR-999-does-not-exist.md. C9 must
reject this file when it is directly --target-ed.
