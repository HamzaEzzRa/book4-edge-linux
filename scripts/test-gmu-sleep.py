#!/usr/bin/env python3
"""GMU stop-guard regression, real helper, mocked registers
Run: python3 scripts/test-gmu-sleep.py /path/to/kernel/tree
"""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip(), file=sys.stderr)
    sys.exit(0 if sys.argv[1:] in (['-h'], ['--help']) else 2)

source = (Path(sys.argv[1]) / "drivers/gpu/drm/msm/adreno/a6xx_gmu.c").read_text()
start = source.index("static void a6xx_rpmh_stop(")
stop = source.index("\nstatic inline void pdc_write(", start)
function = source[start:stop]
harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef uint32_t u32;
#define BIT(n) (1UL << (n))
#define GMU_STATUS_FW_START 0
#define GMU_STATUS_PDC_SLEEP 1
#define REG_A6XX_GMU_RSCC_CONTROL_REQ 1
#define REG_A6XX_GPU_RSCC_RSC_STATUS0_DRV0 2
#define container_of(p, t, m) ((t *)((char *)(p) - offsetof(t, m)))
struct a6xx_gmu { unsigned long status; };
struct adreno_gpu { bool a840; };
struct a6xx_gpu { struct adreno_gpu base; struct a6xx_gmu gmu; };
static int writes;
static u32 ack;
static bool adreno_is_a840(struct adreno_gpu *gpu) { return gpu->a840; }
static bool test_and_clear_bit(int bit, unsigned long *status)
{
    bool old = !!(*status & BIT(bit));
    *status &= ~BIT(bit);
    return old;
}
static void set_bit(int bit, unsigned long *status) { *status |= BIT(bit); }
static void gmu_write(struct a6xx_gmu *gmu, int reg, u32 value)
{
    (void)gmu;
    assert(reg == REG_A6XX_GMU_RSCC_CONTROL_REQ);
    assert(value == (writes % 2 == 0 ? 1U : 0U));
    writes++;
}
#define gmu_poll_timeout_rscc(gmu, reg, val, cond, delay, timeout) \
    ((val) = ack, assert(cond), 0)
#define DRM_DEV_ERROR(...) assert(!"unexpected RSC timeout")
'''
checks = r'''
int main(void)
{
    for (int a840 = 0; a840 <= 1; a840++) {
        struct a6xx_gpu gpu = { .base.a840 = a840 };
        ack = BIT(a840 ? 30 : 16);
        writes = 0;
        a6xx_rpmh_stop(&gpu.gmu); /* No firmware, no PDC writes */
        assert(writes == 0 && gpu.gmu.status == 0);
        for (int cycle = 1; cycle <= 2; cycle++) {
            gpu.gmu.status = BIT(GMU_STATUS_FW_START);
            a6xx_rpmh_stop(&gpu.gmu);
            assert(writes == cycle * 2);
            assert(gpu.gmu.status == BIT(GMU_STATUS_PDC_SLEEP));
            a6xx_rpmh_stop(&gpu.gmu); /* Repeated stop, no retrigger */
            assert(writes == cycle * 2);
        }
    }
    return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    binary = str(Path(directory) / "gmu-sleep-check")
    subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", "-x", "c", "-o", binary, "-"],
                   input=harness + function + checks, text=True, check=True)
    subprocess.run([binary], check=True)
print("GMU sleep guard checks passed")
