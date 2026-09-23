#!/usr/bin/env python3
"""Actual eUSB2 init/exit and system-PM helpers, mocked hardware
Run: python3 scripts/test-eusb2-system-pm.py /path/to/kernel/tree
Excluded: physical low-power state, USB wake and energy
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip(), file=sys.stderr)
    sys.exit(0 if sys.argv[1:] in (['-h'], ['--help']) else 2)

source = (Path(sys.argv[1]) / 'drivers/phy/phy-snps-eusb2.c').read_text()
probe = re.search(r'static int snps_eusb2_hsphy_probe\(.*?^}', source, re.M | re.S)[0]
assert 'phy->phy = generic_phy;' in probe
assert probe.index('phy->phy = generic_phy;') < probe.index('devm_of_phy_provider_register(')
assert '.pm\t= &snps_eusb2_hsphy_pm_ops,' in source
assert 'pm_runtime_' not in source
state = re.search(r'struct snps_eusb2_hsphy \{.*?^};', source, re.M | re.S)[0]
helpers = '\n'.join(re.search(rf'static int snps_eusb2_hsphy_{name}\(.*?^}}', source, re.M | re.S)[0]
                    for name in ('init', 'exit', 'suspend', 'resume'))
ops = re.search(r'static const struct dev_pm_ops snps_eusb2_hsphy_pm_ops = \{.*?^};', source, re.M | re.S)[0]
harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#define __iomem
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define EUSB2_NUM_VREGS 2
#define pm_sleep_ptr(p) (p)
#define dev_err(d, ...) ((void)(d))
#define usleep_range(a, b) ((void)(a), (void)(b))
struct device { void *data; struct device *parent; };
struct phy { struct device dev; int init_count; };
struct clk { int unused; };
struct clk_bulk_data { int *count; };
struct reset_control { int unused; };
struct regulator_bulk_data { int count; };
enum phy_mode { PHY_MODE_INVALID, PHY_MODE_USB_HOST, PHY_MODE_USB_DEVICE };
struct snps_eusb2_phy_drvdata { int (*phy_init)(struct phy *); int num_clks; };
struct dev_pm_ops {
    int (*suspend)(struct device *), (*resume)(struct device *);
    int (*runtime_suspend)(struct device *), (*runtime_resume)(struct device *);
    int (*freeze)(struct device *), (*thaw)(struct device *), (*poweroff)(struct device *), (*restore)(struct device *);
};
static int fail_stage;
static void *dev_get_drvdata(struct device *d) { return d->data; }
static void *phy_get_drvdata(struct phy *p) { return p->dev.data; }
static void *dev_of_node(struct device *d) { return d; }
static int regulator_bulk_enable(size_t n, struct regulator_bulk_data *v) {
    if (fail_stage == 1) return -1;
    for (size_t i = 0; i < n; i++) { assert(v[i].count == 0); v[i].count++; }
    return 0;
}
static void regulator_bulk_disable(size_t n, struct regulator_bulk_data *v) {
    for (size_t i = 0; i < n; i++) { assert(v[i].count == 1); v[i].count--; }
}
static int phy_init(struct phy *p) {
    if (fail_stage == 2) return -2;
    assert(p->init_count == 0); p->init_count++; return 0;
}
static int phy_exit(struct phy *p) { assert(p->init_count == 1); p->init_count--; return 0; }
static int of_clk_set_defaults(void *d, bool supplier) {
    assert(d && !supplier); return fail_stage == 3 ? -3 : 0;
}
static int clk_bulk_prepare_enable(int n, struct clk_bulk_data *c) {
    if (fail_stage == 4) return -4;
    for (int i = 0; i < n; i++) (*c[i].count)++;
    return 0;
}
static void clk_bulk_disable_unprepare(int n, struct clk_bulk_data *c) {
    for (int i = 0; i < n; i++) { assert(*c[i].count > 0); (*c[i].count)--; }
}
static int reset_control_assert(struct reset_control *r) { (void)r; return fail_stage == 5 ? -5 : 0; }
static int reset_control_deassert(struct reset_control *r) { (void)r; return fail_stage == 6 ? -6 : 0; }
static int hw_init(struct phy *p) { assert(p); return fail_stage == 7 ? -7 : 0; }
static const struct snps_eusb2_phy_drvdata sm8550_snps_eusb2_phy = { hw_init, 1 };
static const struct snps_eusb2_phy_drvdata exynos2200_snps_eusb2_phy = { hw_init, 3 };
'''
harness += state + '\n' + helpers + '\n' + ops
harness += r'''
static void supplies(struct snps_eusb2_hsphy *p, int count) {
    assert(p->repeater->init_count == count);
    for (size_t i = 0; i < ARRAY_SIZE(p->vregs); i++) assert(p->vregs[i].count == count);
}
int main(void) {
    const struct dev_pm_ops *ops = &snps_eusb2_hsphy_pm_ops;
    assert(ops->suspend && ops->resume);
    assert(!ops->runtime_suspend && !ops->runtime_resume);
    assert(!ops->freeze && !ops->thaw && !ops->poweroff && !ops->restore);
    int clocks[3] = {0};
    struct clk_bulk_data c[3] = {{&clocks[0]}, {&clocks[1]}, {&clocks[2]}};
    struct phy generic = {0}, repeater = {0};
    struct snps_eusb2_hsphy p = { .phy = &generic, .clks = c, .repeater = &repeater,
        .data = &sm8550_snps_eusb2_phy, .mode = PHY_MODE_USB_HOST };
    struct device dev = { .data = &p };
    generic.dev = (struct device){ .data = &p, .parent = &dev };
    assert(ops->suspend(&dev) == 0 && ops->resume(&dev) == 0 && clocks[0] == 0);
    for (fail_stage = 1; fail_stage <= 7; fail_stage++) {
        assert(snps_eusb2_hsphy_init(&generic) == -fail_stage);
        supplies(&p, 0);
        assert(clocks[0] == 0 && !p.clocks_suspended);
        assert(ops->suspend(&dev) == 0 && ops->resume(&dev) == 0);
    }
    fail_stage = 0;
    assert(snps_eusb2_hsphy_init(&generic) == 0);
    generic.init_count = 1;
    for (int mode = PHY_MODE_INVALID; mode <= PHY_MODE_USB_DEVICE; mode++) {
        p.mode = mode;
        for (int i = 0; i < 100; i++) {
            assert(ops->suspend(&dev) == 0);
            assert(clocks[0] == (mode != PHY_MODE_USB_HOST));
            assert(p.clocks_suspended == (mode == PHY_MODE_USB_HOST));
            supplies(&p, 1);
            assert(ops->suspend(&dev) == 0);
            assert(ops->resume(&dev) == 0 && ops->resume(&dev) == 0);
            assert(clocks[0] == 1 && !p.clocks_suspended);
            supplies(&p, 1);
        }
    }
    p.mode = PHY_MODE_USB_HOST;
    assert(ops->suspend(&dev) == 0);
    fail_stage = 4;
    for (int i = 0; i < 3; i++) {
        assert(ops->resume(&dev) == -4 && p.clocks_suspended && clocks[0] == 0);
        assert(ops->suspend(&dev) == 0);
        supplies(&p, 1);
    }
    fail_stage = 0;
    assert(ops->resume(&dev) == 0 && clocks[0] == 1);
    assert(ops->suspend(&dev) == 0);
    fail_stage = 4;
    assert(ops->resume(&dev) == -4);
    assert(snps_eusb2_hsphy_exit(&generic) == 0);
    generic.init_count = 0;
    assert(!p.clocks_suspended && clocks[0] == 0);
    supplies(&p, 0);
    assert(ops->resume(&dev) == 0 && clocks[0] == 0);
    fail_stage = 0;
    p.data = &exynos2200_snps_eusb2_phy;
    assert(snps_eusb2_hsphy_init(&generic) == 0);
    generic.init_count = 1;
    assert(ops->suspend(&dev) == 0);
    for (int i = 0; i < 3; i++) assert(clocks[i] == 1);
    assert(!p.clocks_suspended && ops->resume(&dev) == 0);
    assert(snps_eusb2_hsphy_exit(&generic) == 0);
    generic.init_count = 0;
    supplies(&p, 0);
    for (int i = 0; i < 3; i++) assert(clocks[i] == 0);
    /* Four PHYs, three reference gates, one gate shared by two PHYs */
    struct snps_eusb2_hsphy peers[4];
    struct phy phys[4] = {0};
    struct device devices[4];
    for (int i = 0; i < 4; i++) {
        peers[i] = (struct snps_eusb2_hsphy){ .phy = &phys[i], .data = &sm8550_snps_eusb2_phy,
            .mode = PHY_MODE_USB_HOST, .clks = &c[i % 3] };
        phys[i].init_count = 1;
        devices[i].data = &peers[i];
        assert(clk_bulk_prepare_enable(1, peers[i].clks) == 0);
    }
    for (int cycle = 0; cycle < 100; cycle++) {
        assert(clocks[0] == 2 && clocks[1] == 1 && clocks[2] == 1);
        for (int i = 0; i < 4; i++) assert(ops->suspend(&devices[i]) == 0);
        assert(clocks[0] == 0 && clocks[1] == 0 && clocks[2] == 0);
        for (int i = 3; i >= 0; i--) assert(ops->resume(&devices[i]) == 0);
    }
    return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    binary = str(Path(directory) / 'eusb2-system-pm-check')
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-x', 'c', '-o', binary, '-'],
                   input=harness, text=True, check=True)
    subprocess.run([binary], cwd=directory, check=True)
print('eUSB2 system PM: host-only, Exynos/device exclusions, shared gates, 100 cycles and failure unwinds passed')
