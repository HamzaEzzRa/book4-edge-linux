#!/usr/bin/env python3
"""CSI PHY ownership regression, real power helpers
Run: python3 scripts/test-csiphy-clocks.py /path/to/kernel/tree
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip(), file=sys.stderr)
    sys.exit(0 if sys.argv[1:] in (['-h'], ['--help']) else 2)

source = (Path(sys.argv[1]) / "drivers/phy/qualcomm/phy-qcom-mipi-csi2-core.c").read_text()
probe = re.search(r"static int phy_qcom_mipi_csi2_probe\(.*?^}", source, re.M | re.S)[0]
assert "clk_bulk_prepare_enable(" not in probe, "probe leaks an extra clock reference"
start = source.index("static int phy_qcom_mipi_csi2_power_on(")
stop = source.index("static const struct phy_ops", start)
harness = r'''
#include <assert.h>
struct device { int unused; };
struct phy { struct device dev; };
struct stream_config { long link_freq; };
struct mipi_csi2phy_device;
struct mipi_csi2phy_hw_ops {
    void (*hw_version_read)(struct mipi_csi2phy_device *);
    int (*lanes_enable)(struct mipi_csi2phy_device *, struct stream_config *);
};
struct soc_config { int num_clk, num_supplies; const struct mipi_csi2phy_hw_ops *ops; };
struct mipi_csi2phy_device {
    struct soc_config *soc_cfg;
    void *clks, *supplies;
    struct stream_config stream_cfg;
};
static struct mipi_csi2phy_device device;
static int clocks, supplies, fail_stage, activations;
#define dev_err(dev, ...) ((void)(dev))
static struct mipi_csi2phy_device *phy_get_drvdata(struct phy *phy)
{ assert(phy); return &device; }
static int regulator_bulk_enable(int count, void *data)
{ assert(count == 2 && data); if (fail_stage == 1) return -1; supplies++; return 0; }
static void regulator_bulk_disable(int count, void *data)
{ assert(count == 2 && data && supplies == 1); supplies--; }
static int phy_qcom_mipi_csi2_set_clock_rates(struct mipi_csi2phy_device *dev, long rate)
{ assert(dev == &device && rate > 0 && supplies == 1); return fail_stage == 2 ? -2 : 0; }
static int clk_bulk_prepare_enable(int count, void *data)
{ assert(count == 4 && data); if (fail_stage == 3) return -3; clocks++; return 0; }
static void clk_bulk_disable_unprepare(int count, void *data)
{ assert(count == 4 && data && clocks == 1); clocks--; }
static void read_version(struct mipi_csi2phy_device *dev)
{ assert(dev == &device && clocks == 1 && supplies == 1); }
static int enable_lanes(struct mipi_csi2phy_device *dev, struct stream_config *cfg)
{ assert(dev == &device && cfg == &device.stream_cfg && clocks == 1 && supplies == 1); activations++; return 0; }
'''
checks = r'''
int main(void)
{
    const struct mipi_csi2phy_hw_ops ops = { read_version, enable_lanes };
    struct soc_config config = { .num_clk = 4, .num_supplies = 2, .ops = &ops };
    struct phy phy;
    device = (struct mipi_csi2phy_device) {
        .soc_cfg = &config, .clks = &clocks, .supplies = &supplies,
        .stream_cfg = { .link_freq = 1000000000 },
    };
    for (fail_stage = 1; fail_stage <= 3; fail_stage++) {
        assert(phy_qcom_mipi_csi2_power_on(&phy) == -fail_stage);
        assert(clocks == 0 && supplies == 0 && activations == 0);
    }
    fail_stage = 0;
    for (int i = 0; i < 100; i++) {
        assert(phy_qcom_mipi_csi2_power_on(&phy) == 0);
        assert(clocks == 1 && supplies == 1);
        assert(phy_qcom_mipi_csi2_power_off(&phy) == 0);
        assert(clocks == 0 && supplies == 0);
    }
    assert(activations == 100);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    binary = str(Path(directory) / "csiphy-clocks-check")
    subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", "-x", "c", "-o", binary, "-"],
                   input=harness + source[start:stop] + checks, text=True, check=True)
    subprocess.run([binary], check=True)
print("CSI PHY probe and power-cycle clock checks passed")
