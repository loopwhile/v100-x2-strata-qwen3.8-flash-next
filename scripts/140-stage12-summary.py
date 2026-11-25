#!/usr/bin/env python3
"""Generate Stage 12 aggregate summary.md across all completed candidate receipts."""
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    art_dir = root / "artifacts/stage12-results-20261125"
    cand = json.loads((root / "bench/stage12-candidates.json").read_text())

    lines = [
        "# Stage 12 Campaign Results Summary",
        "",
        "| Candidate | Gate | Engine / Patch | Raw ID | Prefill A / B (tok/s) | Decode A / B (tok/s) | TTFT A / B (s) | Status |",
        "|---|---|---|---|---:|---:|---:|---|",
        "| `S11X-D2` (Ref) | Ref | `0.1.59` + `stage11x-d2.patch` | `d2-20261119T003753` | `1032.6 / 1037.0` | `37.1 / 41.0` | `123.21 / 122.69` | Prior Promoted |",
    ]
    for cid, meta in cand.get("candidates", {}).items():
        if cid.startswith("S12-A"):
            continue
        p = meta.get("prefill_tok_s_A_B") or meta.get("diag_prefill_tok_s_A_B")
        d = meta.get("decode_tok_s_A_B") or meta.get("diag_decode_tok_s_A_B")
        t = meta.get("ttft_s_A_B") or meta.get("diag_ttft_s_A_B")
        p_s = f"{p[0]:.1f} / {p[1]:.1f}" if p else "—"
        d_s = f"{d[0]:.1f} / {d[1]:.1f}" if d else "—"
        t_s = f"{t[0]:.2f} / {t[1]:.2f}" if t else "—"
        eng = meta.get("engine", "0.1.67")
        if meta.get("patch"):
            eng += f" + `{Path(meta['patch']).name}`"
        raw = meta.get("raw_id", "—")
        lines.append(f"| `{cid}` | {meta.get('gate', '?')} | {eng} | `{raw}` | {p_s} | {d_s} | {t_s} | {meta.get('status')} |")

    out_path = art_dir / "summary.md"
    out_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
