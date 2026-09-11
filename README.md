# EvidenceDesk

Local AI code review with exact source evidence and explicit uncertainty.

Paste a Git diff, inspect the changed lines, ask a local model for observations, and
follow each citation back to its exact old or new source line. A separate deterministic
validator checks the response shape and reference IDs. **Valid references do not prove
that an AI claim is true or that code is safe.**

EvidenceDesk is a runnable local prototype, not a hosted or production service.

## Quick start

Requirements:

- **Python 3.9 or later** and a modern browser. The app uses only the Python standard
  library: no pip installation, build step, account or API key is required.
- For live AI review, **Ollama must already be running locally** with a compatible
  installed text model. The tested model was `qwen3.6:35b`; other models are not
  certified by these results. Model files and hardware requirements are separate
  from this repository. EvidenceDesk does not install or download them.
- **Git** is needed to create diffs and to run the full automated test suite.

From this directory:

```sh
python3 run.py
```

Open **http://127.0.0.1:8769**. On Windows, `py -3 run.py` is an alternative where
that launcher is installed. Use `python3 run.py --port 8770` if the default port is busy.
The launch command changes to the repository directory automatically; `python3 app.py`
also works. Stop the server with Ctrl-C.

1. Choose **Load example**, paste a diff, or load a UTF-8 `.diff` file.
2. Choose **Inspect evidence** to inspect changed lines without a model.
3. Select an installed model and choose **Review this change** for a real local review.
4. Read the observations, their uncertainty, and cited source lines together.
5. Use **Export JSON** to save evidence, review, validation and provenance.

If Ollama or the selected model is unavailable, the UI says **Inference unavailable**.
Extraction and validation of imported review JSON still work. Import only an object
with a `claims` array, not a complete exported bundle. The included
[ai-review.example.json](ai-review.example.json) matches `fixtures/mixed.diff` and is
explicitly an imported, AI-authored synthetic example; see its
[provenance](ai-review-provenance.md). It is never substituted for live inference.
If you start Ollama after opening the app, reload the page to refresh model availability.

## CLI

```sh
# Read local runtime status; does not install or run a model.
python3 local_review.py --status

# Run an already installed model on a small synthetic diff.
python3 local_review.py fixtures/semantic-smoke.diff --model qwen3.6:35b --output fresh-review.json

# Extract evidence without any AI runtime.
python3 evidence_pack.py fixtures/mixed.diff --json fresh-evidence.json --markdown fresh-evidence.md

# Validate an imported review against the matching evidence pack.
python3 validate_review.py fresh-evidence.json ai-review.example.json
```

Use fresh output names. The local-review CLI refuses to overwrite an existing result;
the deterministic extractor writes to the requested paths and can replace their contents.
To review a real repository change, create an ordinary diff in that repository:

```sh
git diff --no-ext-diff --no-color BASE HEAD > changes.diff
```

Replace `BASE` and `HEAD` with existing revisions, then load the file in EvidenceDesk.
Diff contents are treated as data; the application does not execute them.

## Scope and limits

The UI/local-AI adapter accepts a **64,000-byte UTF-8 diff**, at most **20,000 characters
of projected evidence**, and a **150-second model response timeout**. Only one UI
inference runs at a time. Oversized input fails explicitly rather than being silently
truncated. CLI extraction has no AI dependency.

The model receives changed textual lines with file status and paired old/new paths.
Unchanged code context, binary contents, metadata-only changes, test outcomes and
runtime behavior are outside its AI review scope. The deterministic evidence pack can
retain file metadata even when the AI projection cannot review it. Inspect such changes
manually. A diff alone cannot establish deployment behavior, security or passing tests.

The parser supports ordinary `diff --git` unified diffs, additions/deletions,
rename/copy metadata, modes, empty files, binary markers, multiple hunks, Git-quoted
UTF-8 paths, CRLF file contents and explicit missing-final-newline markers. Truncated
hunks fail closed. Combined merge diffs, email patches, custom prefixes and converted
CRLF diff framing are unsupported. Ambiguous unquoted binary path headers containing
` b/` are outside the prototype's reliable path support.

Evidence IDs use the first 20 hexadecimal SHA-256 characters over file paths,
change kind, coordinates, text and EOF marker. The reference validator requires the
exact claim schema and known IDs, rejects duplicate JSON keys, and requires a citation
for supported claims. `semantic_truth_checked` remains **false**, including when
reference validation passes.

## Local data handling

The server binds only to `127.0.0.1`, checks Host/Origin headers, serves three explicit
UI assets and has no database, telemetry or accounts. The application does not persist
user diffs: inputs remain in browser/request memory until the user exports a file.
The CLI writes a result only when requested. An exported review contains source text;
inspect it before sharing.

The AI adapter contacts only `127.0.0.1:11434`, disables HTTP proxy environment settings,
and does not call a cloud fallback or substitute a saved response. Ollama is a separate
runtime: its configuration, resource use, model availability and licensing remain the
operator's responsibility. This Python development server is **not intended to be
exposed to a network or deployed as a shared web service**.

## Verification and honest evidence

```sh
python3 verify_release.py
python3 -m unittest -v
```

The recorded development suite passed **27 tests** on Python 3.14/macOS. Tests use
synthetic inputs and mocked inference for deterministic application checks; they do not
prove model accuracy. The full suite also creates temporary local Git repositories,
with no commits or network. Other operating systems/Python versions have not yet been
individually verified.

Real local model records are separate: the second evaluation batch preserved **9
responses and all 24 manually assessed claims**. Four selected cases contain **10
manually checked observations**, with reference validation passing. These are selected
after iteration, not held-out accuracy results. The implementing AI assistant both
created the fixtures and assessed the responses; no independent evaluator or user study
was involved. The final prompt refinement was tested only on one focused case; the
other three selected cases used the immediately preceding prompt.

Earlier references to nonexistent evidence IDs, an incorrect EOF conclusion, and an ambiguous condition
claim are retained. See [QA guide](qa/README.md), [semantic audit](semantic-audit.md)
and [complete second-batch assessments](evaluation-v2/manual-audit.json). Saved JSON
records are **historical synthetic runs**, not live responses when someone opens them.
The release manifest records file checksums; it is an integrity inventory, not a signed
claim of authenticity or semantic correctness.

The final-prompt desktop smoke completed a real local review and displayed three
claims with exact references; basic keyboard focus and order were checked. These are
separate UI checks and do not increase the nine-response semantic evaluation count.
A recorded demonstration, responsive testing, full accessibility checks, evaluation on
unfamiliar real diffs and measurement of reviewer benefit are still needed. No adoption,
time savings or general accuracy claims are made.

## Project and licensing

Codex AI agents assisted with implementation, debugging, tests, documentation and
synthetic evaluation. Human review remains part of the workflow. Project code and
included synthetic materials are released under the [MIT License](LICENSE).
[Third-party notices](THIRD_PARTY_NOTICES.md) distinguish the optional runtime and model
licenses; no model weights are distributed.

Integration references: [Ollama chat API](https://docs.ollama.com/api/chat) and
[structured outputs](https://docs.ollama.com/capabilities/structured-outputs).
