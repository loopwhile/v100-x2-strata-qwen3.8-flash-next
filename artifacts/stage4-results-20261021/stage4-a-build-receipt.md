# Stage 4-A Docker Image Build Receipt

- **Date / Time**: 2026-10-21 21:53:12 KST
- **Target Image**: `strata-v100-upstream:0.1.44.1`
- **Image ID**: `sha256:56fd71f0ddfe7c702df76371358252fb59407cad821b0f7e52e027054ec7ae93`
- **Base Image**: `nvidia/cuda:12.9.1-devel-ubuntu24.04` (`sha256:020bc241a628...`)
- **Upstream Git Source**: `https://github.com/Niko1221/Strata.git`
- **Resolved Commit**: `296b59d2f73c8f04a805df29c2fa97655adace78` (tag `v0.1.44.1`)
- **Pinned llama.cpp Commit**: `3cf03257f219afbe7334045ff7c6a06ac68c627d`
- **Target Architecture**: Volta `sm_70` (Tesla V100-SXM2-16GB)
- **CMake Options**:
  - `-DSTRATA_ENABLE_CUDA=ON`
  - `-DSTRATA_BUILD_TESTS=OFF`
  - `-DSTRATA_EXPERIMENTAL_SM60=ON`
  - `-DCMAKE_CUDA_ARCHITECTURES=70`
- **Engine Binaries**:
  - `/opt/strata/engine/strata` (72,633,568 bytes)
  - `/opt/strata/engine/libstrata_kq.so` (16,368,096 bytes)
- **Engine BUILD.json**:
```json
{
 "source": "local",
 "version": "0.1.44.1",
 "archs": [
  70
 ],
 "vision": "none",
 "cuda_dirs": [
  "/usr/local/cuda/bin",
  "/usr/local/cuda/lib64"
 ],
 "src": "7dfd34378bd2d32a",
 "vision_src": null
}
```

**Gate 4-A Build Passed**: High-fidelity isolated build verified, exact revision pinned, sm_70 experimental flags confirmed, and existing Stage 3-A Docker images remain untouched.
