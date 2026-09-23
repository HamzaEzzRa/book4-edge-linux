// SPDX-License-Identifier: GPL-2.0
/* Cached DDR/RPMh votes after device suspension, no hardware access
 * Private types: matching kernel source/config required
 */
#include <linux/clk.h>
#include <linux/clk-provider.h>
#include <linux/device.h>
#include <linux/interconnect.h>
#include <linux/interconnect-provider.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_platform.h>
#include <linux/platform_device.h>
#include <linux/pci.h>
#include <linux/phy/phy.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/syscore_ops.h>
#include <linux/usb.h>
#include <linux/usb/hcd.h>
#include "internal.h"
#include "qcom/icc-rpmh.h"
#include "rpmh-internal.h"

/* Source-validated private layouts: drivers/soc/qcom/rpmh.c */
struct cache_req {
	u32 addr;
	u32 sleep_val;
	u32 wake_val;
	struct list_head list;
};

struct batch_cache_req {
	struct list_head list;
	int count;
	struct rpmh_request rpm_msgs[];
};

/* Source-validated clk_core prefix through prepare_count: drivers/clk/clk.c
 * Cached counts only
 * clk_hw_is_prepared(): provider resume/hardware-access risk at syscore
 */
struct clk_core {
	const char *name;
	const struct clk_ops *ops;
	struct clk_hw *hw;
	struct module *owner;
	struct device *dev;
	struct hlist_node rpm_node;
	struct device_node *of_node;
	struct clk_core *parent;
	struct clk_parent_map *parents;
	u8 num_parents;
	u8 new_parent_index;
	unsigned long rate;
	unsigned long req_rate;
	unsigned long new_rate;
	struct clk_core *new_parent;
	struct clk_core *new_child;
	unsigned long flags;
	bool orphan;
	bool rpm_enabled;
	unsigned int enable_count;
	unsigned int prepare_count;
};

struct observed_clock {
	struct list_head list;
	struct clk *clk;
	struct device *consumer;
	unsigned int index;
};
static LIST_HEAD(clocks);

static void put_clocks(void)
{
	struct observed_clock *c, *next;

	list_for_each_entry_safe(c, next, &clocks, list) {
		list_del(&c->list);
		clk_put(c->clk);
		put_device(c->consumer);
		kfree(c);
	}
}

static int record_device_pm(struct device *dev, void *unused)
{
	pr_info("book4-votes: init-PM device=%s usage=%d children=%d state=%d disable=%u auto=%u no_callbacks=%u\n",
		dev_name(dev), atomic_read(&dev->power.usage_count),
		atomic_read(&dev->power.child_count), READ_ONCE(dev->power.runtime_status),
		dev->power.disable_depth, dev->power.runtime_auto, dev->power.no_callbacks);
	if (dev->class && !strcmp(dev->class->name, "phy")) {
		struct phy *phy = to_phy(dev);

		pr_info("book4-votes: PHY device=%s init=%d power=%d\n",
			dev_name(dev), READ_ONCE(phy->init_count), READ_ONCE(phy->power_count));
	}
	return device_for_each_child(dev, NULL, record_device_pm);
}

static int collect_clocks(struct device *dev, void *unused)
{
	int i, count;

	if (dev->driver && !strcmp(dev->driver->name, "xhci-hcd")) {
		struct usb_hcd *hcd = dev_get_drvdata(dev);

		if (hcd)
			pr_info("book4-votes: HCD device=%s skip_phy=%u roothub_phy=%u\n",
				dev_name(dev), hcd->skip_phy_initialization, !!hcd->phy_roothub);
	}
	/* ponytail: bound platform DT consumers only, wider bus coverage for unexplained XO */
	if (!dev->driver || !dev->of_node)
		return 0;
	if (strstr(dev_name(dev), ".phy"))
		record_device_pm(dev, NULL);
	count = of_clk_get_parent_count(dev->of_node);
	for (i = 0; i < count; i++) {
		struct observed_clock *c;
		struct clk_hw *hw;
		struct clk *clk = of_clk_get(dev->of_node, i);

		if (IS_ERR_OR_NULL(clk)) {
			pr_info("book4-votes: CCF unavailable consumer=%s index=%d error=%ld\n",
				dev_name(dev), i, clk ? PTR_ERR(clk) : -ENOENT);
			continue;
		}
		hw = __clk_get_hw(clk);
		if (!hw || hw->core->hw != hw ||
		    hw->core->flags != clk_hw_get_flags(hw)) {
			clk_put(clk);
			return -EINVAL;
		}
		c = kzalloc(sizeof(*c), GFP_KERNEL);
		if (!c) {
			clk_put(clk);
			return -ENOMEM;
		}
		c->clk = clk;
		c->consumer = get_device(dev);
		c->index = i;
		list_add_tail(&c->list, &clocks);
	}
	return 0;
}

