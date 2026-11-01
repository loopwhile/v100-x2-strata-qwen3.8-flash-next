#!/usr/bin/env python3
"""Bounded WMMA2/lean adaptation; run inside a new pinned 0.1.54 image."""
import pathlib
import sys

root, fork, arm = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
assert arm in ('15', '16')


def replace(s, old, new, count=1):
    assert s.count(old) == count, (old[:100], s.count(old), count)
    return s.replace(old, new)


p = root / 'src/kernels/cuda/iq_kernels.cu'
s, f = p.read_text(), fork.read_text()
start = '// ---- STRATA_PF_WMMA2=1 (opt-in):'
# Only the fork's W2 decoder/tile is ported. Keep upstream generic WMMA,
# scheduling, defaults and contiguous group weights. No fork default bundle.
w2 = f[f.index(start):f.index('bool w2_attrs_fit(int dev) {')]
w2 = w2.replace('int wsrc,\n                                                                  GroupedWeightTable tbl', 'int /*reserved*/')
w2 = replace(w2, '(wsrc == 0 ? W + (size_t) e * expert_bytes\n                                   : (const uint8_t*) (wsrc == 1 ? tbl.gu[e] : tbl.dn[e]))', '(W + (size_t) e * expert_bytes)')
w2 = 'constexpr int W2_RB = 128, W2_CB = 64, W2_KT = 64, W2_NT = 256, W2_LD = W2_KT + 8;\nconstexpr int W2_RB_N64 = 64, W2_CB_N64 = 128;\n' + w2
# Deliberately use the original 128-output / 64-token orientation only.
w2 += '''bool w2_on() {
    static const bool v = [] { const char* e = std::getenv("STRATA_PF_WMMA2"); return e && e[0] == '1'; }();
    return v;
}
'''
s = s[:s.index(start)] + w2 + s[s.index('}  // namespace\n\nbool gemm_iq_f16_grouped', s.index(start)):]
# Input row indirection is needed by lean, with a null default preserving callers.
s = replace(s, 'const int32_t* __restrict__ bounds, int ch_per_e,', 'const int32_t* __restrict__ bounds, const int32_t* __restrict__ ids, int ch_per_e,')
s = replace(s, '(c0 + t * WG_BM + r) * ldx', '(ids ? ids[c0 + t * WG_BM + r] : c0 + t * WG_BM + r) * ldx')
s = replace(s, 'int ldy, void* stream) {\n    if (n_out % WG_BN', 'int ldy, void* stream, const int32_t* ids) {\n    if (n_out % WG_BN')
a = s.index('    // STRATA_PF_WMMA2=1 (opt-in):', s.index('bool gemm_iq_f16_grouped'))
b = s.index('    const bool q20', a)
s = s[:a] + '''    // S7 selective port: IQ3_XXS added; no new defaults or tile orientation.
    if (w2_on() && n_out % W2_RB == 0 && ldx % 8 == 0 && ldy % 8 == 0 && (uintptr_t) X % 16 == 0 && (uintptr_t) Y % 32 == 0 &&
        (uintptr_t) W % 4 == 0 && expert_bytes % 4 == 0 &&
        (((ty == 18 || ty == 22) && K % 256 == 0) || (ty == 20 && K % 128 == 0))) {
        const size_t rb = iq_row_bytes(ty, K);
        const int ch = (max_rows + W2_CB - 1) / W2_CB;
        if ((long long) n_experts * ch <= 65535) {
            const dim3 grid2((unsigned) (n_out / W2_RB), (unsigned) (n_experts * ch));
            cudaStream_t s2 = (cudaStream_t) stream;
#define S7_W2(T) gemm_iq_f16_w2_kernel<T, W2_RB, W2_CB><<<grid2, W2_NT, 0, s2>>>((const uint8_t*) W, expert_bytes, rb, K, (const __half*) X, ldx, bounds, ids, ch, Y, ldy, 0)
            if (ty == 18) { S7_W2(18); }
            else if (ty == 22) { S7_W2(22); }
            else { S7_W2(20); }
#undef S7_W2
            const bool ok = cudaGetLastError() == cudaSuccess;
            static thread_local bool seen[64] = {};
            if (ok && !seen[ty]) {
                seen[ty] = true;
                std::fprintf(stderr, "S7_WMMA2 launched ty=%d K=%d out=%d ids=%d tile=128x64\\n", ty, K, n_out, ids != nullptr);
            }
            return ok;
        }
    }
''' + s[b:]
s = replace(s, 'ldx, bounds, mt, Y, ldy)', 'ldx, bounds, ids, mt, Y, ldy)', 3)
s = replace(s, 'int, int, float*, int, void*) {\n    return false;', 'int, int, float*, int, void*, const int32_t*) {\n    return false;')
p.write_text(s)
p = root / 'include/strata/kernels/iq_kernels.hpp'
s = p.read_text()
s = replace(s, 'int max_rows, float* Y, int ldy, void* stream);', 'int max_rows, float* Y, int ldy, void* stream, const int32_t* ids = nullptr);')
p.write_text(s)
# Existing upstream parity omits type 18: include it explicitly in this image.
p = root / 'src/kernels/pf_wmma_parity.cpp'
s = replace(p.read_text(), 'for (int ty : {16, 22, 29})', 'for (int ty : {16, 18, 22, 29})')
s = replace(s, 'std::mt19937& rng) {\n    const std::vector<int> rows', 'std::mt19937& rng, bool indexed = false) {\n    const std::vector<int> rows')
s = replace(s, 'const int maxr = *std::max_element(rows.begin(), rows.end());', '''std::vector<int32_t> ids(total);
    for (int i = 0; i < total; ++i) ids[i] = total - 1 - i;
    int32_t* di = nullptr;
    if (indexed) {
        ck(cudaMalloc(&di, total * sizeof(int32_t)), "ids");
        ck(cudaMemcpy(di, ids.data(), total * sizeof(int32_t), cudaMemcpyHostToDevice), "ids copy");
    }
    const int maxr = *std::max_element(rows.begin(), rows.end());''')
