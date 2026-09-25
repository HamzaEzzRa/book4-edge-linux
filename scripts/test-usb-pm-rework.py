#!/usr/bin/env python3
"""Extracted USB ownership and DWC3 resume helpers, no hardware access
Usage: test-usb-pm-rework.py KERNEL_TREE [SOURCE_TREE]
Includes provider errors and host runtime/system transitions with modeled PM boundaries
Excluded: full PM engine, hardware fault injection, peripheral wake and energy
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if sys.argv[1:] in (['-h'], ['--help']):
    print(__doc__)
    raise SystemExit(0)
if len(sys.argv) not in (2, 3):
    print(__doc__, file=sys.stderr)
    raise SystemExit(2)
kernel = Path(sys.argv[1])
source = Path(sys.argv[-1])

def function(text, name):
    match = re.search(r'^(?:static )?(?:int|void) ' + name + r'\([^;]*?\n\{.*?^\}', text, re.M | re.S)
    assert match, name
    return match[0]

phy = (source / 'drivers/usb/core/phy.c').read_text()
hcd = (source / 'drivers/usb/core/hcd.c').read_text()
core = (source / 'drivers/usb/dwc3/core.c').read_text()
host = (source / 'drivers/usb/dwc3/host.c').read_text()
glue_source = (source / 'drivers/usb/dwc3/dwc3-qcom.c').read_text()
framework = (kernel / 'drivers/phy/phy-core.c').read_text()
root_type = re.search(r'struct usb_phy_roothub \{.*?\n\};', phy, re.S)[0]
setter = (function(phy, 'usb_phy_roothub_set_parent_owned') if 'void usb_phy_roothub_set_parent_owned(' in phy else
          'void usb_phy_roothub_set_parent_owned(struct usb_phy_roothub *r) { (void)r; }')
roots = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <errno.h>
struct list_head { struct list_head *next, *prev; };
#define entry(p) ((struct usb_phy_roothub *)((char *)(p) - offsetof(struct usb_phy_roothub, list)))
#define list_for_each_entry(p,h,m) for (p=entry((h)->next); &p->m!=(h); p=entry(p->m.next))
#define list_for_each_entry_reverse(p,h,m) for (p=entry((h)->prev); &p->m!=(h); p=entry(p->m.prev))
#define list_for_each_entry_continue_reverse(p,h,m) for (p=entry(p->m.prev); &p->m!=(h); p=entry(p->m.prev))
enum phy_mode { PHY_MODE_USB_HOST, PHY_MODE_USB_HOST_SS };
struct phy { int init, power, mode, calibrations, connects, disconnects, fail_init, fail_power; bool ss; };
struct device { bool wake; };
static int device_may_wakeup(struct device *d) { return d->wake; }
static int phy_init(struct phy *p) { if (p->fail_init) return -EIO; p->init++; return 0; }
static int phy_exit(struct phy *p) { assert(p->init>0); p->init--; return 0; }
static int phy_power_on(struct phy *p) { if (p->fail_power) return -EIO; assert(p->init); p->power++; return 0; }
static int phy_power_off(struct phy *p) { assert(p->power>0); p->power--; return 0; }
static int phy_set_mode(struct phy *p, enum phy_mode m) { if (m==PHY_MODE_USB_HOST_SS && !p->ss) return -EINVAL; p->mode=m; return 0; }
static int phy_calibrate(struct phy *p) { assert(p->init && p->power); p->calibrations++; return 0; }
static int phy_notify_connect(struct phy *p, int port) { assert(port==1); p->connects++; return 0; }
static int phy_notify_disconnect(struct phy *p, int port) { assert(port==1); p->disconnects++; return 0; }
'''
roots += root_type + '\n' + setter + '\n'
for name in ('init', 'exit', 'set_mode', 'calibrate', 'notify_connect', 'notify_disconnect', 'power_on', 'power_off', 'suspend', 'resume'):
    roots += function(phy, 'usb_phy_roothub_' + name) + '\n'
roots += r'''
static void link(struct usb_phy_roothub *r, struct usb_phy_roothub *e, struct phy *p) {
    r->list.next=&e[0].list; r->list.prev=&e[1].list;
    for (int i=0; i<2; i++) {
        e[i].phy=&p[i]; e[i].list.prev=i ? &e[0].list : &r->list;
        e[i].list.next=i ? &r->list : &e[1].list;
    }
}
int main(void) {
    usb_phy_roothub_set_parent_owned(NULL);
    assert(!usb_phy_roothub_init(NULL) && !usb_phy_roothub_exit(NULL));
    assert(!usb_phy_roothub_power_on(NULL)); usb_phy_roothub_power_off(NULL);
    for (int owned=0; owned<2; owned++) for (int wake=0; wake<2; wake++) {
        struct usb_phy_roothub r={0}, e[2]={0}; struct phy p[2]={0}; struct device d={wake};
        link(&r,e,p);
        if (owned) { usb_phy_roothub_set_parent_owned(&r); p[0].init=p[1].init=1; p[0].power=p[1].power=1; }
        assert(!usb_phy_roothub_init(&r));
        assert(p[0].init==1 && p[1].init==1);
        assert(!usb_phy_roothub_power_on(&r));
        assert(p[0].power==1 && p[1].power==1);
        assert(usb_phy_roothub_set_mode(&r,PHY_MODE_USB_HOST_SS)==-EINVAL);
        assert(!usb_phy_roothub_set_mode(&r,PHY_MODE_USB_HOST));
        assert(p[0].mode==PHY_MODE_USB_HOST && p[1].mode==PHY_MODE_USB_HOST);
        p[0].ss=p[1].ss=true;
        assert(!usb_phy_roothub_set_mode(&r,PHY_MODE_USB_HOST_SS));
        assert(p[0].mode==PHY_MODE_USB_HOST_SS && p[1].mode==PHY_MODE_USB_HOST_SS);
        for (int i=0; i<100; i++) {
            assert(!usb_phy_roothub_calibrate(&r));
            assert(!usb_phy_roothub_notify_connect(&r,1));
            assert(!usb_phy_roothub_notify_disconnect(&r,1));
            assert(!usb_phy_roothub_suspend(&d,&r));
            for (int j=0; j<2; j++) { assert(p[j].init==(owned||wake)); assert(p[j].power==owned); }
            assert(!usb_phy_roothub_resume(&d,&r));
            for (int j=0; j<2; j++) assert(p[j].init==1 && p[j].power==1);
        }
        usb_phy_roothub_power_off(&r); assert(!usb_phy_roothub_exit(&r));
        for (int j=0; j<2; j++) {
            assert(p[j].init==owned && p[j].power==owned);
            assert(p[j].calibrations==100 && p[j].connects==100 && p[j].disconnects==100);
        }
    }
    for (int fail=0; fail<2; fail++) {
        struct usb_phy_roothub r={0}, e[2]={0}; struct phy p[2]={0};
        link(&r,e,p); p[fail].fail_init=1;
        assert(usb_phy_roothub_init(&r)==-EIO); assert(!p[0].init && !p[1].init);
        p[fail].fail_init=0; assert(!usb_phy_roothub_init(&r)); p[fail].fail_power=1;
        assert(usb_phy_roothub_power_on(&r)==-EIO); assert(!p[0].power && !p[1].power);
        p[fail].fail_power=0; assert(!usb_phy_roothub_power_on(&r));
        usb_phy_roothub_power_off(&r); assert(!usb_phy_roothub_exit(&r));
    }
}
'''
resume = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <errno.h>
#define ENOTSUPP 524
#define DWC3_GCTL_PRTCAP_DEVICE 1
#define DWC3_GCTL_PRTCAP_HOST 2
#define DWC3_GCTL_PRTCAP_OTG 3
#define DWC3_OTG_ROLE_DEVICE 1
#define DWC3_OTG_ROLE_HOST 2
#define DWC3_GUSB2PHYCFG(i) (i)
#define DWC3_GUSB3PIPECTL(i) (8+(i))
#define DWC3_GUSB2PHYCFG_SUSPHY 1
#define DWC3_GUSB3PIPECTL_SUSPHY 1
#define DWC3_GUSB2PHYCFG_ENBLSLPM 2
#define DWC3_GUCTL3 16
#define DWC3_GUCTL3_SPLITDISABLE 4
#define PMSG_SUSPEND 1
#define PMSG_RESUME 2
#define PMSG_AUTO_SUSPEND 0x100
#define PMSG_AUTO_RESUME 0x102
#define PMSG_IS_AUTO(m) ((m)&0x100)
typedef unsigned int u32;
typedef int pm_message_t;
struct device { bool enabled, wake, suspended, pinctrl; int refs, result, resume_calls; void *data; struct device *parent; };
struct phy { struct device dev; };
struct dwc3 {
    struct device *dev; struct phy *usb2_generic_phy[4], *usb3_generic_phy[4];
    int num_usb2_ports, num_usb3_ports, current_dr_role, current_otg_role, irq_gadget;
    bool needs_full_reinit, dis_u2_susphy_quirk, dis_enblslpm_quirk, susphy_state, dis_split_quirk, pm_suspended, pending_events;
};
struct usb_hcd { struct { struct device *controller; } self; };
int dwc3_runtime_resume(struct dwc3 *dwc);
static int mmio, full_error, full_calls, full_ready, runtime_depth, active_error, gadget_error;
int pm_runtime_resume(struct device *d) {
    assert(d->refs>0);
    d->resume_calls++;
    if (!d->enabled) return -EACCES;
    if (d->result<0) return d->result;
    if (!d->suspended) return 1;
    if (d->data) {
        int ret=dwc3_runtime_resume(d->data);
        if (ret) return ret;
    }
    d->suspended=false;
    return 0;
}
static bool pm_runtime_enabled(struct device *d) { return d->enabled; }
static int pm_runtime_get_sync(struct device *d) { d->refs++; return d->result; }
static int pm_runtime_put_sync(struct device *d) { assert(d->refs>0); d->refs--; return 0; }
static bool pm_runtime_suspended(struct device *d) { return d->suspended; }
static bool device_may_wakeup(struct device *d) { return d->wake; }
static void *dev_get_drvdata(struct device *d) { return d->data; }
static void pm_runtime_disable(struct device *d) { (void)d; runtime_depth++; }
static void pm_runtime_enable(struct device *d) { (void)d; runtime_depth--; }
static int pm_runtime_set_active(struct device *d) { if (active_error) return active_error; d->suspended=false; return 0; }
static void pm_runtime_set_suspended(struct device *d) { d->suspended=true; }
static void pinctrl_pm_select_sleep_state(struct device *d) { (void)d; }
static void pinctrl_pm_select_default_state(struct device *d) { (void)d; }
static bool dev_pinctrl(struct device *d) { return d->pinctrl; }
static void pm_runtime_put(struct device *d) { assert(d->refs>0); d->refs--; }
static void pm_runtime_mark_last_busy(struct device *d) { (void)d; }
static void enable_irq(int irq) { (void)irq; }
static void phy_accessible(struct phy *p) {
    if (!p || !p->dev.enabled) return;
    assert(p->dev.refs>0);
    assert(p->dev.parent->enabled && !p->dev.parent->suspended);
}
static void accessible(struct dwc3 *d) {
    if (full_ready) return;
    for (int i=0; i<d->num_usb2_ports; i++) phy_accessible(d->usb2_generic_phy[i]);
    for (int i=0; i<d->num_usb3_ports; i++) phy_accessible(d->usb3_generic_phy[i]);
}
static u32 dwc3_readl(struct dwc3 *d, int reg) { (void)reg; accessible(d); mmio++; return 3; }
static void dwc3_writel(struct dwc3 *d, int reg, u32 val) { (void)reg; (void)val; accessible(d); mmio++; }
static void dwc3_enable_susphy(struct dwc3 *d, bool v) { (void)v; accessible(d); mmio++; }
static int dwc3_core_init_for_resume(struct dwc3 *d) { (void)d; full_calls++; if (!full_error) full_ready=1; return full_error; }
static void dwc3_set_prtcap(struct dwc3 *d, int r, bool v) { (void)r; (void)v; accessible(d); }
static int dwc3_gadget_suspend(struct dwc3 *d) { (void)d; return gadget_error; }
static void dwc3_gadget_resume(struct dwc3 *d) { accessible(d); }
static void dwc3_core_exit(struct dwc3 *d) { (void)d; full_ready=0; }
static void synchronize_irq(int irq) { (void)irq; }
static void usleep_range(int lo, int hi) { (void)lo; (void)hi; }
static void dwc3_otg_exit(struct dwc3 *d) { (void)d; }
static void dwc3_otg_init(struct dwc3 *d) { (void)d; }
static void dwc3_otg_host_init(struct dwc3 *d) { (void)d; }
'''
for name in ('phy_pm_runtime_get_sync', 'phy_pm_runtime_put_sync'):
    resume += function(framework, name) + '\n'
if 'static int dwc3_resume_phy_parent(' in core:
    resume += function(core, 'dwc3_resume_phy_parent') + '\n'
for name in ('dwc3_suspend_common', 'dwc3_resume_common', 'dwc3_runtime_resume', 'dwc3_pm_suspend', 'dwc3_pm_resume', 'dwc3_pm_complete', 'dwc3_pm_prepare'):
    resume += function(core, name) + '\n'
resume += (function(host, 'dwc3_xhci_resume_quirk') if 'static int dwc3_xhci_resume_quirk(' in host else
           'static int dwc3_xhci_resume_quirk(struct usb_hcd *h) { (void)h; return 0; }') + '\n'
resume += r'''
static struct phy p[8]; static struct device dev, child, providers[8];
static struct dwc3 dwc; static struct usb_hcd hcd;
static void setup(int n2,int n3) {
    dev=(struct device){.enabled=true,.wake=true,.refs=1}; child=(struct device){.parent=&dev};
    dwc=(struct dwc3){.dev=&dev,.num_usb2_ports=n2,.num_usb3_ports=n3,.current_dr_role=DWC3_GCTL_PRTCAP_HOST,.dis_u2_susphy_quirk=true,.dis_enblslpm_quirk=true,.dis_split_quirk=true};
    dev.data=&dwc; hcd.self.controller=&child;
    for (int i=0;i<8;i++) {
        providers[i]=(struct device){.enabled=true,.refs=1};
        p[i]=(struct phy){.dev={.enabled=true,.refs=1,.parent=&providers[i]}};
    }
    for (int i=0;i<n2;i++) dwc.usb2_generic_phy[i]=&p[i];
    for (int i=0;i<n3;i++) dwc.usb3_generic_phy[i]=&p[4+i];
    mmio=full_error=full_calls=full_ready=runtime_depth=active_error=gadget_error=0;
}
static void refs(int expected) {
    for (int i=0;i<dwc.num_usb2_ports;i++) if (dwc.usb2_generic_phy[i] && dwc.usb2_generic_phy[i]->dev.enabled) assert(p[i].dev.refs==expected);
    for (int i=0;i<dwc.num_usb3_ports;i++) if (dwc.usb3_generic_phy[i] && dwc.usb3_generic_phy[i]->dev.enabled) assert(p[4+i].dev.refs==expected);
}
int main(void) {
    for (int auto_pm=0;auto_pm<2;auto_pm++) for (int n2=0;n2<=4;n2++) for (int n3=0;n3<=4;n3++) {
        for (int fail=-1;fail<n2+n3;fail++) {
            setup(n2,n3);
            if (auto_pm) assert(!dwc3_suspend_common(&dwc,PMSG_AUTO_SUSPEND));
            else { assert(!dwc3_pm_suspend(&dwc)); assert(dwc3_xhci_resume_quirk(&hcd)==-EHOSTDOWN); }
            refs(0); mmio=0;
            if (fail>=0) p[fail<n2?fail:4+fail-n2].dev.result=-EIO;
            int ret=auto_pm?dwc3_resume_common(&dwc,PMSG_AUTO_RESUME):dwc3_pm_resume(&dwc);
            if (fail>=0) {
                assert(ret==-EIO && mmio==0); refs(0);
                if (!auto_pm) { assert(dwc.pm_suspended); assert(dwc3_xhci_resume_quirk(&hcd)==-EHOSTDOWN); dwc3_pm_complete(&dwc); assert(mmio==0); }
                for (int i=0;i<8;i++) p[i].dev.result=0;
                ret=auto_pm?dwc3_resume_common(&dwc,PMSG_AUTO_RESUME):dwc3_pm_resume(&dwc);
            }
            assert(!ret && runtime_depth==0); refs(1);
            if (!auto_pm) { assert(!dwc.pm_suspended); assert(!dwc3_xhci_resume_quirk(&hcd)); dwc3_pm_complete(&dwc); }
        }
    }
    setup(4,2); dwc.usb2_generic_phy[0]=NULL; p[1].dev.enabled=false; p[4].dev.result=1;
    assert(!dwc3_pm_suspend(&dwc)); assert(!dwc3_pm_resume(&dwc)); refs(1);
    for (int i=0;i<100;i++) { assert(!dwc3_pm_suspend(&dwc)); assert(!dwc3_pm_resume(&dwc)); refs(1); }
    for (int role=1;role<=3;role++) {
        setup(0,0); dwc.current_dr_role=role; dwc.needs_full_reinit=true; dwc.current_otg_role=DWC3_OTG_ROLE_HOST;
        assert(!dwc3_pm_suspend(&dwc)); mmio=0; full_error=-EIO;
        assert(dwc3_pm_resume(&dwc)==-EIO && mmio==0 && dwc.pm_suspended);
        assert(dwc3_xhci_resume_quirk(&hcd)==-EHOSTDOWN); dwc3_pm_complete(&dwc); assert(mmio==0);
        full_error=0; assert(!dwc3_pm_resume(&dwc)); assert(!dwc.pm_suspended && !runtime_depth);
    }
    setup(1,1); assert(!dwc3_pm_suspend(&dwc)); mmio=0; active_error=-EBUSY;
    assert(dwc3_pm_resume(&dwc)==-EBUSY && mmio==0 && dwc.pm_suspended && !runtime_depth);
    assert(dwc3_xhci_resume_quirk(&hcd)==-EHOSTDOWN); dwc3_pm_complete(&dwc); assert(mmio==0);
    setup(0,0); dwc.current_dr_role=DWC3_GCTL_PRTCAP_DEVICE; gadget_error=-EBUSY;
    assert(dwc3_pm_suspend(&dwc)==-EBUSY && !dwc.pm_suspended);
    for (int failure=0;failure<8;failure++) {
        setup(4,4);
        for (int i=0;i<8;i++) { p[i].dev.refs++; p[i].dev.result=1; }
        assert(!dwc3_pm_suspend(&dwc)); refs(1); mmio=0;
        providers[failure].suspended=true;
        providers[failure].result=-EIO;
        assert(dwc3_pm_resume(&dwc)==-EIO);
        assert(mmio==0 && dev.suspended && dwc.pm_suspended && !runtime_depth);
        refs(1);
        assert(dwc3_runtime_resume(&dwc)==-EHOSTDOWN && mmio==0);
        assert(dwc3_xhci_resume_quirk(&hcd)==-EHOSTDOWN);
        dwc3_pm_complete(&dwc); assert(mmio==0);
        providers[failure].result=0;
        assert(!dwc3_pm_resume(&dwc)); refs(2);
        assert(!dev.suspended && !dwc.pm_suspended && !runtime_depth);
        for (int i=0;i<8;i++) assert(providers[i].refs==1);
        for (int i=0;i<8;i++) p[i].dev.refs--;
        refs(1);
    }
    setup(1,1); assert(!dwc3_pm_suspend(&dwc)); mmio=0;
    providers[0].enabled=false;
    assert(dwc3_pm_resume(&dwc)==-EHOSTDOWN && mmio==0);
    assert(!providers[0].resume_calls && dwc.pm_suspended);
    providers[0].enabled=true;
    assert(!dwc3_pm_resume(&dwc)); refs(1);
    setup(1,1);
    assert(!dwc3_pm_prepare(&dwc) && !dev.suspended);
    for (int cycle=0;cycle<100;cycle++) {
        assert(!dwc3_suspend_common(&dwc,PMSG_AUTO_SUSPEND)); refs(0);
        dev.suspended=true;
        p[0].dev.refs++; p[4].dev.refs++;
        assert(!dwc3_pm_prepare(&dwc) && !dev.suspended); refs(2);
        assert(!dwc3_pm_suspend(&dwc)); refs(1);
        assert(!dwc3_pm_resume(&dwc)); refs(2);
        dwc3_pm_complete(&dwc);
        p[0].dev.refs--; p[4].dev.refs--;
        refs(1);
        assert(providers[0].refs==1 && providers[4].refs==1);
    }
    setup(1,1); dev.suspended=true; dev.result=-EIO;
    assert(dwc3_pm_prepare(&dwc)==-EIO && dev.suspended);
    setup(0,0); dwc.current_dr_role=DWC3_GCTL_PRTCAP_DEVICE; dev.suspended=true;
    assert(dwc3_pm_prepare(&dwc)==1 && dev.suspended && !dev.resume_calls);
    dev.pinctrl=true; assert(!dwc3_pm_prepare(&dwc) && dev.suspended);
}
'''
glue = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <errno.h>
struct dwc3 { int unused; };
struct dwc3_qcom { struct dwc3 dwc; bool pm_suspended; };
struct device { struct dwc3 *dwc; bool wake; };
static int glue_error, core_error, core_calls;
static struct dwc3 *dev_get_drvdata(struct device *d) { return d->dwc; }
static struct dwc3_qcom *to_dwc3_qcom(struct dwc3 *d) { return (struct dwc3_qcom *)d; }
static bool device_may_wakeup(struct device *d) { return d->wake; }
static int dwc3_qcom_resume(struct dwc3_qcom *q, bool wake) { (void)q; assert(wake); return glue_error; }
static int dwc3_pm_resume(struct dwc3 *d) { (void)d; core_calls++; return core_error; }
'''
glue += function(glue_source, 'dwc3_qcom_pm_resume') + r'''
int main(void) {
    struct dwc3_qcom q={.pm_suspended=true};
    struct device d={.dwc=&q.dwc,.wake=true};
    glue_error=-EIO;
    assert(dwc3_qcom_pm_resume(&d)==-EIO && q.pm_suspended && !core_calls);
    glue_error=0; core_error=-EHOSTDOWN;
    assert(dwc3_qcom_pm_resume(&d)==-EHOSTDOWN && q.pm_suspended && core_calls==1);
    core_error=0;
    assert(!dwc3_qcom_pm_resume(&d) && !q.pm_suspended && core_calls==2);
}
'''
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    for name, code in (('ownership', roots), ('resume', resume), ('glue', glue)):
        path = root / f'{name}.c'
        path.write_text(code)
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', str(path), '-o', str(root / name)], check=True)
        subprocess.run([str(root / name)], check=True, cwd=directory)
        print(name, 'actual-helper checks passed', flush=True)

prefix = function(hcd, 'usb_add_hcd').split('dev_info(')[0]
assert 'usb-phy-parent-owned' in prefix
assert prefix.index('usb-phy-parent-owned') < prefix.index('usb_phy_roothub_init(')
assert prefix.index('usb_phy_roothub_set_parent_owned(') < prefix.index('usb_phy_roothub_set_mode(') < prefix.index('usb_phy_roothub_power_on(')
assert 'PROPERTY_ENTRY_BOOL("usb-phy-parent-owned")' in host and 'XHCI_SKIP_PHY_INIT' not in host
assert int(re.search(r'props\[(\d+)\]', host)[1]) > host.count('props[prop_idx++] = PROPERTY_ENTRY_')
assert '.resume_quirk = dwc3_xhci_resume_quirk' in host
xhci = (kernel / 'drivers/usb/host/xhci-plat.c').read_text()
body = function(xhci, 'xhci_plat_resume_common')
assert body.index('xhci_priv_resume_quirk(') < body.index('xhci_resume(')
print('Property/mode wiring, property terminator and pre-xHCI guard checks passed')
