# S6-7 assessment — 2026-10-28

**No final combination or three-batch candidate validation was run:** S6-2 through S6-6 did not produce a candidate that demonstrated a dual-agent improvement beyond S6-0 variability and passed the necessary gates. Combining unvalidated flags would violate the plan. S6-7 combination is therefore **skipped**, not claimed as tested.

The only validated three-batch recipe remains S6-0 T7-Fixed: A/B decode medians 22.3/21.2 tok/s, with both agents below the >=30 tok/s target in every run. Single-batch screens do not establish statistical equivalence or reliably isolate the cause of Stage 5's full-bundle regression. `ADAPT_OVERLAP=1` was active and showed 18.7/18.6 tok/s in one valid C2 screen, making it a reason to avoid that unvalidated flag, not proof it alone caused the historical regression.

S6-1 showed that CPU expert work and GPU waitCPU dominate instrumented timing. One CPU worker count and one fixed PCIe share did not improve the unprofiled screen; further untested values cannot be ruled out. Cache 4400 failed startup VRAM planning; KV resident 24576 failed C2's minimum output requirement. No production promotion was performed. Retain the pinned S6-0 recipe as the measured reference, not a 30 tok/s solution.

C2 checks mechanical conditions and overlap, not semantic coding quality. No candidate qualified for the separate task-quality check. Further tuning, targeted source/kernel profiling, or additional controlled candidates would require new evidence; the target remains unmet.
