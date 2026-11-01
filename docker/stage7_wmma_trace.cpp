// Non-scored diagnostics only: observe actual CUDA driver kernel launches.
#include <cupti.h>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <set>
#include <string>

static void CUPTIAPI callback(void*, CUpti_CallbackDomain domain, CUpti_CallbackId,
                             const void* data) {
    if (domain != CUPTI_CB_DOMAIN_DRIVER_API) return;
    auto* cb = static_cast<const CUpti_CallbackData*>(data);
    if (cb->callbackSite != CUPTI_API_EXIT || !cb->symbolName ||
        !std::strstr(cb->symbolName, "gemm_iq_f16")) return;
    static std::mutex mu;
    static std::set<std::string> seen;
    std::lock_guard<std::mutex> lock(mu);
    if (seen.insert(cb->symbolName).second)
        std::fprintf(stderr, "S7_CUPTI kernel=%s result=%d\n", cb->symbolName,
                     cb->functionReturnValue ? *static_cast<const int*>(cb->functionReturnValue) : -1);
}

__attribute__((constructor)) static void initialize() {
    CUpti_SubscriberHandle subscriber;
    CUptiResult rc = cuptiSubscribe(&subscriber, callback, nullptr);
    if (rc == CUPTI_SUCCESS) rc = cuptiEnableDomain(1, subscriber, CUPTI_CB_DOMAIN_DRIVER_API);
    std::fprintf(stderr, "S7_CUPTI subscription=%d\n", static_cast<int>(rc));
}
