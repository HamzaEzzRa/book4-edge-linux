#!/usr/bin/env python3
"""QCOM clock/domain synchronization selection and order, actual source fragments
Run: python3 scripts/test-qcom-cc-sync.py /path/to/kernel/tree [common.c]
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if len(sys.argv) not in (2, 3) or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip(), file=sys.stderr)
    sys.exit(0 if sys.argv[1:] in (['-h'], ['--help']) else 2)

kernel = Path(sys.argv[1])
source = (Path(sys.argv[2]) if len(sys.argv) == 3 else kernel / 'drivers/clk/qcom/common.c').read_text()
device = (kernel / 'include/linux/device.h').read_text()

def function(text, name):
    found = re.search(r'^(?:static (?:inline )?)?(?:void|int) ' + name + r'\(.*?^}', text, re.M | re.S)
    assert found, name
    return found[0]

probe = function(source, 'qcom_cc_really_probe')
start = probe.index('return -ENOMEM;') + len('return -ENOMEM;')
stop = probe.index('ret = devm_pm_domain_attach_list')
selection = probe[start:stop]
assert stop < probe.index('gdsc_register(') < probe.index('devm_clk_hw_register(')
combined = function(source, 'qcom_cc_clk_genpd_sync_state') if 'static void qcom_cc_clk_genpd_sync_state(' in source else ''
explicit = function(source, 'qcom_cc_sync_state')
setter = function(device, 'dev_set_drv_sync_state')

harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
struct device;
struct device_driver { void (*sync_state)(struct device *); };
struct device_node { bool domains, powered; };
struct device { struct device_driver *driver; struct device_node *of_node; bool icc; };
static char events[16];
static unsigned int used, icc_calls;
static void event(char c) { assert(used + 1 < sizeof(events)); events[used++] = c; events[used] = 0; }
static void clk_sync_state(struct device *dev)
{ assert(!dev->of_node || !dev->of_node->domains || dev->of_node->powered); event('C'); }
static void of_genpd_sync_state(struct device_node *node)
{ if (node && node->domains) { event('D'); node->powered = false; } }
static void genpd_sync_state(struct device *dev) { of_genpd_sync_state(dev->of_node); }
static void icc_sync_state(struct device *dev) { assert(dev->icc); icc_calls++; event('I'); }
static void custom_sync_state(struct device *dev) { assert(dev); event('X'); }
'''
registration = r'''
static void register_providers(struct device *dev)
{
    dev_set_drv_sync_state(dev, genpd_sync_state);
    dev_set_drv_sync_state(dev, clk_sync_state);
}
'''
checks = r'''
static void exercise(void (*initial)(struct device *), bool icc, bool domains,
                     const char *expected, bool preserve)
{
    struct device_driver driver = { .sync_state = initial };
    struct device_node nodes[2] = { { domains, true }, { domains, true } };
    struct device devices[2] = {
        { &driver, &nodes[0], icc },
        { &driver, &nodes[1], icc },
    };
    unsigned int old_icc = icc_calls;
    for (unsigned int i = 0; i < 2; i++) {
        select_sync(&devices[i]);
        register_providers(&devices[i]);
        select_sync(&devices[i]);
        if (preserve) assert(driver.sync_state == initial);
        used = 0;
        events[0] = 0;
        driver.sync_state(&devices[i]);
        assert(strcmp(events, expected) == 0);
    }
    assert(icc_calls - old_icc == (icc ? 2U : 0U));
}
int main(void)
{
    exercise(NULL, false, true, "CD", false);
    exercise(clk_sync_state, false, true, "CD", false);
    exercise(NULL, false, false, "C", false);
    exercise(qcom_cc_sync_state, true, true, "ICD", true);
    exercise(qcom_cc_sync_state, true, false, "IC", true);
    exercise(custom_sync_state, false, true, "X", true);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    binary = str(Path(directory) / 'qcom-cc-sync-check')
    code = harness + setter + '\n' + combined + '\n' + explicit + '\n'
    code += 'static void select_sync(struct device *dev) { (void)dev;\n' + selection + '\n}\n'
    code += registration + checks
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-x', 'c', '-o', binary, '-'],
                   input=code, text=True, check=True)
    subprocess.run([binary], check=True)
print('QCOM clock/domain selection, clock-before-domain order, ICC accounting and explicit callbacks passed')
