#!/usr/bin/env python3
"""DWC3 ownership and QMP registration-order regression, real CCF helpers
Run: python3 scripts/test-usb-phy-pm.py /path/to/kernel/tree
Excluded: probe error paths, USB/DisplayPort hardware
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

kernel = Path(sys.argv[1])
usb = kernel / 'drivers/usb'
phy = kernel / 'drivers/phy/qualcomm'
ccf = (kernel / 'drivers/clk/clk.c').read_text()

def function(source, name):
    return re.search(rf'static (?:int|void) {name}\(.*?^}}', source, re.M | re.S)[0]

quirk = re.search(r'static const struct xhci_plat_priv dwc3_xhci_plat_quirk = \{.*?^};',
                  (usb / 'dwc3/host.c').read_text(), re.M | re.S)[0]
flag = re.search(r'^#define XHCI_SKIP_PHY_INIT\s+(.+)$',
                 (usb / 'host/xhci.h').read_text(), re.M)[1]
assert 'priv->quirks & XHCI_SKIP_PHY_INIT' in (usb / 'host/xhci-plat.c').read_text()
helpers = '\n'.join(function(ccf, name) for name in
                    ('clk_pm_runtime_get', 'clk_pm_runtime_put', 'clk_pm_runtime_init'))
harness = r'''
#include <assert.h>
#include <stdbool.h>
#define BIT_ULL(n) (1ULL << (n))
struct xhci_plat_priv { unsigned long long quirks; void (*plat_start)(void); };
static void dwc3_xhci_plat_start(void) {}
struct device { bool enabled; int usage; };
struct clk_core { struct device *dev; bool rpm_enabled; int rpm_node; };
static int clk_rpm_list_lock, clk_rpm_list;
#define mutex_lock(p) ((void)(p))
#define mutex_unlock(p) ((void)(p))
#define hlist_add_head(n, h) ((void)(n), (void)(h))
static bool pm_runtime_enabled(struct device *dev) { return dev->enabled; }
static int pm_runtime_resume_and_get(struct device *dev) { dev->usage++; return 0; }
static void pm_runtime_put_sync(struct device *dev) { assert(dev->usage > 0); dev->usage--; }
'''
harness += '#define XHCI_SKIP_PHY_INIT ' + flag + '\n' + quirk + '\n' + helpers
harness += r'''
int main(void) {
assert(dwc3_xhci_plat_quirk.quirks & XHCI_SKIP_PHY_INIT);
/* Control: runtime-enabled provider reference */
{
    struct device dev = {.enabled = true};
    struct clk_core clock = {.dev = &dev};
    clk_pm_runtime_init(&clock);
    assert(clock.rpm_enabled && clk_pm_runtime_get(&clock) == 0 && dev.usage == 1);
    clk_pm_runtime_put(&clock);
    assert(dev.usage == 0);
}
'''
for driver, register in (
    ('usb', 'phy_pipe_clk_register'),
    ('usb-legacy', 'phy_pipe_clk_register'),
    ('combo', 'qmp_combo_register_clocks'),
    ('usbc', 'qmp_usbc_register_clocks'),
):
    source = (phy / f'phy-qcom-qmp-{driver}.c').read_text()
    probe = function(source, 'qmp_' + driver.replace('-', '_') + '_probe')
    # Registration/PM ordering from the actual probe
    steps = {
        register: 'clk_pm_runtime_init(&clock); registered = true;',
        'devm_pm_runtime_enable': 'dev.enabled = true;',
        'pm_runtime_forbid': 'dev.usage++;',
        'devm_phy_create': 'assert(registered && dev.enabled && dev.usage == 1);',
    }
    harness += '{ struct device dev = {0}; struct clk_core clock = {.dev = &dev}; bool registered = false;\n'
    harness += '\n'.join(code for name, code in sorted(steps.items(), key=lambda item: probe.index(item[0] + '(')))
    harness += r'''
assert(!clock.rpm_enabled && "PIPE clock must not pin its own PHY");
assert(clk_pm_runtime_get(&clock) == 0); /* first PIPE prepare */
assert(dev.usage == 1); /* only the default forbid reference */
dev.usage--; /* Runtime-PM opt-in */
assert(dev.usage == 0); /* Suspend-callback eligibility */
clk_pm_runtime_put(&clock);
assert(dev.usage == 0);
}
'''
harness += 'return 0; }\n'
with tempfile.TemporaryDirectory() as directory:
    binary = str(Path(directory) / 'usb-phy-pm-check')
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-x', 'c', '-o', binary, '-'],
                   input=harness, text=True, check=True)
    subprocess.run([binary], check=True, cwd=directory)
print('DWC3 ownership flag and all four QMP clock/runtime-PM registration orders passed')
