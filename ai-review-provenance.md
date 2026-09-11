# AI review provenance

Created September 11, 2026 by the coordinating Codex AI assistant after reading the actual `example.json` evidence pack. This is a real AI-authored review of a synthetic demonstration fixture. The four claims were also selected by that assistant; this is not a held-out benchmark or an independently authored user evaluation.

Workflow: deterministic Git diff extraction -> AI reads evidence and assesses claims -> separate deterministic validator checks the output schema and evidence references. The review identifies one supported claim, a newline claim contradicted by evidence, and two claims for which the supplied diff is insufficient.

No external model API was called by the CLI. The AI step was performed in this Codex conversation, not automatically by the application. No measured accuracy, live product deployment, end-to-end autonomous service, or contest submission is claimed. The exact underlying inference snapshot and marginal cost were not exposed; no credits or API calls were purchased.

Validation can establish well-formed output and valid references. It cannot establish that the AI's semantic conclusions are correct. Binary-file metadata currently has no line evidence ID; the image claim therefore has no cited line.
