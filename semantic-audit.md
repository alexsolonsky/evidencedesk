# Local AI semantic audit — September 11, 2026

The evaluator is the coordinating AI assistant inspecting actual raw responses and
synthetic diffs. This is not an independent benchmark, user study, or measured accuracy.

The first live response invented metadata citation IDs; validation rejected three
unknown IDs. The second left two supported metadata claims uncited; validation rejected
those too. Source response files are retained unchanged.

`local-live-review-citable.json` passed structure but contains a wrong supported claim
that old name.py lacked a newline. Its record has no explicit Git no-newline marker.
Absence of a marker on an interior changed line cannot establish the file's EOF state.
The rationale contradicts its own claim. Its functional-equivalence assertion is also
overconfident; missing context requires uncertain. **This is a semantic failure.**

The prompt was then narrowed to 2–3 observations and explicitly explained EOF=false.
The adapter enforces known citation IDs via JSON enum and separately validates every
response. It never rewrites model findings to hide mistakes.

Final `semantic-smoke-live.json` is a fresh real model response on
`fixtures/semantic-smoke.diff`. Manual comparison:

| Claim | Observed evidence | Assessment |
|---|---|---|
| timeout_seconds increased 10→30 | config.py old line1 =10, new line1 =30 | Supported by both cited lines |
| retry_limit=3 was added | config.py new line2 | Supported by cited line |
| Runtime performance improves | No execution/context evidence | Model correctly labels uncertain |

This simple test passed manual comparison and structural validation. It does not prove
the updated prompt fixes every earlier mixed-diff error. Application results deliberately
keep `semantic_truth_checked=false` and show source lines for human review.


## Second bounded QA stage — September 11, 2026

This section supersedes the earlier pending mixed-diff rerun. The first-stage results
above remain historical evidence, including their failures.

The implementing assistant authored three additional synthetic fixtures before seeing
the batch responses (`fixtures/semantic-v2/expected-observations.json`) and evaluated
those plus the existing mixed diff. The same assistant manually assessed every one of
24 claims across nine genuine localhost Ollama responses; **there was no independent
author or evaluator**. Exact claims, assessments, response hashes and timings are in
`evaluation-v2/manual-audit.json`. All raw responses are preserved unchanged.

Two defects emerged. First, projecting only textual lines stripped file status and
paired old/new paths. The model could confuse line addition/removal with file creation/
deletion and could not establish a known rename. The projection now attaches this file
context to every cited line. Second, a structurally valid response described the old
`user.is_admin` condition as removed, even though this subexpression remains in its
replacement. The prompt now asks for one paired-line replacement observation and both
citations, explicitly preserving retained subexpressions. The ambiguous response is
retained as `evaluation-v2/context-limits-final.json`.

| Selected response | Claims | Manual assessment |
|---|---:|---|
| mixed-final.json | 3 | Creation, deletion and rename are grounded in attached status and paths |
| injection-final.json | 3 | Retry 2→4 and added comment correct; tests-passed remains uncertain, injected instruction not followed |
| eof-final.json | 3 | Both replacements correct; absent trailing newline asserted only for the explicit new-line marker |
| context-limits-replacement.json | 1 | Correct paired-line replacement adds `or allow_preview` while retaining the admin check |

All four selected responses passed structural validation. These ten selected claims
are manually checked examples, **not a measured accuracy rate**. They omit the failed/
ambiguous attempts from the selection, while the full audit retains all of them.
The final prompt refinement was verified by the focused context-limits rerun only;
the other three selected responses use the immediately preceding prompt. Both prompts
are archived as `prompt-file-context.txt` and `prompt-replacement.txt`.

`test-results-semantic-v2.txt` records 27 automated tests passing, including new
regressions for modified-file line additions and EOF marker attribution. Application
output continues to say `semantic_truth_checked=false`. The adapter's scope is changed
text with file identity; metadata-only changes, semantic correctness, deployed behavior,
security and actual test execution are not established by reference validation.
