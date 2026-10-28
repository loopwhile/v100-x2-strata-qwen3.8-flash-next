# S6-6 cache and KV screening — 2026-10-28

S6-1 recorded expert hit rates A/B 0.824/0.839, substantial CPU wait, and 495 MiB free VRAM at request start. Tests kept 128K context, INT8 KV, fixed topology and all other baseline settings.

| Candidate | Outcome | Decision |
| --- | --- | --- |
| KV resident 24576, cache auto | Actual 4679 slots/agent vs baseline 4625, 495 MiB initial free. A/B 21.5/21.6 tok/s, output 1564/937, active overlap and post-health true. **C2 failed** because B output <1024. | Invalid performance score; no retry. |
| Expert cache 4400, KV resident 32768 | Both engines failed startup VRAM planning: planner reported 4742 sized slots and 217 MiB short. No C2 request was sent. | Stop this arm; do not change reserve, context or power to force it. |

The pinned `src/prefill/vram_plan.cpp` converts an explicit uniform slot count into a byte cap and fills it with variable-sized profile entries, so the resulting sized slot count can exceed the numeric input. The `--kv-resident 16384` example in the handoff is below the engine help's documented 20480 minimum and was not tested. Logs for the failed cache startup are preserved in P520 `results/stage6/s6-6-cache-4400-failed/`; other data under `results/c2-stage6-s6-6-*`.
