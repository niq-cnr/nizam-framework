# Bare-reference negative fixture (F-055, NDEBT-005b)

This fixture carries a BARE, stale numbered-document reference: 05_gamma.md,
whose basename is enumerated by no key_document in the canonical index
`enum_index.json`. It is the exact NDEBT-003b shape -- a bare `NN_name.md`
surviving a renumbering -- that C9's `/`-qualification and C10's three
sub-checks both miss. vlib_bare_ref_resolves must FAIL (return 1) on this file.

The resolving reference 00_alpha.md is included so the guard is shown to flag
only the stale token, not every bare reference in the file.
