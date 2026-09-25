# QCE system-sleep bandwidth candidate

- Experimental, excluded from maintained patches 0001–0006
- Bound QCE: idle queue required before releasing the DDR vote
- Resume or suspend rollback: bandwidth restored before request admission
- Clocks, runtime PM, hibernation and installed modules unchanged
- Source/native evidence: `/var/log/book4-qce-suspend.2GDLSV/`
- Callback capture: `/var/log/book4-qce-core.PnUvLH/`
- Real-sleep capture: `/var/log/book4-qce-sleep.TxEFdi/`
- Real sleep: 789.402 s APSS, DDR D4 97.437%, zero sleep DDR vote, QCE remained bound
- Explicit CBC before/after real sleep passed, original module restored, recovery and preservation passed
- CX/AOSS entries: 0/0, drain unresolved
- DDR sleep vote: 393600/393600 → 0/0 kB/s with QCE loaded
- Eight awake QCE request rows: 393600/393600 kB/s before and after callbacks
- Explicit kernel Crypto API `cbc-aes-qce` AES-128 known answer: original driver and candidate before/after callbacks passed
- Hardware proof limited to the CBC vector, no AF_ALG mask bypass
- First load attempt: `modprobe -r` also removed `libdes`, candidate load failed, original module restored
- Retry: `rmmod qcrypto` retained dependencies, callbacks and automatic restoration passed
- Busy hardware queues, hardware fault recovery and energy savings unvalidated
- ICC API returns checked, firmware vote delivery not independently verified

## Behavior coverage

- Genuine gap: existing AF_ALG checks do not exercise QCE PM or request admission
- Actual queue, completion and PM helpers with mocked ICC/hardware boundaries
- Busy and queued requests, blocked admission, failed bandwidth changes, rollback and retry

```sh
python3 scripts/test-qce-suspend.py /path/to/kernel-with-candidate
```
