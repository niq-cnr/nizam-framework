<!-- INTENTIONAL NEGATIVE FIXTURE - untagged code fence, used only via tools/validate.sh --target -->
---
id: untagged-fence-fixture
title: "Untagged Fence Fixture"
description: "Intentional negative fixture for tools/validate.sh --target: fully valid 6-key frontmatter (self-referential authoritative_source) but one fenced code block opened without a language tag."
version: 0.1.0
status: draft
authoritative_source: tools/fixtures/untagged_fence.md
---

# Untagged Fence Fixture

This file intentionally fails the C3 untagged-fence sweep only -- C1 and C2 both pass
on this file in isolation. The block below is opened with a bare fence and no
language tag, in violation of NDS Sec 6.2:

```
this fence has no language tag
```

This fixture is reachable only via `bash tools/validate.sh --target
tools/fixtures/untagged_fence.md`; it is never part of the default (no-args)
repo-wide sweep, which structurally excludes `tools/fixtures/`.