static void record_clocks(const char *phase)
{
	struct observed_clock *c;
	unsigned int count = 0;

	pr_info("book4-votes: CCF begin phase=%s\n", phase);
	list_for_each_entry(c, &clocks, list) {
		struct clk_core *core = __clk_get_hw(c->clk)->core;
		unsigned int prepared = READ_ONCE(core->prepare_count);
		unsigned int enabled = READ_ONCE(core->enable_count);

		count++;
		if (prepared || enabled)
			/* Shared clock counts, not per-consumer ownership */
			pr_info("book4-votes: CCF clock=%s prepare=%u enable=%u consumer=%s index=%u\n",
				core->name, prepared, enabled, dev_name(c->consumer), c->index);
		/* Cached PIPE provider self-votes, no runtime get */
		if (prepared && strstr(core->name, "pipe")) {
			for (; core; core = core->parent) {
				struct device *dev = core->dev;

				if (!dev)
					continue;
				pr_info("book4-votes: clock-PM clock=%s provider=%s rpm_enabled=%u prepare=%u usage=%d children=%d state=%d\n",
					core->name, dev_name(dev), READ_ONCE(core->rpm_enabled), READ_ONCE(core->prepare_count),
					atomic_read(&dev->power.usage_count),
					atomic_read(&dev->power.child_count),
					READ_ONCE(dev->power.runtime_status));
			}
		}
	}
	pr_info("book4-votes: CCF end phase=%s handles=%u\n", phase, count);
}

static struct device *rsc_dev;
static struct rsc_drv *rsc;
static struct platform_device *gpu;
static struct icc_path *path;
static struct icc_node *ebi;
static struct pci_dev *ports[2];

static void record_pci(void)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(ports); i++) {
		struct pci_dev *dev = ports[i];

		if (dev)
			pr_info("book4-votes: PCI=%s state=%d bridge_d3=%u hotplug=%u pciehp=%u no_d3cold=%u\n",
				pci_name(dev), dev->current_state, dev->bridge_d3,
				dev->is_hotplug_bridge, dev->is_pciehp, dev->no_d3cold);
	}
}

static void record_rpmh(const char *phase)
{
	struct rpmh_ctrlr *ctrlr = &rsc->client;
	struct cache_req *req;
	struct batch_cache_req *batch;
	unsigned long flags;
	int i, j;

	/* rpmh_flush() constraint: nonblocking syscore cache lock */
	if (!spin_trylock_irqsave(&ctrlr->cache_lock, flags)) {
		pr_info("book4-votes: RPMh phase=%s skipped: cache busy\n", phase);
		return;
	}
	pr_info("book4-votes: RPMh begin phase=%s dirty=%u\n", phase, ctrlr->dirty);
	list_for_each_entry(req, &ctrlr->cache, list)
		/* 0xffffffff: unset, not an explicit vote */
		pr_info("book4-votes: RPMh addr=%#x sleep=%#x wake=%#x\n",
			req->addr, req->sleep_val, req->wake_val);
	list_for_each_entry(batch, &ctrlr->batch_cache, list) {
		for (i = 0; i < batch->count; i++) {
			const struct tcs_request *msg = &batch->rpm_msgs[i].msg;

			if (msg->state != RPMH_SLEEP_STATE)
				continue;
			for (j = 0; j < msg->num_cmds; j++)
				pr_info("book4-votes: RPMh batch addr=%#x sleep=%#x\n",
					msg->cmds[j].addr, msg->cmds[j].data);
		}
	}
	pr_info("book4-votes: RPMh end phase=%s\n", phase);
	spin_unlock_irqrestore(&ctrlr->cache_lock, flags);
}

