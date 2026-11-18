# Stage 11 — S10-D4 recipe on Qwen3.8-Flash-Next IQ3_S (COMPLETED / CLOSED — 2026-11-19)

**Status: COMPLETED / CLOSED (2026-11-19 KST).** `S11-D4` (`d4-20261119T025044`) completed 1 startup smoke + 3/3 valid concurrent 128K C2 batches (`PASS`), backed up with SHA-256 verification. See [Stage 11 summary](../artifacts/stage11-results-20261119/summary.md) and [receipt](../artifacts/stage11-results-20261119/d4-20261119T025044/report.md). All Stage 11 IDs are CLOSED; do not rerun or reuse them.

## Executed Outcome (`d4-20261119T025044`)

- **Medians (3 batches)**: Prefill A/B **893.8 / 898.0** tok/s, Decode A/B **23.3 / 23.4** tok/s, TTFT A/B **142.30 / 141.69** s.
- **vs Historical `S6-0` (`IQ3_S`, 22.3 / 21.2 decode)**: +1.0 / +2.2 tok/s decode improvement, while dual-agent 30 tok/s was NOT MET on `IQ3_S` (expert hit rate `0.751–0.794` and ~`47.8 GiB / 51.05 GiB` Shard 1 OS page-cache ceiling).

## Scope & Single Candidate (`S11-D4`)

| Item | Value |
| --- | --- |
| **Candidate ID** | `S11-D4` |
| **Target Model** | `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S` (`/srv/models/strata-iq3s`) |
| **Engine Image** | Upstream Strata `0.1.59` (`sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`, binary SHA256 `ccca4882...`) |
| **Drafter** | Stock DFlash2 (`qwen3.8-flash-next-dflash2.q4_0-selq4.pack`, SHA256 `4a42b982...`), `--draft-fallback none` (no MTP) |
| **D4 Recipe Flags** | `--spec 8 --draft-conf 0.7 --prefill auto --max-context 131072 --kv int8 --kv-resident 32768 --expert-cache auto --mmap-experts` |
| **Volta Env** | `STRATA_SELECT_SIMT=1`, `STRATA_SM70_TABLE=1`, `STRATA_PF_WMMA=1` |
| **Topology** | Independent GPU0/A (`0-2,6-8`, test port `18088`) and GPU1/B (`3-5,9-11`, test port `18089`) |
| **Host Policy** | Preserve 150 W GPU limits and `135–1245 MHz` `v100-clock-lock.service`; no host changes |
| **Workload** | Frozen C2 128K (`v100-performance-v1.json`, `e413acced27c...`), 1 startup smoke + 3 fresh concurrent scored batches |

## Historical Context (Non-Causal Reference Only)

- **IQ3_S historical reference (`S6-0`, engine `0.1.47` fork + MTP, 1110 MHz envelope):** Prefill A/B `908.2 / 923.1` tok/s, Decode A/B `22.3 / 21.2` tok/s, TTFT `140.09 / 137.84` s.
- **IQ3_XXS `S10-D4` reference (`0.1.59` + stock DFlash2, 1245 MHz envelope):** Prefill A/B `1025.1 / 1027.8` tok/s, Decode A/B `30.4 / 30.3` tok/s, TTFT `124.08 / 123.79` s.
- `IQ3_S` GGUF shards total ~77.9 GiB (`54.82 GB + 28.80 GB`) vs ~70.6 GiB for `IQ3_XXS` on 64 GB host RAM, so host page-cache residency, file-tier I/O, and VRAM expert-cache slot count under DFlash2 (`~715 MiB` vs MTP `~1082 MiB`) must be observed directly in `S11-D4`.

## Safety & Preservation Contract

1. Keep stopped serving containers `p520-llm-a` / `p520-llm-b` and all historical containers/images/results untouched.
2. Keep `/srv/models/strata-iq3xxs` and `/srv/models/strata-data` untouched alongside restored `/srv/models/strata-iq3s`.
3. Do not mutate P520 power limits, clocks, BIOS, tunnel (`18080/18081`), or production ports (`8080/8081`).
4. Require clean `128-stage11-prepare.py` gate before any authorized `129-stage11-c2.py` execution.