s = replace(s, 'dy, n_out, nullptr))', 'dy, n_out, nullptr, di))')
s = replace(s, 'x[(size_t) r * K + kk]', 'x[(size_t) (indexed ? ids[r] : r) * K + kk]')
s = replace(s, 'cudaFree(dw); cudaFree(dx);', 'cudaFree(di); cudaFree(dw); cudaFree(dx);')
s = replace(s, 'fails += run(20, 2560, 640, rng);', '''fails += run(20, 2560, 640, rng);
        for (int ty : {18, 23}) fails += run(ty, 1280, 2560, rng, true);''')
p.write_text(s)
if arm == '16':
    p = root / 'src/prefill/prefill.cpp'
    s = p.read_text()
    marker = '// #136 P3: a layout whose chunks run the fused experts'
    lean = '''// S7 selective WMMA_LEAN adaptation of fork 2c9b1dd: skip gathered FP16
// input, alias the down input to dead xn16 scratch, and omit the fallback DQ
// ring. Keep upstream's group weights, MMQ buffers and scheduling unchanged.
// The exact same predicate is used for accounting, carving and every reader.
bool wmma_lean() {
    static const bool enabled = [] {
        const char* e = std::getenv("STRATA_PF_WMMA_LEAN");
        if (!e || e[0] != '1' || !pf_wmma()) return false;
        int n = 0, dev = 0, major = 0, minor = 0;
        if (cudaGetDeviceCount(&n) != cudaSuccess || n != 1 || cudaGetDevice(&dev) != cudaSuccess ||
            cudaDeviceGetAttribute(&major, cudaDevAttrComputeCapabilityMajor, dev) != cudaSuccess ||
            cudaDeviceGetAttribute(&minor, cudaDevAttrComputeCapabilityMinor, dev) != cudaSuccess || major != 7 || minor != 0)
            return false;
        const auto& mp = mmq_plan();
        const auto& lay = strata::kernels::cpu::expert_layout();
        if (!mp.any || mp.fallback || !lay.native || lay.fmt.empty()) return false;
        for (const auto& f : lay.fmt)
            if ((f.gu_type != 16 && f.gu_type != 17 && f.gu_type != 18 && f.gu_type != 21 && f.gu_type != 22 && f.gu_type != 23) ||
                (f.d_type != 20 && f.d_type != 42) || f.tail_off || f.had_gu || f.had_d) return false;
        static_assert(D >= K * 640, "xn16 must hold all routed down inputs");
        std::fprintf(stderr, "S7_WMMA_LEAN eligible: Xs skipped, Hh aliases xn16, DQ ring omitted\\n");
        return true;
    }();
    return enabled;
}
'''
    s = replace(s, marker, lean + marker)
    s = replace(s, 'if (fp16_bufs(mp)) a.take<uint16_t>', 'if (fp16_bufs(mp) && !wmma_lean()) a.take<uint16_t>', 2)
    s = replace(s, 'm.Xs = fp16_bufs(mp) ?', 'm.Xs = fp16_bufs(mp) && !wmma_lean() ?')
    s = replace(s, 'm.Hh = fp16_bufs(mp) ? c.take<uint16_t>(T * K * 640, ok) : nullptr;', 'm.Hh = wmma_lean() ? m.xn16 : (fp16_bufs(mp) ? c.take<uint16_t>(T * K * 640, ok) : nullptr);')
    s = replace(s, 'for (int i = 0; i < DQ; ++i) { m.dq_gu[i] = o.take<uint16_t>(1280 * 2560, ok); m.dq_d[i] = o.take<uint16_t>(2560 * 640, ok); }', 'if (!wmma_lean())\n        for (int i = 0; i < DQ; ++i) { m.dq_gu[i] = o.take<uint16_t>(1280 * 2560, ok); m.dq_d[i] = o.take<uint16_t>(2560 * 640, ok); }')
    s = replace(s, 'for (int i = 0; i < DQ; ++i) { o.take<uint16_t>(1280 * 2560, ok); o.take<uint16_t>(2560 * 640, ok); }', 'if (!wmma_lean())\n        for (int i = 0; i < DQ; ++i) { o.take<uint16_t>(1280 * 2560, ok); o.take<uint16_t>(2560 * 640, ok); }')
    s = replace(s, 'const size_t mmq_gub = use_mmq ? mmq::matrix_bytes(mmq_gt, 1280, N) : 0;', '''if (wmma_lean() && (!wmma_l || m.fused_bufs || had_gu || had_d)) {
                            err = "prefill: WMMA_LEAN reader predicate drift (FP16 fallback buffers omitted)";
                            return false;
                        }
                        const size_t mmq_gub = use_mmq ? mmq::matrix_bytes(mmq_gt, 1280, N) : 0;''')
    s = replace(s, 'if (fused_l) {\n                        if (static bool said', '''if (wmma_lean() && (!use_mmq || fused_l || had_gu || had_d)) {
                        err = "prefill: WMMA_LEAN cannot take a fused or fallback expert path";
                        return false;
                    }
                    if (fused_l) {
                        if (static bool said''')
    s = replace(s, 'gather_rows16(m.mixed_h, m.src_dev, m.Xs, T * K, N, m.cs);\n                                if (had_gu)', 'if (!wmma_lean()) gather_rows16(m.mixed_h, m.src_dev, m.Xs, T * K, N, m.cs);\n                                if (had_gu)')
    s = replace(s, 'mmq_gt, m.grp_gu, mmq_gub, 1280, (int) N, m.Xs, (int) N, m.bounds_dev + j0, ngx,\n                                        (int) maxr, m.GU, 1280, m.cs);', '''mmq_gt, m.grp_gu, mmq_gub, 1280, (int) N, wmma_lean() ? m.mixed_h : m.Xs, (int) N, m.bounds_dev + j0, ngx,
                                        (int) maxr, m.GU, 1280, m.cs, wmma_lean() ? m.src_dev : nullptr);''')
    # The layer-major implementation does not have the guarded WMMA reader.
    s = replace(s, 'const MmqPlan& mp = mmq_plan();\n    if ((int64_t) mp.layer.size()', 'if (wmma_lean()) { why = "WMMA_LEAN requires guarded run_impl"; return 0; }\n    const MmqPlan& mp = mmq_plan();\n    if ((int64_t) mp.layer.size()')
    p.write_text(s)
