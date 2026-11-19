# Promoted P520 Serving Deployment (`S11X-D2`) — 2026-11-19 KST

**PASS; both promoted operating containers `p520-llm-a` and `p520-llm-b` are running (`Up`), verified live via `scripts/127-p520-serving.py check` and concurrent ThinkPad tunnel API smoke requests.**

Following user approval on 2026-11-19 (`승격하자! 운영용 도커, 문서 업데이트해줘`), the stable P520 serving pair was upgraded from `S10-D4` (`s10-d4-20261111T012331`, `sha256:dd8913d85f18...`) to **`S11X-D2`** (`s11x-d2-20261119T095616`, `strata-v100:stage11x-d2`) with all historical images, releases, and `S10-D4` containers preserved for rollback.

| Contract | Agent A | Agent B |
| --- | --- | --- |
| Container / client API alias | `p520-llm-a` | `p520-llm-b` |
| Container ID | `fdc2df3baf23...` | `460065e8cdf8...` |
| P520 loopback | `127.0.0.1:8080` | `127.0.0.1:8081` |
| ThinkPad tunnel base URL | `http://127.0.0.1:18080/v1` | `http://127.0.0.1:18081/v1` |
| Canonical model name (DFlash2 detection) | `qwen3.8-flash-next-iq3_xxs_p520_a` | `qwen3.8-flash-next-iq3_xxs_p520_b` |
| Host GPU / CPU affinity | GPU 0 / `0-2,6-8` | GPU 1 / `3-5,9-11` |
| Context / KV | `131072` / INT8, `32768` resident | `131072` / INT8, `32768` resident |

- **Release**: `results/p520-serving/releases/s11x-d2-20261119T095616` on P520
- **Image**: `strata-v100:stage11x-d2` (`sha256:26d2bbfe67bc7cb4e489e6f9283e22bb4cd59c6e9659abf3396caa4f1a4f7f38`)
- **Engine Patch & Binary SHA256**: [stage11x-d2.patch](../../docker/patches/stage11x-d2.patch) on pinned `0.1.59` (`712fec6b4297c9cfd32ab43daaa2979a9aa01edf`), `/opt/strata/engine/strata` (`7f6fc8f7858739d18b177911d32d0d832393274b4ba7797dfd3cf29e634e76a9`)
- **DFlash2 Pack SHA256**: `qwen3.8-flash-next-dflash2.q4_0-selq4.pack` (`4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`)
- **19 Verified `STRATA_*` Environment Overrides**:
  - D4 base: `STRATA_SELECT_SIMT=1`, `STRATA_SM70_TABLE=1`, `STRATA_PF_WMMA=1`
  - P1 Volta prefill: `STRATA_PF_WMMA2=1`, `STRATA_PF_WMMA_LEAN=1`, `STRATA_PF_WMMA_SKINNY=1`
  - D1 CPU `PathC7`: `STRATA_AVX512BW_IQ=22`, `STRATA_IQ_MT_MIN=1`, `STRATA_IQ_GATHER=1`, `STRATA_IQ256_GATHER=1`, `STRATA_Q2_BITPLANE=1`
  - D2 Sync/Cache & `nv_defaults`: `STRATA_SIDE_MIXER=2`, `STRATA_ATTN_DAILY=1`, `STRATA_GR_UP75=1`, `STRATA_GU_SWIGLU=1`, `STRATA_QSA_ROWS=1`, `STRATA_FUSE_WAIT=2`, `STRATA_MMAP_ADAPT_ASYNC=1`, `STRATA_COLD_OVERLAP=5`

## Live Verification Summary

1. **Archive & Install**: Verified existing `p520-llm-a` and `p520-llm-b` were `exited` under `s10-d4-20261111T012331`, renamed them cleanly to `p520-llm-{a,b}-archive-s10-d4-20261111T012331`, and installed the new `S11X-D2` containers from `s11x-d2-20261119T095616`.
2. **Start & Contract Inspection (`scripts/127-p520-serving.py start` + `check`)**:
   - Both `/health` endpoints returned `status="ok"`, `loaded=true`, `max_context=131072`.
   - Both `/v1/models` endpoints expose `p520-llm-a` / `p520-llm-b` aliases.
   - Live `/proc/<pid>/cmdline` and `/proc/<pid>/environ` confirmed `--draft dflash2 --draft-fallback none --spec 8 --draft-conf 0.7 --prefill auto`, engine SHA256 `7f6fc8f7...`, all 19 `STRATA_*` overrides active, and zero disallowed overrides (`STRATA_ADAPT_LAG`, `STRATA_ADAPT_NOWAIT`, `STRATA_PF_HC_REGION`, `STRATA_AUX_CPUS`).
3. **Engine Logs & Concurrent ThinkPad Tunnel Smoke Check (`18080` / `18081`)**:
   - Both `agent-a.log` and `agent-b.log` logged: `CPU expert kernels: AVX-2 + AVX-512BW`, `STRATA_COLD_OVERLAP=5` (`total waited 0.0 ms`), `S11X_WMMA_LEAN eligible`, `DFlash2 drafter on ... no MTP layer is loaded (--draft-fallback none)`, and `asynchronous adaptive tier`.
   - Concurrent `127.0.0.1:18080/v1/chat/completions` (`model="p520-llm-a"`) and `127.0.0.1:18081/v1/chat/completions` (`model="p520-llm-b"`) both returned `P520_OK`, `finish_reason="stop"`, reporting their permanent aliases.
   - GPU telemetry after smoke: `15475 MiB` VRAM used on both GPUs, `150.00 W` limits, `1245 MHz` clock policy active, `42 / 44 °C`.
4. **Unit Tests (`tests/test_p520_serving.py`)**: `5/5` passed on both ThinkPad and P520.

## Rollback

- Stop `S11X-D2` serving: `ssh p520 'docker stop -t 30 p520-llm-a p520-llm-b'`
- Restore preserved `S10-D4` pair (`s10-d4-20261111T012331`): rename `p520-llm-{a,b}` to archive/rollback names and rename `p520-llm-{a,b}-archive-s10-d4-20261111T012331` back to `p520-llm-{a,b}`.
