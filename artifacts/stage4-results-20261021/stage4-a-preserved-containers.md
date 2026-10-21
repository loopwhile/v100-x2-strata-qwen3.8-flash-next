# Stage 4-A Preserved Containers Inventory

- **Status**: Exited (0) (Preserved without removal for potential future reuse)
- **Stopped At**: 2026-10-21 22:05:36 KST
- **Image**: `strata-v100-upstream:0.1.44.1` (`sha256:56fd71f0ddfe7c702df76371358252fb59407cad821b0f7e52e027054ec7ae93`)

---

## 1. Agent A (`strata-s4a-iq2xs-agent-a`)

- **Container ID**: `202918be49c9bc86ecbc87507ad158c617507e0f1ed5e876ff40cd1945986d04`
- **Host GPU**: Device ID `0` (`--gpus '"device=0"'`)
- **CPU Affinity**: `0-2,6-8`
- **Port Mapping**: Host `127.0.0.1:8080` -> Container `8080/tcp`
- **Mounted Config**: `/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/artifacts/stage4-configs-20261021/iq2xs/strata-s4a-iq2xs-agent-a.json:/opt/strata/config.json:ro`
- **Binds**:
  - `/srv/models/strata-iq2xs:/iq2:ro`
  - `/srv/models/strata-iq2xs/logs:/iq2-logs`
  - `/srv/models/strata-data/mtp:/shared-mtp:ro`
- **Cmd**:
  ```bash
  /opt/strata/.venv/bin/python /opt/strata/serve/server.py --engine strata --config /opt/strata/config.json --host 0.0.0.0 --port 8080
  ```

---

## 2. Agent B (`strata-s4a-iq2xs-agent-b`)

- **Container ID**: `3d7a4c17005cd5385d45ee55b39cc8b5d53ab92551bebd7d454fd3547071b3cb`
- **Host GPU**: Device ID `1` (`--gpus '"device=1"'`)
- **CPU Affinity**: `3-5,9-11`
- **Port Mapping**: Host `127.0.0.1:8081` -> Container `8080/tcp`
- **Mounted Config**: `/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/artifacts/stage4-configs-20261021/iq2xs/strata-s4a-iq2xs-agent-b.json:/opt/strata/config.json:ro`
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
ssh p520 'docker start strata-s4a-iq2xs-agent-a strata-s4a-iq2xs-agent-b'
```
