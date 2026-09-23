#!/usr/bin/env python3
"""QMP suspend/resume registration and extracted native forced-PM helpers
Run: python3 scripts/test-qmp-system-pm.py /path/to/kernel/tree
Excluded: PHY hardware, peripheral wake, DisplayPort, hibernation
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip(), file=sys.stderr)
    sys.exit(0 if sys.argv[1:] in (['-h'], ['--help']) else 2)

kernel = Path(sys.argv[1])
runtime = (kernel / 'drivers/base/power/runtime.c').read_text()
helpers = '\n'.join(re.search(rf'^(?:int|bool) {name}\(.*?^}}', runtime, re.M | re.S)[0]
                    for name in ('pm_runtime_need_not_resume', 'pm_runtime_force_suspend', 'pm_runtime_force_resume'))
harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
struct device;
struct dev_pm_ops {
    int (*suspend)(struct device *), (*resume)(struct device *);
    int (*runtime_suspend)(struct device *), (*runtime_resume)(struct device *);
    int (*freeze)(struct device *), (*thaw)(struct device *);
    int (*poweroff)(struct device *), (*restore)(struct device *);
};
struct device {
    struct { int usage_count, child_count; bool ignore_children, needs_force_resume, smart_suspend; } power;
    const struct dev_pm_ops *ops;
    bool suspended;
    int disabled, clocks, fail_suspend, fail_resume;
};
#define atomic_read(p) (*(p))
#define GET_CALLBACK(dev, cb) ((dev)->ops->cb)
#define pm_sleep_ptr(p) (p)
#define SET_RUNTIME_PM_OPS(s, r, i) .runtime_suspend = s, .runtime_resume = r,
#define dev_pm_enable_wake_irq_check(d, b) ((void)(d), (void)(b))
#define dev_pm_enable_wake_irq_complete(d) ((void)(d))
#define dev_pm_disable_wake_irq_check(d, b) ((void)(d), (void)(b))
#define pm_runtime_mark_last_busy(d) ((void)(d))
static void pm_runtime_disable(struct device *d) { d->disabled++; }
static void pm_runtime_enable(struct device *d) { assert(d->disabled > 0); d->disabled--; }
static bool pm_runtime_status_suspended(struct device *d) { return d->suspended; }
static bool dev_pm_smart_suspend(struct device *d) { return d->power.smart_suspend; }
static void pm_runtime_set_suspended(struct device *d) { d->suspended = true; }
static int clock_suspend(struct device *d) {
    if (d->fail_suspend) return -5;
    assert(d->clocks == 1); d->clocks--; return 0;
}
static int clock_resume(struct device *d) {
    if (d->fail_resume) return -5;
    assert(d->clocks == 0); d->clocks++; return 0;
}
'''
harness += helpers
for driver in ('combo', 'usb'):
    source = (kernel / f'drivers/phy/qualcomm/phy-qcom-qmp-{driver}.c').read_text()
    ops = re.search(rf'static const struct dev_pm_ops qmp_{driver}_pm_ops = \{{.*?^}};', source, re.M | re.S)[0]
    harness += f'\n#define qmp_{driver}_runtime_suspend clock_suspend\n#define qmp_{driver}_runtime_resume clock_resume\n' + ops
harness += r'''
int main(void) {
const struct dev_pm_ops *drivers[] = { &qmp_combo_pm_ops, &qmp_usb_pm_ops };
for (unsigned int i = 0; i < sizeof(drivers) / sizeof(drivers[0]); i++) {
    const struct dev_pm_ops *ops = drivers[i];
    assert(ops->suspend && ops->resume);
    assert(!ops->freeze && !ops->thaw && !ops->poweroff && !ops->restore);
    for (int policy = 0; policy <= 1; policy++) {
        /* PM preparation reference, active generic-PHY child */
        struct device d = { .ops = ops, .clocks = 1,
            .power = { .usage_count = 1 + policy, .child_count = 1 } };
        for (int cycle = 0; cycle < 100; cycle++) {
            assert(ops->suspend(&d) == 0 && d.clocks == 0 && d.disabled == 1);
            assert(d.power.needs_force_resume);
            assert(ops->resume(&d) == 0 && d.clocks == 1 && d.disabled == 0);
            assert(!d.power.needs_force_resume && d.power.usage_count == 1 + policy);
        }
        d.fail_suspend = 1;
        assert(ops->suspend(&d) == -5 && d.clocks == 1 && d.disabled == 0);
        d.fail_suspend = 0;
        assert(ops->suspend(&d) == 0);
        d.fail_resume = 1;
        assert(ops->resume(&d) == -5 && d.clocks == 0 && d.disabled == 0 && d.suspended);
        assert(!d.power.needs_force_resume);
    }
    /* Already runtime-suspended provider, no duplicate clock operation */
    struct device idle = { .ops = ops, .suspended = true, .power = { .usage_count = 1 } };
    assert(ops->suspend(&idle) == 0 && idle.clocks == 0 && idle.disabled == 1);
    assert(ops->resume(&idle) == 0 && idle.clocks == 0 && idle.disabled == 0);
    /* No consumer reference, resume deferred to runtime PM */
    struct device unused = { .ops = ops, .clocks = 1, .power = { .usage_count = 1 } };
    assert(ops->suspend(&unused) == 0 && unused.clocks == 0 && unused.suspended);
    assert(ops->resume(&unused) == 0 && unused.clocks == 0 && unused.disabled == 0);
}
return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    binary = str(Path(directory) / 'qmp-system-pm-check')
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-x', 'c', '-o', binary, '-'],
                   input=harness, text=True, check=True)
    subprocess.run([binary], cwd=directory, check=True)
print('QMP system PM: both registrations, native helpers, 100 cycles, idle and error paths passed')
