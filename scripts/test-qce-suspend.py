#!/usr/bin/env python3
"""QCE queue admission and suspend bandwidth, actual helpers
Gap: existing AF_ALG checks do not exercise QCE PM or request admission
Usage: python3 scripts/test-qce-suspend.py SOURCE_TREE
Excluded: DMA hardware, firmware vote delivery, energy
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip(), file=sys.stderr)
    sys.exit(0 if sys.argv[1:] in (['-h'], ['--help']) else 2)

source = (Path(sys.argv[1]) / 'drivers/crypto/qce/core.c').read_text()
names = ('qce_handle_queue', 'qce_req_done_work', 'qce_suspend', 'qce_resume')
functions = '\n'.join(re.search(r'static (?:int|void)(?: __maybe_unused)? ' + name +
                               r'\(.*?^}', source, re.M | re.S)[0] for name in names)
ops = re.search(r'static const struct dev_pm_ops qce_pm_ops = .*?^};', source, re.M | re.S)[0]
defines = re.search(r'^#define QCE_DEFAULT_MEM_BANDWIDTH\s+\d+', source, re.M)[0]
harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <pthread.h>
#define __maybe_unused
#define pm_sleep_ptr(p) (p)
#define container_of(p, t, m) ((t *)((char *)(p) - offsetof(t, m)))
struct device { void *data; };
struct crypto_async_request { int starts, completions; };
struct crypto_queue { struct crypto_async_request *items[8]; unsigned int qlen; };
struct work_struct { int scheduled; };
struct qce_device {
    struct crypto_queue queue;
    pthread_mutex_t lock;
    struct work_struct done_work;
    struct crypto_async_request *req;
    int result;
    bool suspended;
    void *mem_path;
};
struct dev_pm_ops { int (*suspend)(struct device *); int (*resume)(struct device *); };
struct lock_guard { pthread_mutex_t *lock; };
static struct lock_guard acquire(pthread_mutex_t *lock)
{ assert(!pthread_mutex_lock(lock)); return (struct lock_guard){ lock }; }
static void release(struct lock_guard *g)
{ if (g->lock) { assert(!pthread_mutex_unlock(g->lock)); g->lock = NULL; } }
#define guard(kind) struct lock_guard held __attribute__((cleanup(release))) = acquire
#define scoped_guard(kind, ptr) for (guard(kind)(ptr); held.lock; release(&held))
static void *dev_get_drvdata(struct device *dev) { return dev->data; }
static unsigned int crypto_queue_len(struct crypto_queue *q) { return q->qlen; }
static int crypto_enqueue_request(struct crypto_queue *q, struct crypto_async_request *r)
{ assert(q->qlen < 8); q->items[q->qlen++] = r; return -EINPROGRESS; }
static struct crypto_async_request *crypto_dequeue_request(struct crypto_queue *q)
{
    if (!q->qlen) return NULL;
    struct crypto_async_request *r = q->items[0];
    for (unsigned int i = 1; i < q->qlen; i++) q->items[i-1] = q->items[i];
    q->qlen--;
    return r;
}
static struct crypto_async_request *crypto_get_backlog(struct crypto_queue *q)
{ (void)q; return NULL; }
static void (*completion_hook)(void);
static void crypto_request_complete(struct crypto_async_request *r, int error)
{
    assert(error == 0);
    r->completions++;
    if (completion_hook) completion_hook();
}
static unsigned int bandwidth = 393600;
static int fail_votes;
static int icc_set_bw(void *path, unsigned int avg, unsigned int peak)
{
    (void)path;
    assert(avg == peak);
    if (fail_votes) { fail_votes--; bandwidth = 0; return -EIO; }
    bandwidth = avg;
    return 0;
}
static int qce_handle_request(struct crypto_async_request *r)
{ assert(bandwidth == 393600); r->starts++; return 0; }
static void schedule_work(struct work_struct *work) { work->scheduled++; }
'''
checks = r'''
static struct device dev;
static int callback_suspend_result;
static void try_suspend(void) { callback_suspend_result = qce_pm_ops.suspend(&dev); }
int main(void)
{
    struct qce_device qce = { .lock = PTHREAD_MUTEX_INITIALIZER };
    struct crypto_async_request a = {0}, b = {0};
    dev.data = &qce;
    assert(qce_handle_queue(&qce, &a) == -EINPROGRESS);
    assert(qce_pm_ops.suspend(&dev) == -EBUSY && bandwidth == 393600);
    assert(qce_handle_queue(&qce, &b) == -EINPROGRESS);
    completion_hook = try_suspend;
    qce_req_done_work(&qce.done_work);
    assert(callback_suspend_result == -EBUSY && bandwidth == 393600);
    completion_hook = NULL;
    qce_req_done_work(&qce.done_work);
    assert(a.starts == 1 && a.completions == 1 && b.starts == 1 && b.completions == 1);

    for (int cycle = 0; cycle < 3; cycle++) {
        assert(qce_pm_ops.suspend(&dev) == 0 && bandwidth == 0);
        assert(qce_pm_ops.suspend(&dev) == 0);
        assert(qce_handle_queue(&qce, &a) == -ESHUTDOWN);
        fail_votes = 1;
        assert(qce_pm_ops.resume(&dev) == -EIO);
        assert(qce_handle_queue(&qce, &a) == -ESHUTDOWN);
        assert(qce_pm_ops.resume(&dev) == 0 && bandwidth == 393600);
        assert(qce_handle_queue(&qce, &a) == -EINPROGRESS);
        qce_req_done_work(&qce.done_work);
        assert(a.starts == cycle + 2 && a.completions == cycle + 2);
    }

    fail_votes = 1;
    assert(qce_pm_ops.suspend(&dev) == -EIO && bandwidth == 393600);
    assert(qce_handle_queue(&qce, &a) == -EINPROGRESS);
    qce_req_done_work(&qce.done_work);
    fail_votes = 2;
    assert(qce_pm_ops.suspend(&dev) == -EIO);
    assert(qce_handle_queue(&qce, &a) == -ESHUTDOWN);
    assert(qce_pm_ops.resume(&dev) == 0 && bandwidth == 393600);
    assert(qce_handle_queue(&qce, &a) == -EINPROGRESS);
    qce_req_done_work(&qce.done_work);
    assert(a.starts == 6 && a.completions == 6);
    assert(!pthread_mutex_destroy(&qce.lock));
    return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    binary = str(Path(directory) / 'qce-pm')
    subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-pthread',
                    '-x', 'c', '-o', binary, '-'],
                   input=harness + defines + '\n' + functions + '\n' + ops + checks,
                   text=True, check=True, timeout=30)
    subprocess.run([binary], check=True, timeout=10)
print('QCE busy/queued requests, suspend admission, bandwidth failure and retry: passed')
