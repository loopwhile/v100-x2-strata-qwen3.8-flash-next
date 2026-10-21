# Stage 4-C Preserved Containers Inventory

- **Status**: Exited (0) (Preserved without removal for potential future reuse)
- **Stopped At**: 2026-10-21 22:32:06 KST
- **Image**: `strata-v100-upstream:0.1.47` (`sha256:19c3b72a1097486eeae3fd9b964179a36a1c137615e5c93f6d6e70eacdab8e9d`)
- **Tuning Flag**: `STRATA_SM70_TABLE=1`

---

## 1. Agent A (`strata-s4c-iq2xs-agent-a`)

- **Container ID**: `a2d51a2c2b63a6a29105103cd66ff35157d9245e28ba761b68b5f660f3e5687d`
- **Host GPU**: Device ID `0` (`--gpus '"device=0"'`)
- **CPU Affinity**: `0-2,6-8`
- **Port Mapping**: Host `127.0.0.1:8080` -> Container `8080/tcp`
- **Env**: `STRATA_SM70_TABLE=1`, `STRATA_EXECV=1`
- **Mounted Config**: `/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/artifacts/stage4-configs-20261021/iq2xs/strata-s4c-iq2xs-agent-a.json:/opt/strata/config.json:ro`
- **Binds**:
  - `/srv/models/strata-iq2xs:/iq2:ro`
  - `/srv/models/strata-iq2xs/logs:/iq2-logs`
  - `/srv/models/strata-data/mtp:/shared-mtp:ro`
- **Cmd**:
  ```bash
  /opt/strata/.venv/bin/python /opt/strata/serve/server.py --engine strata --config /opt/strata/config.json --host 0.0.0.0 --port 8080
  ```

---

## 2. Agent B (`strata-s4c-iq2xs-agent-b`)

- **Container ID**: `b19b291ebfd527cc1b28a0e962044309eb62a75dca9bec57badc1759338fa82a`
- **Host GPU**: Device ID `1` (`--gpus '"device=1"'`)
- **CPU Affinity**: `3-5,9-11`
- **Port Mapping**: Host `127.0.0.1:8081` -> Container `8080/tcp`
- **Env**: `STRATA_SM70_TABLE=1`, `STRATA_EXECV=1`
- **Mounted Config**: `/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/artifacts/stage4-configs-20261021/iq2xs/strata-s4c-iq2xs-agent-b.json:/opt/strata/config.json:ro`
- **Binds**:
  - `/srv/models/strata-iq2xs:/iq2:ro`
  - `/srv/models/strata-iq2xs/logs:/iq2-logs`
  - `/srv/models/strata-data/mtp:/shared-mtp:ro`
- **Cmd**:
  ```bash
  /opt/strata/.venv/bin/python /opt/strata/serve/server.py --engine strata --config /opt/strata/config.json --host 0.0.0.0 --port 8080
  ```

---

## 3. Reuse / Start Command

언제든 필요 시 아래 명령으로 바로 재시작하여 사용할 수 있습니다:
```bash
ssh p520 'docker start strata-s4c-iq2xs-agent-a strata-s4c-iq2xs-agent-b'
```
