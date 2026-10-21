# Stage 4-0 Inventory & Reproducibility Receipt

- **Date / Time**: 2026-10-21 21:42:00 KST
- **ThinkPad E14 Workspace**: `~/Data/Workspace_VSCode/v100-x2-strata-qwen3.8-flash-next`
- **ThinkPad Git Commit**: `752844f5c70b6fb38f60dbc233a8e8cde131048d` (clean)
- **P520 Git Commit**: `752844f5c70b6fb38f60dbc233a8e8cde131048d` (synchronized via `git pull --ff-only`, clean)

---

## 1. Host System Environment (ThinkStation P520)

| Item | Value |
| --- | --- |
| OS / Kernel | Linux 7.0.0-38-generic #38-Ubuntu SMP PREEMPT_DYNAMIC x86_64 GNU/Linux |
| CPU | Intel(R) Xeon(R) W-2135 CPU @ 3.70GHz (6C / 12T, 1 socket, NUMA node0: CPUs 0-11) |
| System RAM | 61 GiB total (1.5 GiB used, 19 GiB free, 59 GiB available) |
| Swap | 4.0 GiB total, 0 B used |
| Root Disk (`/dev/nvme0n1p2`) | 233 GiB total, 65 GiB used, 157 GiB available (30% usage) |
| NVIDIA Driver | 580.178.04 |
| CUDA Version (Driver) | 13.0 |
| GPU 0 | Tesla V100-SXM2-16GB, Bus-Id `0000:65:00.0`, Temp 43°C, Power 26W / 150W (Unchanged) |
| GPU 1 | Tesla V100-SXM2-16GB, Bus-Id `0000:B3:00.0`, Temp 37°C, Power 26W / 150W (Unchanged) |
| Persistence Mode | Enabled (`On` on both GPUs) |

---

## 2. Docker Containers & Images Audit

### Existing Preserved Images
| Repository:Tag | Image ID | Content Size | Created / Revision |
| --- | --- | --- | --- |
| `strata-v100-jmnargi:9d77749` | `sha256:a67a09cedf08d61e5f76fcc2f4b196207e6fa9cc44a01c17fe914646a4289e9e` | 5.91 GB | `9d7774919e26d235359bc2c3001f61f607eb288d` |

### Existing Agent Containers
| Container Name | Container ID | Status | GPU | CpusetCpus | Port Binding | Mounted Config |
| --- | --- | --- | --- | --- | --- | --- |
| `strata-jmn-iq2xs-agent-a` | `9546cb655108` | `exited (0)` | Device ID `0` | `0-2,6-8` | `127.0.0.1:8080:8080/tcp` | `/srv/models/strata-iq2xs/config/strata-jmn-iq2xs-agent-a.json` |
| `strata-jmn-iq2xs-agent-b` | `3b489b7140d1` | `exited (0)` | Device ID `1` | `3-5,9-11` | `127.0.0.1:8081:8080/tcp` | `/srv/models/strata-iq2xs/config/strata-jmn-iq2xs-agent-b.json` |

*Note: Containers were exited cleanly at 2026-10-21 21:16 KST (`FinishedAt: 2026-10-21T12:16:08Z`, ExitCode: 0).*

---

## 3. ThinkPad Local Tunnel Status

- **Service**: `strata-tunnel.service` (`systemctl --user status strata-tunnel`)
- **Status**: `active (running)`
- **Ports Forwarded**:
  - `127.0.0.1:18080` -> P520 `127.0.0.1:8080`
  - `127.0.0.1:18081` -> P520 `127.0.0.1:8081`

---

## 4. Frozen Asset & Manifest Verification

| Asset | Expected SHA-256 | Live / Repository SHA-256 | Verification Status |
| --- | --- | --- | --- |
| C2 Workload (`bench/workloads/v100-performance-v1.json`) | `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca` | `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca` | **MATCH** |
| Agent A Config (`strata-jmn-iq2xs-agent-a.json`) | `7b4ad01d3e87c58d2854c6adbc850dad0131e9b6124b28344a3ca30c2c950180` | `7b4ad01d3e87c58d2854c6adbc850dad0131e9b6124b28344a3ca30c2c950180` | **MATCH** |
| Agent B Config (`strata-jmn-iq2xs-agent-b.json`) | `9ef62aaf0c902e46cd1234f0709d81fe7248c7a73b7d2941aff28ccb8af63363` | `9ef62aaf0c902e46cd1234f0709d81fe7248c7a73b7d2941aff28ccb8af63363` | **MATCH** |

---

## 5. Model & Shared Storage Integrity

- Model Directory: `/srv/models/strata-iq2xs/model`
  - `Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf` (39,225,954,592 bytes)
  - `Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf` (28,800,138,432 bytes)
- Native Pack: `/srv/models/strata-iq2xs/pack/iq2_xs-native`
- Shared MTP: `/srv/models/strata-data/mtp/rt` & `mtp-q2_0.gguf` (889,017,216 bytes)

**Gate 4-0 Passed**: All baseline components, configs, and integrity hashes match expectations. No existing containers or images were modified.
