#!/usr/bin/env python3
from pathlib import Path

p = Path("/opt/strata/src/kernels/cuda/qsa_prompt_attn.cu")
s = p.read_text(encoding="utf-8")

old = """        static int cc_major[64] = {};
        int dev = 0;
        if (cudaGetDevice(&dev) != cudaSuccess || dev < 0 || dev >= 64) { cudaGetLastError(); return false; }
        if (cc_major[dev] == 0) {
            int major = 0;
            if (cudaDeviceGetAttribute(&major, cudaDevAttrComputeCapabilityMajor, dev) != cudaSuccess) {
                cudaGetLastError();
                return false;
            }
            cc_major[dev] = major;
        }
        if (cc_major[dev] < 7) return false;
        turing = cc_major[dev] < 8;
"""

new = """        static int cc[64] = {};
        int dev = 0;
        if (cudaGetDevice(&dev) != cudaSuccess || dev < 0 || dev >= 64) { cudaGetLastError(); return false; }
        if (cc[dev] == 0) {
            int major = 0, minor = 0;
            if (cudaDeviceGetAttribute(&major, cudaDevAttrComputeCapabilityMajor, dev) != cudaSuccess ||
                cudaDeviceGetAttribute(&minor, cudaDevAttrComputeCapabilityMinor, dev) != cudaSuccess) {
                cudaGetLastError();
                return false;
            }
            cc[dev] = major * 10 + minor;
        }
        if (cc[dev] < 75) return false;
        turing = cc[dev] < 80;
"""

if old not in s:
    raise SystemExit("expected qsa_prompt_attn compute-capability block not found")

p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("patched qsa_prompt_attn: sm_70 now returns false and uses the old prompt-attention fallback")
