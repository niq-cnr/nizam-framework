# vlib_word_present FAIL Fixture

The contract was renewed twice, so the letters of the target token appear only
inside the longer word renewed -- never delimited on their own. A whole-word
probe must therefore reject the token here, where a bare substring grep would
false-pass on the containing word.
