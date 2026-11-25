#!/usr/bin/env python3
"""Stage 12 P520 Docker build + ISA / cuobjdump / CPU & GPU parity gate verifier."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import socket
import subprocess as sp

PINS = {
    "0.1.66": ("Niko1221/Strata", "a34979fc94f3d126b9bb8210f4ad311345688b52", "0.1.66"),
    "0.1.67": ("Niko1221/Strata", "d46f5f268f8ed797e83a5c63a69bffbd7a581cf6", "0.1.67"),
}

MANDATORY_CTESTS_CPU = (
    "isa_guard_check|no_mmq_symbols|"
    "native_arithmetic_parity|native_arithmetic_parity_avx|native_arithmetic_parity_mt1|"
    "native_arithmetic_parity_no512|native_arithmetic_parity_ggml|"
    "pool_determinism|pool_determinism_dep_off|iq_avx2_parity|iq_avx1_parity|"
    "q8k_quant_parity|q2_bitplane_parity|quant_selftest|quant_parity|"
    "nv_defaults_test|tail_skip_default_test|lookup_default_test|adapt_async_default_test|"
    "cgroup_mem_test|cgroup_cpu_test|file_expert_source_test"
)

MANDATORY_CTESTS_GPU = (
    "native_expert_parity_v31_iq2_xxs_q2_0|native_expert_parity_v31_iq2_xs_q2_0|"
    "native_expert_parity_v31_iq2_s_q2_0|native_expert_parity_v31_iq3_xxs_q2_0|"
    "native_expert_parity_v31_iq2_xxs_iq4_nl|native_expert_parity_v31_iq2_xs_iq4_nl|"
    "native_expert_parity_v31_iq2_s_iq4_nl|native_expert_parity_v31_iq3_xxs_iq4_nl|"
    "native_i8_parity|native_grouped_parity|native_multi_parity|pf_wmma_parity|"
    "qsa_merge_daily_parity_default|qsa_merge_daily_parity_daily"
)

# Pass explicit bounded dimensions (ctx=8192, nq=512, reps=2) to qsa_prompt_attn_parity;
# bare invocation defaults to 32768x2048x5 which can trigger a P520 PSU trip.
DIRECT_GPU_EXES = (
    ("qsa_prompt_attn_parity", ["8192", "512", "2"]),
    ("dflash2_q4_parity", []),
)


def run(*args, timeout=600) -> str:
    return sp.check_output(args, text=True, stderr=sp.STDOUT, timeout=timeout)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", required=True, choices=PINS)
    p.add_argument("--tag", required=True)
    p.add_argument("--patch", default="", help="Patch filename under docker/patches/")
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--skip-gpu-tests", action="store_true")
    p.add_argument("--extra-ctest-regex", default="")
    args = p.parse_args()

    assert socket.gethostname() == "p520-llm", "Must run on p520-llm"
    assert not run("docker", "ps", "-q").strip(), "Running container found; aborting build/parity"
    assert sp.run(["docker", "image", "inspect", args.tag], capture_output=True).returncode != 0, f"Image exists: {args.tag}"

    repo, revision, version = PINS[args.version]
    root = Path(__file__).resolve().parents[1]
    args.out.mkdir(parents=True, exist_ok=False)

    cmd = [
        "docker", "build", "-f", str(root / "Dockerfile.stage12"), "-t", args.tag,
        "--build-arg", f"STRATA_REPO={repo}",
        "--build-arg", f"STRATA_REF={revision}",
        "--build-arg", f"STRATA_VERSION={version}",
        "--build-arg", f"STAGE12_PATCH={args.patch}",
        str(root),
    ]
    record = {
        "version": version, "revision": revision, "tag": args.tag, "patch": args.patch or None,
        "started": dt.datetime.now().astimezone().isoformat(), "command": cmd, "phase": "building",
    }
    (args.out / "progress.json").write_text(json.dumps(record, indent=2) + "\n")

    with (args.out / "build.log").open("w") as log:
        rc = sp.run(cmd, stdout=log, stderr=sp.STDOUT, timeout=7200).returncode
    assert rc == 0, f"Docker build failed with rc={rc}"

    info = json.loads(run("docker", "image", "inspect", args.tag))[0]
    image_id = info["Id"]
    record["image_id"] = image_id

    # Provenance & cuobjdump sm_70 verification (CPU-only container)
    probe_script = (
        "cat /opt/strata/engine/BUILD.json && echo '---SHA---' && "
        "sha256sum /opt/strata/engine/strata && echo '---NVCC---' && nvcc --version && "
        "echo '---CUOBJDUMP_ARCH---' && cuobjdump --list-elf /opt/strata/engine/strata | head -n 40 && "
        "echo '---LDD---' && ldd /opt/strata/engine/strata"
    )
    prov = run("docker", "run", "--rm", "--network", "none", "--entrypoint", "/bin/bash", image_id, "-euc", probe_script)
    (args.out / "provenance.txt").write_text(prov)
    assert "sm_70" in prov, "sm_70 cubin missing from binary"

    build_meta = json.loads(run("docker", "run", "--rm", "--network", "none", "--entrypoint", "cat", image_id, "/opt/strata/engine/BUILD.json"))
    record["binary_sha256"] = build_meta["binary_sha256"]

    # Run CPU-only ctest suite (strictly refuse skipped tests on mandatory suite)
    cpu_regex = f"^({MANDATORY_CTESTS_CPU})$"
    if args.extra_ctest_regex:
        cpu_regex = f"^({MANDATORY_CTESTS_CPU}|{args.extra_ctest_regex})$"

    ctest_cpu_cmd = [
        "docker", "run", "--rm", "--network", "none", "--entrypoint", "/bin/bash", image_id, "-euc",
        f"cd /opt/strata && /opt/strata/.venv/bin/ctest --test-dir /opt/strata/build-stage12 --output-on-failure -j 6 -R '{cpu_regex}'"
    ]
    cpu_out = run(*ctest_cpu_cmd, timeout=1800)
    # Also audit strata_pf_own CUDA spills directly (upstream cuda_spill_guard skips sm_70 due to stub libstrata_pf_fp4.a)
    spill_cmd = [
        "docker", "run", "--rm", "--network", "none", "--entrypoint", "/bin/bash", image_id, "-euc",
        "cd /opt/strata && /opt/strata/.venv/bin/python tools/check_cuda_spills.py --cuobjdump /usr/local/cuda/bin/cuobjdump /opt/strata/build-stage12/libstrata_pf_own.a || true"
    ]
    cpu_out += "\n=== pf_own_spill_audit ===\n" + run(*spill_cmd, timeout=300)
    (args.out / "ctest-cpu.log").write_text(cpu_out)
    assert "0 tests failed" in cpu_out and "Skipped" not in cpu_out and "Not Run" not in cpu_out, f"CPU ctest check failed:\n{cpu_out}"

    if not args.skip_gpu_tests:
        assert not run("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader").strip(), "GPU busy before parity"
        gpu_regex = MANDATORY_CTESTS_GPU + ("|gr_write_norm_parity" if version == "0.1.67" else "")
        ctest_gpu_cmd = [
            "docker", "run", "--rm", "--network", "none", "--gpus", "device=0",
            "--entrypoint", "/bin/bash", image_id, "-euc",
            f"cd /opt/strata && /opt/strata/.venv/bin/ctest --test-dir /opt/strata/build-stage12 --output-on-failure -R '^({gpu_regex})$'"
        ]
        gpu_out = run(*ctest_gpu_cmd, timeout=1800)
        for exe, exe_args in DIRECT_GPU_EXES:
            exe_cmd = [
                "docker", "run", "--rm", "--network", "none", "--gpus", "device=0",
                "--entrypoint", f"/opt/strata/build-stage12/{exe}", image_id, *exe_args,
            ]
            gpu_out += f"\n=== {exe} {' '.join(exe_args)} ===\n" + run(*exe_cmd, timeout=600)
        (args.out / "ctest-gpu.log").write_text(gpu_out)
        assert "0 tests failed" in gpu_out and "Skipped" not in gpu_out and "Not Run" not in gpu_out, f"GPU ctest failed:\n{gpu_out}"

    record.update(phase="results_saved", verdict="BUILD_AND_PARITY_PASS", finished=dt.datetime.now().astimezone().isoformat())
    (args.out / "progress.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
