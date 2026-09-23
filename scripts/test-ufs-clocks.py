#!/usr/bin/env python3
"""UFS reference regression, real helpers, mocked bulk clocks
Run: python3 scripts/test-ufs-clocks.py /path/to/kernel/tree
"""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip(), file=sys.stderr)
    sys.exit(0 if sys.argv[1:] in (['-h'], ['--help']) else 2)

source = (Path(sys.argv[1]) / "drivers/ufs/host/ufs-qcom.c").read_text()
start = source.index("static void ufs_qcom_disable_lane_clks(")
stop = source.index("static int ufs_qcom_init_lane_clks(", start)
functions = source[start:stop]
harness = r'''
#include <assert.h>
#include <stdbool.h>
struct ufs_qcom_host {
    int num_clks;
    void *clks;
    bool is_lane_clks_enabled;
};
static int refs, enable_error;
static int clk_bulk_prepare_enable(int count, void *clks)
{
    assert(count == 8 && clks);
    if (enable_error)
        return enable_error; /* Bulk API partial-failure unwind */
    refs++;
    return 0;
}
static void clk_bulk_disable_unprepare(int count, void *clks)
{
    assert(count == 8 && clks && refs > 0);
    refs--;
}
'''
checks = r'''
int main(void)
{
    struct ufs_qcom_host host = { .num_clks = 8, .clks = &refs };
    ufs_qcom_disable_lane_clks(&host);
    assert(refs == 0 && !host.is_lane_clks_enabled);
    enable_error = -5;
    assert(ufs_qcom_enable_lane_clks(&host) == -5);
    assert(refs == 0 && !host.is_lane_clks_enabled);
    enable_error = 0;
    for (int cycle = 0; cycle < 100; cycle++) {
        assert(ufs_qcom_enable_lane_clks(&host) == 0); /* setup_clocks */
        assert(ufs_qcom_enable_lane_clks(&host) == 0); /* resume */
        assert(ufs_qcom_enable_lane_clks(&host) == 0); /* HCE restart */
        assert(refs == 1 && host.is_lane_clks_enabled);
        enable_error = -5;
        assert(ufs_qcom_enable_lane_clks(&host) == 0); /* Already held */
        assert(refs == 1 && host.is_lane_clks_enabled);
        enable_error = 0;
        ufs_qcom_disable_lane_clks(&host);
        assert(refs == 0 && !host.is_lane_clks_enabled);
        ufs_qcom_disable_lane_clks(&host); /* suspend/setup_clocks overlap */
        assert(refs == 0 && !host.is_lane_clks_enabled);
    }
    return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    binary = str(Path(directory) / "ufs-clocks-check")
    subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", "-x", "c", "-o", binary, "-"],
                   input=harness + functions + checks, text=True, check=True)
    subprocess.run([binary], check=True)
print("UFS clock reference checks passed")
