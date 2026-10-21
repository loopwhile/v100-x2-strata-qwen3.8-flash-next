# Stage 4-B Docker Image Build Receipt

- **Date / Time**: 2026-10-21 22:18:52 KST
- **Target Image**: `strata-v100-upstream:0.1.47`
- **Image ID**: `sha256:19c3b72a1097486eeae3fd9b964179a36a1c137615e5c93f6d6e70eacdab8e9d`
- **Base Image**: `nvidia/cuda:12.9.1-devel-ubuntu24.04`
- **Upstream Git Source**: `https://github.com/Niko1221/Strata.git`
- **Resolved Commit**: `011c9e600a93bbc9fd451c563501b5831c32bbca` (tag `v0.2.2`, engine `0.1.47`)
- **Pinned llama.cpp Commit**: `3cf03257f219afbe7334045ff7c6a06ac68c627d`
- **Target Architecture**: Volta `sm_70` (Tesla V100-SXM2-16GB)
- **CMake Options**:
  - `-DSTRATA_ENABLE_CUDA=ON`
  - `-DSTRATA_BUILD_TESTS=OFF`
  - `-DSTRATA_EXPERIMENTAL_SM60=ON`
  - `-DCMAKE_CUDA_ARCHITECTURES=70`
- **Engine Binaries**:
  - `/opt/strata/engine/strata` (89,073,272 bytes)
  - `/opt/strata/engine/libstrata_kq.so` (16,368,096 bytes)
- **Engine BUILD.json**:
```json
{
 "source": "local",
 "version": "0.1.47",
 "archs": [
  70
 ],
 "vision": "none",
 "cuda_dirs": [
  "/usr/local/cuda/bin",
  "/usr/local/cuda/lib64"
 ],
 "src": "ba8a2d3595085632",
 "vision_src": null
}
```

**Gate 4-B Build Passed**: Successfully built and packaged Strata engine 0.1.47 for Volta sm_70 under CUDA 12.9.
