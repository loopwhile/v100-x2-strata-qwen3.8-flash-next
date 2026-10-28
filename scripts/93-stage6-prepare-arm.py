#!/usr/bin/env python3
"""Create NEW, isolated Stage 6 experiment configs; never edit baseline or live containers."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/stage6-configs-20261028/iq3s"
ARMS = ROOT / "results/stage6/arms"
NAMES = ("strata-s6-iq3s-agent-a", "strata-s6-iq3s-agent-b")
ALLOWED_ENV = {
    "STRATA_DECODE_TIMING", "STRATA_VERIFY_PROFILE",
    "STRATA_SIDE_MIXER", "STRATA_GU_SWIGLU", "STRATA_GR_UP75",
    "STRATA_ATTN_DAILY", "STRATA_GR_NORM_FAST", "STRATA_ARGMAX_ROWS_SM70",
    "STRATA_Q8_GATHER_WIDE", "STRATA_GDN_REC_WARP", "STRATA_SM70_TABLE",
    "STRATA_EXPDEC", "STRATA_ADAPT_OVERLAP", "STRATA_FUSE_DECODE",
    "STRATA_QSA_ROWS", "STRATA_QIL", "STRATA_B6_MMVQ_ROWS", "STRATA_GR_DOWN_TG",
}
PINNED_ARGS = {"--max-context": "131072", "--kv": "int8"}


def update_arg(args: list[str], flag: str, value: object) -> None:
    if value is None:
        return
    val = str(value)
    if flag in args:
        at = args.index(flag)
        if at + 1 >= len(args):
            raise ValueError(f"missing baseline value after {flag}")
        args[at + 1] = val
    else:
        args.extend([flag, val])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--id", required=True, help="unique arm id, e.g. s6-2-spec6-p05")
    ap.add_argument("--spec", type=int, choices=(4, 6, 8))
    ap.add_argument("--min-p", type=float)
    ap.add_argument("--kv-resident", type=int)
    ap.add_argument("--expert-cache", help="auto or positive integer expert slots")
    ap.add_argument("--pool-workers", type=int)
    ap.add_argument("--pcie-frac", type=float)
    ap.add_argument("--env", action="append", default=[], metavar="KEY=VALUE")
    ns = ap.parse_args()

    if not re.fullmatch(r"s6-[a-z0-9][a-z0-9-]{0,55}", ns.id):
        ap.error("--id must match s6-[a-z0-9][a-z0-9-]{0,55}")
    if ns.min_p is not None and not 0.0 <= ns.min_p <= 1.0:
        ap.error("--min-p must be 0..1")
    if ns.kv_resident is not None and ns.kv_resident not in (16384, 24576, 32768):
        ap.error("--kv-resident: use 16384/24576/32768 only (128K context remains fixed)")
    if ns.expert_cache is not None and ns.expert_cache != "auto":
        if not ns.expert_cache.isdecimal() or int(ns.expert_cache) <= 0:
            ap.error("--expert-cache must be auto or positive slot count")
    if ns.pool_workers is not None and not 1 <= ns.pool_workers <= 6:
        ap.error("--pool-workers must be 1..6 within existing CPU affinity")
    if ns.pcie_frac is not None and not 0.0 <= ns.pcie_frac <= 1.0:
        ap.error("--pcie-frac must be 0..1")

    env: dict[str, str] = {}
    for item in ns.env:
        if "=" not in item:
            ap.error("--env requires KEY=VALUE")
        k, v = item.split("=", 1)
        if k not in ALLOWED_ENV:
            ap.error(f"unapproved Stage 6 flag: {k}")
        if k in env:
            ap.error(f"duplicate Stage 6 flag: {k}")
        if not re.fullmatch(r"[0-9]+", v):
            ap.error("Stage 6 experimental env values must be non-negative integers")
        env[k] = v

    changes = any((
        ns.spec is not None, ns.min_p is not None, ns.kv_resident is not None,
        ns.expert_cache is not None, ns.pool_workers is not None,
        ns.pcie_frac is not None, bool(env),
    ))
    if not changes:
        ap.error("no experimental parameter provided; S6-0 baseline already exists")

    # Validate source BEFORE creating a new arm, and keep its bytes immutable in this script.
    configs = []
    source_hashes: dict[str, str] = {}
    for name in NAMES:
        source = BASE / f"{name}.json"
        raw = source.read_bytes()
        cfg = json.loads(raw)
        assert cfg["args"][cfg["args"].index("--max-context") + 1] == "131072"
        assert cfg["args"][cfg["args"].index("--kv") + 1] == "int8"
        assert "--mmap-experts" in cfg["args"]
        configs.append(cfg)
        source_hashes[name] = hashlib.sha256(raw).hexdigest()

    for cfg in configs:
        args = cfg["args"]
        update_arg(args, "--spec", ns.spec)
        update_arg(args, "--spec-min-p", ns.min_p)
        update_arg(args, "--kv-resident", ns.kv_resident)
        update_arg(args, "--expert-cache", ns.expert_cache)
        update_arg(args, "--pool-workers", ns.pool_workers)
        update_arg(args, "--pcie-frac", ns.pcie_frac)
        assert args[args.index("--max-context") + 1] == PINNED_ARGS["--max-context"]
        assert args[args.index("--kv") + 1] == PINNED_ARGS["--kv"]
    assert configs[0]["args"] == configs[1]["args"]

    target = ARMS / ns.id
    target.mkdir(parents=True, exist_ok=False)
    for name, cfg in zip(NAMES, configs):
        (target / f"{name}.json").write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    (target / "experimental-flags.env").write_text(
        "".join(f"{k}={v}\n" for k, v in sorted(env.items())), encoding="utf-8"
    )
    (target / "arm.json").write_text(
        json.dumps({
            "arm": ns.id, "status": "PREPARED_NOT_EXECUTED",
            "source_configs_sha256": source_hashes, "args": configs[0]["args"],
            "experimental_env": env,
            "fixed_image": "strata-v100-jmnargi:2c9b1dd",
            "frozen_context": 131072, "kv": "int8",
            "note": "identical A/B recipe; never rewrite committed baseline",
        }, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared arm (no Docker actions): {target}")
    print(f"Start after stopping/removing STAGE-6-ONLY objects: "
          f'STRATA_S6_ARM_DIR="{target}" bash scripts/88-start-stage6-agents.sh both')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
