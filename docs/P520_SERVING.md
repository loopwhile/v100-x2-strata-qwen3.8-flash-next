# P520 stable serving pair

The user initially selected **S10-D4** on 2026-11-11 (`s10-d4-20261111T012331`) and
promoted **`S11X-D2`** on 2026-11-19 (`s11x-d2-20261119T095616`): pinned Strata `0.1.59`
patched with [stage11x-d2.patch](../docker/patches/stage11x-d2.patch), IQ3_XXS, stock
DFlash2, `--spec 8 --draft-conf 0.7 --prefill auto`.
The operating names and API model IDs are independent of the engine version.
Both promoted servers are deployed, verified live, and running from release
`s11x-d2-20261119T095616`; see
[2026-11-19 deployment verification](../artifacts/p520-serving-20261119/summary.md)
(initial 2026-11-11 `S10-D4` deployment notes are preserved in
[2026-11-11 summary](../artifacts/p520-serving-20261111/summary.md)).

| Contract | Agent A | Agent B |
| --- | --- | --- |
| Container name / API model ID | `p520-llm-a` | `p520-llm-b` |
| Physical GPU | GPU0 | GPU1 |
| CPU affinity | `0-2,6-8` | `3-5,9-11` |
| P520 listener | `127.0.0.1:8080` | `127.0.0.1:8081` |
| ThinkPad base URL | `http://127.0.0.1:18080/v1` | `http://127.0.0.1:18081/v1` |
| Context / KV | 131072 / INT8, 32768 resident | 131072 / INT8, 32768 resident |

The existing ThinkPad `strata-tunnel.service` is unchanged. Containers use host
networking with loopback listeners, matching D4's network mode. Docker's PORTS
column can therefore be empty. Restart policy is `unless-stopped`.

Client model IDs are native server **aliases**. Internally the canonical names
are `qwen3.8-flash-next-iq3_xxs_p520_a/b`, because the unmodified server uses the
Qwen model-name pattern to select DFlash2. `/health` reports the canonical name;
`/v1/models` lists the canonical name and the stable alias. Responses to a
request using `p520-llm-a/b` report that same alias. This separates client names
from model-family detection without patching the engine or server.

## Daily commands from ThinkPad

```bash
# Start both and wait for health, model IDs and the effective D4 engine flags.
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && python3 scripts/127-p520-serving.py start'

# State, including stopped containers.
ssh p520 'docker ps -a --filter name=p520-llm-'

# Stop; retain the containers and all release files.
ssh p520 'docker stop -t 30 p520-llm-a p520-llm-b'

# Logs (A; substitute b for B).
ssh p520 'docker logs --tail 100 -f p520-llm-a'

# Full configuration and health checks without inference.
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && python3 scripts/127-p520-serving.py check'

# Unchanged tunnel service.
systemctl --user status strata-tunnel
```

On P520 itself, `docker start p520-llm-a p520-llm-b` also works. Allow model
loading to finish before sending requests. Each endpoint is an independent
single-GPU agent.

## Fixed client configuration

OpenCode provider keys remain `p520-a` and `p520-b`. Its default model becomes
`p520-a/p520-llm-a`; the other selection is `p520-b/p520-llm-b`.
Only the initial migration changes client model selections. Later compatible
engine updates retain these IDs and URLs, so clients need no version edits.
Existing saved sessions that explicitly selected the historical model should
select the new stable model once.

OpenAI-compatible request example:

```json
{
  "model": "p520-llm-a",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 128
}
```

## Versioned implementation and rollback

Active `S11X-D2` image ID (`strata-v100:stage11x-d2`):
`sha256:26d2bbfe67bc7cb4e489e6f9283e22bb4cd59c6e9659abf3396caa4f1a4f7f38`.
Base source: `712fec6b4297c9cfd32ab43daaa2979a9aa01edf` + [stage11x-d2.patch](../docker/patches/stage11x-d2.patch).
Engine SHA256: `7f6fc8f7858739d18b177911d32d0d832393274b4ba7797dfd3cf29e634e76a9`.
The 19 verified `S11X-D2` environment overrides are:
- Baseline D4: `STRATA_SELECT_SIMT=1`, `STRATA_SM70_TABLE=1`, `STRATA_PF_WMMA=1`
- P1 Volta prefill: `STRATA_PF_WMMA2=1`, `STRATA_PF_WMMA_LEAN=1`, `STRATA_PF_WMMA_SKINNY=1`
- D1 CPU `PathC7`: `STRATA_AVX512BW_IQ=22`, `STRATA_IQ_MT_MIN=1`, `STRATA_IQ_GATHER=1`, `STRATA_IQ256_GATHER=1`, `STRATA_Q2_BITPLANE=1`
- D2 Sync/Cache & `nv_defaults`: `STRATA_SIDE_MIXER=2`, `STRATA_ATTN_DAILY=1`, `STRATA_GR_UP75=1`, `STRATA_GU_SWIGLU=1`, `STRATA_QSA_ROWS=1`, `STRATA_FUSE_WAIT=2`, `STRATA_MMAP_ADAPT_ASYNC=1`, `STRATA_COLD_OVERLAP=5`

Disallowed / rejected overrides (`STRATA_ADAPT_LAG`, `STRATA_ADAPT_NOWAIT`, `STRATA_PF_HC_REGION`, `STRATA_AUX_CPUS`) remain absent. DFlash2 is active without an MTP drafter or fallback; the original shared MTP mount remains available for the draft vocabulary.

Preserved rollback `S10-D4` release (`s10-d4-20261111T012331`, containers `p520-llm-{a,b}-archive-s10-d4-20261111T012331`):
image `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`, engine SHA256 `ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031`.

`results/p520-serving/releases/<release>/` keeps separate JSON configurations,
logs, exact create commands, image/config hashes, initial preflight and a
rollback file. Original D4 files are read and copied; never edited or rerun.
The helper's `prepare` and `install --release <path>` commands create a new
release and **stopped** containers. They refuse an occupied stable name or
foreign running workloads. `start` is separate.

Future upgrades should build/pin a new versioned image, prepare a new release,
and validate compatibility. In an approved maintenance window, stop and rename
only these owned operating containers to unique archive names, then create the
replacement pair under `p520-llm-a/b`. Keep their API IDs/ports fixed. Preserve
the previous image, configs and containers so rollback can restore the previous
names and start the old pair. The current helper pins `S11X-D2` and deliberately
refuses a different image; update its verified contract with an approved upgrade.
Do not install a new engine by mutating files inside an existing container.

Stop active `S11X-D2` serving:

```bash
ssh p520 'docker stop -t 30 p520-llm-a p520-llm-b'
```

Full rollback to the preserved `S10-D4` pair (only if needed):

```bash
ssh p520 '
docker stop -t 30 p520-llm-a p520-llm-b
docker rename p520-llm-a p520-llm-a-rollback-s11x-d2
docker rename p520-llm-b p520-llm-b-rollback-s11x-d2
docker rename p520-llm-a-archive-s10-d4-20261111T012331 p520-llm-a
docker rename p520-llm-b-archive-s10-d4-20261111T012331 p520-llm-b
'
```

ThinkPad OpenCode files are backed up next to the originals before the one-time
model-ID update. Restore those backups only if reverting the client migration.
Historical serving/experiment containers, images, model assets, experiment IDs,
GPU power/clock policies and the SSH tunnel are preserved. This deployment uses
health checks and short API smoke requests; it runs no archived C2 benchmark
and makes no additional throughput or semantic-quality claim.