static int record_votes(void *unused)
{
	struct qcom_icc_node *qn = ebi->data;
	struct icc_req *req;
	size_t i;

	/* Syscore: frozen tasks, offline secondary CPUs, disabled IRQs
	 * No sleeping locks or QMP messages
	 */
	pr_info("book4-votes: DDR sleep avg=%llu peak=%llu kB/s init=%u/%u\n",
		qn->sum_avg[QCOM_ICC_BUCKET_SLEEP],
		qn->max_peak[QCOM_ICC_BUCKET_SLEEP], ebi->init_avg, ebi->init_peak);
	hlist_for_each_entry(req, &ebi->req_list, req_node) {
		if (req->enabled && (req->avg_bw || req->peak_bw))
			pr_info("book4-votes: client=%s tag=%u avg=%u peak=%u kB/s\n",
				req->dev ? dev_name(req->dev) : "none",
				req->tag, req->avg_bw, req->peak_bw);
	}
	for (i = 0; i < qn->num_bcms; i++) {
		struct qcom_icc_bcm *bcm = qn->bcms[i];

		pr_info("book4-votes: BCM=%s sleep x=%llu y=%llu\n",
			bcm->name, bcm->vote_x[QCOM_ICC_BUCKET_SLEEP],
			bcm->vote_y[QCOM_ICC_BUCKET_SLEEP]);
	}
	record_pci();
	record_clocks("suspend");
	record_rpmh("suspend");
	return 0;
}

static const struct syscore_ops ops = { .suspend = record_votes };
static struct syscore observer = { .ops = &ops };

static int __init votes_init(void)
{
	struct device_node *np;
	int ret;

	np = of_find_node_by_path("/soc@0/gpu@3d00000");
	if (!np)
		return -ENODEV;
	gpu = of_find_device_by_node(np);
	of_node_put(np);
	if (!gpu)
		return -ENODEV;
	/* Zero-vote node references, no icc_set_bw() */
	path = of_icc_get(&gpu->dev, "gfx-mem");
	if (IS_ERR_OR_NULL(path)) {
		ret = path ? PTR_ERR(path) : -ENODEV;
		goto put_device;
	}
	ebi = path->reqs[path->num_nodes - 1].node;
	if (!ebi->data || strcmp(((struct qcom_icc_node *)ebi->data)->name, "ebi")) {
		ret = -EINVAL;
		goto put_path;
	}
	rsc_dev = bus_find_device_by_name(&platform_bus_type, NULL, "17500000.rsc");
	if (!rsc_dev) {
		ret = -ENODEV;
		goto put_path;
	}
	rsc = dev_get_drvdata(rsc_dev);
	if (!rsc_dev->driver || strcmp(rsc_dev->driver->name, "rpmh") ||
	    !rsc || rsc->dev != rsc_dev) {
		ret = -ENODEV;
		goto put_rsc;
	}
	ret = bus_for_each_dev(&platform_bus_type, NULL, NULL, collect_clocks);
	if (ret) {
		put_clocks();
		goto put_rsc;
	}
	ports[0] = pci_get_domain_bus_and_slot(4, 0, PCI_DEVFN(0, 0));
	ports[1] = pci_get_domain_bus_and_slot(4, 1, PCI_DEVFN(0, 0));
	record_pci();
	record_clocks("awake");
	record_rpmh("awake");
	register_syscore(&observer);
	pr_info("book4-votes: ready, observing %s; no bandwidth vote added\n", ebi->name);
	return 0;
put_rsc:
	put_device(rsc_dev);
put_path:
	icc_put(path);
put_device:
	put_device(&gpu->dev);
	return ret;
}

static void __exit votes_exit(void)
{
	unregister_syscore(&observer);
	put_clocks();
	pci_dev_put(ports[1]);
	pci_dev_put(ports[0]);
	put_device(rsc_dev);
	icc_put(path);
	put_device(&gpu->dev);
}

module_init(votes_init);
module_exit(votes_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Book4 final-suspend DDR vote observer");
