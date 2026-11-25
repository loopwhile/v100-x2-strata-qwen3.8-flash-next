# Promoted P520 Serving Deployment (`S12-C1T`) — 2026-11-25 KST

**PASS; both promoted operating containers `p520-llm-a` and `p520-llm-b` (release `s12-c1t-20261125T230758`, direct `/srv/models/strata-data/dflash2` bind-mount) were verified live via `scripts/127-p520-serving.py check`, `/metrics`, and concurrent ThinkPad tunnel API smoke requests, then stopped cleanly (`Exited (0)`) at rest per user preference.**

Following user approval on 2026-11-25 (`S12-C1T를 운영용으로 확정할게.`), the stable P520 serving pair was upgraded from `S11X-D2` (`s11x-d2-20261119T095616`, `sha256:26d2bbfe67bc...`) to **`S12-C1T`** (`strata-v100:stage12-0.1.67-c1`) and migrated under release **`s12-c1t-20261125T230758`** (replacing temporary `s12-c1t-20261125T221034`) so that DFlash2 is bind-mounted read-only directly from canonical `/srv/models/strata-data/dflash2` instead of `results/stage10-preparation/draft-data/dflash2`. All historical images, releases, original `results/stage10-preparation/draft-data/dflash2`, `S11X-D2` containers (`p520-llm-{a,b}-archive-s11x-d2-20261119T095616`), and `S10-D4` containers (`p520-llm-{a,b}-archive-s10-d4-20261111T012331`) remain preserved and intact for rollback.

| Contract | Agent A | Agent B |
| --- | --- | --- |
| Container / client API alias | `p520-llm-a` | `p520-llm-b` |
| Container ID | `ce5d59f2d4b1...` | `c32d13e787ff...` |
| P520 loopback | `127.0.0.1:8080` | `127.0.0.1:8081` |
| ThinkPad tunnel base URL | `http://127.0.0.1:18080/v1` | `http://127.0.0.1:18081/v1` |
| Canonical model name (DFlash2 detection) | `qwen3.8-flash-next-iq3_xxs_p520_a` | `qwen3.8-flash-next-iq3_xxs_p520_b` |
| Host GPU / CPU affinity | GPU 0 / `0-2,6-8` | GPU 1 / `3-5,9-11` |
| Context / KV | `131072` / INT8, `32768` resident | `131072` / INT8, `32768` resident |

- **Release**: `results/p520-serving/releases/s12-c1t-20261125T230758` on P520 (prior temporary `s12-c1t-20261125T221034` release directory preserved on disk)
- **Image**: `strata-v100:stage12-0.1.67-c1` (`sha256:33b61b0432e81c44a6d212ca38be46b4191a989a65c4a0141e2cbc9b116f10ec`)
- **Engine Patch & Binary SHA256**: [stage12-d1.patch](../../docker/patches/stage12-d1.patch), [stage12-d2.patch](../../docker/patches/stage12-d2.patch), and [stage12-d3.patch](../../docker/patches/stage12-d3.patch) on pinned `0.1.67` (`d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`), `/opt/strata/engine/strata` (`c01770d00bd49985f008e39d722b996f0ad476545c8bd50bb96ad8a66ed52dda`)
- **DFlash2 Host Mount & Pack SHA256**: `/srv/models/strata-data/dflash2` -> `/stage10-data/dflash2` (RO; copied with exact `mtime_ns` & SHA256 verification across `/dev/nvme0n1p2` -> `/dev/nvme1n1p1`), `qwen3.8-flash-next-dflash2.q4_0-selq4.pack` (`4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`)
- **Explicit Prefill Safety Flag**: `--prefill auto:8192` (never bare `--prefill auto`)
- **14 Verified `STRATA_*` Environment Overrides**:
  - Docker page-cache safety: `STRATA_OOMD_ROOM=0`
  - CPU `PathC7`: `STRATA_AVX512BW_IQ=22`, `STRATA_IQ_MT_MIN=1`, `STRATA_IQ_GATHER=1`, `STRATA_IQ256_GATHER=1`, `STRATA_Q2_BITPLANE=1`
  - Mmap bounce ring & overlap: `STRATA_MMAP_ADAPT_ASYNC=1`, `STRATA_COLD_OVERLAP=5`
  - Volta GPU & sync/routing parity: `STRATA_HC_V100=1`, `STRATA_SELECT_SIMT=1`, `STRATA_ATTN_DAILY=1`, `STRATA_GR_UP75=1`, `STRATA_FUSE_WAIT=2`, `STRATA_ROUTE_TAIL_SKIP=7`

