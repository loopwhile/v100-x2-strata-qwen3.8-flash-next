# Stable P520 serving deployment — 2026-11-11 KST

**PASS; both operating containers were running during deployment validation.**
The user subsequently stopped both containers; live inspection confirmed
`exited` for both. They remain stopped during the commit/push and checkout
synchronization. The user selected **S10-D4**
(spec 8, DFlash2 confidence 0.7) and requested permanent operating names,
following the `p100-llm` convention. This is a separately authorized operating
deployment, not a new Stage 10 experiment or benchmark result.

| Contract | A | B |
| --- | --- | --- |
| Container / client API alias | `p520-llm-a` | `p520-llm-b` |
| P520 loopback | 8080 | 8081 |
| ThinkPad URL | `http://127.0.0.1:18080/v1` | `http://127.0.0.1:18081/v1` |
| OpenCode model selection | `p520-a/p520-llm-a` (default) | `p520-b/p520-llm-b` |
| Host GPU | 0 | 1 |
| CPU affinity | `0-2,6-8` | `3-5,9-11` |

Release: `results/p520-serving/releases/s10-d4-20261111T012331` on P520.
Image: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`.
Source: `712fec6b4297c9cfd32ab43daaa2979a9aa01edf`, engine 0.1.59,
CUDA 12.9.1 / sm_70. Original IQ3_XXS, native pack, stock DFlash2 and shared
vocabulary retained; INT8 KV, 131072 context, 32768 resident KV, mmap experts,
prefill auto. No lag/NOWAIT or allocation combinations were added.

## Verification

- Initial live preflight: no running Docker containers or GPU consumers;
  8080/8081 free; existing 150 W caps and 135–1245 MHz clock service observed.
- All 15 entries of the archived Stage 8 asset SHA256 manifest passed,
  including both GGUF shards, native metadata/tokenizer and shared MTP files.
  DFlash2 pack matched `4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`;
  engine matched `ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031`.
- Both `/health`: loaded, context 131072. `/v1/models` lists the permanent alias.
  Runtime process inspection confirmed DFlash2 alone, fallback none, spec 8,
  confidence 0.7 and the three archived D4 environment overrides.
- **Both effective engine argument lists exactly match archived D4 batch-3.**
  No server/engine binary or source was patched.
- Short concurrent requests through the original ThinkPad tunnel: A and B
  both returned `P520_OK`, reporting their requested permanent alias.
- OpenCode v2.1.3 parsed both updated global config files, listed both models,
  and completed separate file/tool-free A and B requests with `P520_OK`.
- Four CPU preservation checks passed: foreign container refusal, foreign live
  workload refusal, occupied-name refusal, and foreign release-path refusal.

## Model identity and preserved startup attempt

The unmodified server uses `model_name` to recognize the Qwen family before
selecting DFlash2. The initial bare-name attempt selected MTP and was stopped
before sending the smoke requests. It is retained under
`p520-llm-{a,b}-archive-name-gate-20261111T0120`, with its original release
`s10-d4-20261111T011422`. No archived experiment ID was reused.

The successful release uses canonical names
`qwen3.8-flash-next-iq3_xxs_p520_a/b` and the server's native `aliases` setting
for `p520-llm-a/b`. This preserves exact D4 engine arguments and keeps client
names independent of future internal model identifiers.

## Preservation, operation and rollback

Historical containers/images/model assets, Stage 2–10 runners and results,
GPU power/clock/host settings, ports and the ThinkPad tunnel are unchanged.
Both new operating containers use `unless-stopped` restart policy.
The deployment-time inventory contained 472 containers: the prior inventory plus the
two stopped startup-attempt containers and the two live operating containers.
Both operating containers were later stopped by the user and preserved.

OpenCode backups are next to the original files, with suffix
`.before-p520-serving-20261111T011556`. Initial rollback is to stop the new pair
and leave it preserved, returning to the initial stopped serving state:

```bash
ssh p520 'docker stop -t 30 p520-llm-a p520-llm-b'
```

Raw receipts, successful/initial release backups, API responses, OpenCode
events, asset validation and sanitized host inventory are under ThinkPad
`results/p520-serving-20261111/`; release configs and logs also remain on P520.
See [the operating guide](../../docs/P520_SERVING.md) for daily commands and
future versioned image replacement/rollback. No C2 was rerun and these short
smoke requests do not establish long-session or semantic quality.
