# EvidenceDesk — actual CLI demonstration

[Watch or download the 3:40 demonstration](evidencedesk-cli-demo.mp4) · [Download the original replay and evidence pack](evidencedesk-replay-pack.zip) · [Pitch deck](../docs/EvidenceDesk-pitch.pdf)

This 1920 × 1080, 24 fps, silent video presents an actual terminal capture with English explanation cards. The captured subprocess output is replayed at its recorded speed. It is a CLI demonstration, not a browser screen recording.

On 11 September 2026, the local `qwen3.6:35b` model ran against the disclosed synthetic diff and reported 8.368 seconds of model-request time. Its observation cited both the old and new condition on line 20. The valid review passed the deterministic validator; a deliberately unknown reference was rejected with exit code 1.

The replay ZIP preserves the original asciicast, event log, exact input, actual model response, validation output, timing metadata, scripts and a hash manifest. No precomputed response was substituted for the live invocation.

A valid reference does not establish semantic truth. This is a small synthetic demonstration, not an independent accuracy benchmark, production result or user study. Codex AI agents assisted in producing the prototype, fixtures, explanations and video. A recorded demonstration of the browser interface remains future work.

SHA-256:
- Video: `da82be5c829a535484c89c3855329678354b752ea1420905533cb389096f5cd0`
- Replay pack: `f4d9c9d9fbcd4d0a93215d0d0e9b6bf1a7d59c913e6c2491173a899c77b9f8e3`

The root release manifest covers the application release; these demonstration files were added separately.