## Live Verification Summary

1. **DFlash2 Canonical Mount Migration & Install**:
   - Populated `/srv/models/strata-data/dflash2` (`/dev/nvme1n1p1`, `loopwhile:loopwhile`) from `results/stage10-preparation/draft-data/dflash2` (`/dev/nvme0n1p2`) via `cp -a`, verifying identical SHA256 and nanosecond `mtime_ns` across all 4 files (`draft_vocab.bin`, `qwen3.8-flash-next-dflash2.q4_0-selq4.pack`, `.ok`, `qwen3.8-flash-next-dflash2.q4_0.pack`) while leaving `results/stage10-preparation/draft-data/dflash2` untouched for rollback archives.
   - Replaced only the stopped temporary `s12-c1t-20261125T221034` containers with the recreated `S12-C1T` pair from `s12-c1t-20261125T230758` (`p520-llm-a` `ce5d59f2d4b1...`, `p520-llm-b` `c32d13e787ff...`), preserving `p520-llm-{a,b}-archive-s11x-d2-20261119T095616`, `p520-llm-{a,b}-archive-s10-d4-20261111T012331`, and `strata-jmn-iq2xs-agent-{a,b}`.
2. **Start & Contract Inspection (`scripts/127-p520-serving.py start` + `check`)**:
   - Both `/health` endpoints returned `status="ok"`, `loaded=true`, `max_context=131072`.
   - Both `/v1/models` endpoints expose `p520-llm-a` / `p520-llm-b` aliases.
   - Verified container bind-mount `/stage10-data/dflash2` -> `/srv/models/strata-data/dflash2` (`RW=false`).
   - Live `/proc/<pid>/cmdline` and `/proc/<pid>/environ` confirmed `--draft dflash2 --draft-fallback none --spec 8 --draft-conf 0.7 --prefill auto:8192`, engine SHA256 `c01770d00bd49985f008e39d722b996f0ad476545c8bd50bb96ad8a66ed52dda`, all 14 `STRATA_*` overrides active (`+ STRATA_EXECV=1`), and zero disallowed overrides (`STRATA_ADAPT_LAG`, `STRATA_ADAPT_NOWAIT`, `STRATA_PF_HC_REGION`, `STRATA_AUX_CPUS`, `STRATA_PF_WMMA`, `STRATA_PF_WMMA2`).
3. **Container Logs, `/metrics` & Concurrent ThinkPad Tunnel Smoke Check (`18080` / `18081`)**:
   - Both container logs recorded `[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)` and model alias registration (`p520-llm-a` / `p520-llm-b`).
   - Concurrent `127.0.0.1:18080/v1/chat/completions` (`model="p520-llm-a"`) and `127.0.0.1:18081/v1/chat/completions` (`model="p520-llm-b"`) both returned `P520_OK`, `finish_reason="stop"`, reporting their permanent aliases.
   - Both `/metrics` endpoints confirmed `"version": "0.1.67"`, `"drafting": "dflash2"`, `"prefill_cap": 8192`, `"expert_slots": 5587`, `"vram_free_mib": 915`, `drafts_offered=26`, `drafts_accepted=21`, and `hit_rate=0.64`.
   - GPU telemetry during smoke: `15367 MiB` VRAM used on both GPUs, `150.00 W` limits, `1245 MHz` clock policy active, `40 / 43 °C`.
4. **Clean Stop at Rest & Unit Tests (`tests/test_p520_serving.py`)**:
   - Stopped both containers cleanly (`docker stop -t 30 p520-llm-a p520-llm-b`), confirmed `Exited (0)` and `0 MiB` VRAM used on both GPUs (`150.00 W`, `v100-clock-lock.service` active).
   - `tests/test_p520_serving.py`: `7/7` passed on both ThinkPad and P520.

## Rollback

- Stop `S12-C1T` serving: `ssh p520 'docker stop -t 30 p520-llm-a p520-llm-b'`
- Restore preserved `S11X-D2` pair (`s11x-d2-20261119T095616`): rename `p520-llm-{a,b}` to archive/rollback names and rename `p520-llm-{a,b}-archive-s11x-d2-20261119T095616` back to `p520-llm-{a,b}`.
- Older `S10-D4` archive (`p520-llm-{a,b}-archive-s10-d4-20261111T012331`) also remains preserved on P520.
