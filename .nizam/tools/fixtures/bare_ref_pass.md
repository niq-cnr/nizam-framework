# Bare-reference positive fixture (F-055, NDEBT-005b)

Every BARE numbered-document reference in this file resolves against the
canonical index `enum_index.json`: see 00_alpha.md and 01_beta.md for the
governing rules. A `/`-qualified path such as other/09_ignored.md is not a
bare reference (it carries a directory prefix), so vlib_bare_ref_resolves does
not check it, and the embedded token in `a01_beta.md` is not a bare reference
either. vlib_bare_ref_resolves must return 0 for this file.
