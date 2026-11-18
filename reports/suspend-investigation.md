# Suspend investigation — current status

## Decision

- Maintained baseline: patches 0001–0003, 0014–0011, native PCIe PM, original USB drivers
- USB experiments 0012–0015: excluded from the maintained series and next test boot
- USB blockers: [review findings](../patches/experimental/usb/README.md)
- Hook-preserving USB ownership/local-error rework: [boot/core-validated candidate](../patches/experimental/usb-rework/README.md), peripheral/wake pending, no PHY clock gating
- Original chronology and failures: [2026-09-20–22 archive](archive/suspend-2026-09-20-22.md)
- Checkpoint including observer: `74f1210`
- Deployment evidence: `/var/log/book4-review-fixes.5t5Ufq/`
- Rejected blacklist baseline: `/var/log/book4-pm-baseline.PfGPx7/`
- Probe-first baseline: `/var/log/book4-qce-probe.9e24x1/`
- Maintained real-sleep baseline: `/var/log/book4-suspend-probe.dizeUw/`
- Single-flag boot staging: `/var/log/book4-clk-unused.pzWOJp/`
- No-clock-ignore boot/core and callback-owner evidence: `/var/log/book4-clk-baseline.6DJROR/`
- Completed no-clock-ignore real sleep: `/var/log/book4-suspend-clk.B6LlwM/`
- Domain-flag boot staging: `/var/log/book4-pd-unused.dAD5En/`
- No-flags boot/core evidence: `/var/log/book4-pd-baseline.Q3WnGd/`
- Completed no-flags real sleep: `/var/log/book4-suspend-pd.3fjith/`
- Clock/domain source candidate: `/var/log/book4-clock-sync-fix.3Q99z4/`
- Clean candidate build and publication: `/var/log/book4-clock-kernel.KFFCOc/`
- Candidate boot/core and callback ownership: `/var/log/book4-clock-baseline.0PgY4A/`
- Completed candidate real sleep: `/var/log/book4-suspend-clock.qB0ZiX/`
- Normal QCE-loaded core: `/var/log/book4-qce-loaded-core.mp3Myn/`
- Completed normal QCE-loaded overnight: `/var/log/book4-overnight-qce.uZgywz/`
- Completed same-candidate long QCE opt-out: `/var/log/book4-overnight-noqce.NEvDTP/`
- USB rework source/native checks: `/var/log/book4-usb-rework.dWCMR6/`
- USB rework build/publication: `/var/log/book4-usb-build.vCO9zz/`
- USB rework boot/core/recovery: `/var/log/book4-usb-owner-boot.qvP15L/`
- Unchanged-kernel PCIe callback diagnostic: `/var/log/book4-pcie-cache.GBGFdS/`

## Verified

| Item | Evidence |
|---|---|
| GPU 0009 | Boot/resume verified, DDR frequency hold removed |
| UFS 0010 | Runtime/callback verified, sleep request cleared |
| CSI 0011 | Camera before/after real suspend verified, idle clocks released after CCI autosuspend |
| Earlier overnight | QCE unloaded, 76% → 55% over 8 h 20 min, approximately 1.6 W |
| DDR low-power residency | Approximately 97.44% of APSS sleep with GPU fix, native PCIe PM and QCE removal |
| CX/AOSS collapse | Still absent in measured tests |
| 0015 boot | Expected code loaded, incidental suspend/resume completed, no controlled test or promotion |
| Source checkpoint | Observer and all experimental patches committed |
| Maintained patch series | Six patches apply to `2685c75587ff`, GPU/UFS/CSI source matches built tree |
| Maintained module package | Installed UFS/CSI binaries identical to previously tested binaries |
| Initramfs rebuild | 367 module vermagics, installed-byte matches, identical extracted contents and modes across two builds |
| QCE crypto fallback | Kernel AF_ALG SHA-1, SHA-256, both HMAC variants and AES-CBC passed with QCE absent |
| Rejected blacklisted boot | `ff0e1b57-9220-401a-a454-864e8c0826d5`, callback completed, power goal failed |
| Blacklist failure | DDR sleep avg/peak and init values 2147483647, ACV 0/8, MC0 255652/2045222 |
| Corrected boot | `cbf88fb6-930e-4072-83b2-48c2aa5ad299`, expected kernel/modules, original USB, QCE probed |
| Probe-first core callback | Passed, success 0 → 1 / failure 0, APSS duration unchanged, 6.898 s interval / 1.894 s monotonic |
| Corrected final votes | DDR avg/peak and init 0/0, ACV and MC0 0/0, UFS 0/0, XO still 3/3 |
| Corrected recovery | QCE restored, all 17 ICC providers synchronized, original USB policy/wakeup/counts restored, six CSI clocks released |
| Camera recovery | Two ten-frame captures after each core/real test, no images saved, six idle clocks zero after CCI autosuspend |
| Maintained real sleep | APSS 1285.616 s, interval 1287.536 s / monotonic 1.911 s, success 1 → 2 / failure 0 |
| Real-sleep DDR | D4 1252.635 s, 97.43459% of APSS, independent DDR sleep record 1251.635 s |
| Real-sleep votes | DDR/ACV/MC0 zero, UFS 0/0, XO 3/3, no CX/AOSS entries, original USB clocks retained |
| Real-sleep battery | 51% → 50%, 0.038 Ah, roughly 1.6 W including 32.149 s awake settling, single coarse step, not a precision comparison |
| Real-sleep recovery | QCE restored, all 17 ICC providers synchronized, original USB policy/wakeup/counts and Wi-Fi restored |
| Test controls | 14 callback-checker negative controls, real-sleep checker rejects core-only/zero-APSS fixtures, both checkers reproduce the captured real-sleep results |
| Single-flag boot | `6e7850b1-6908-4989-8263-6e6bfe49d3ea`, same kernel/initramfs/DTB, only `clk_ignore_unused` removed |
| Single-flag core callback | Passed, success 0 → 1 / failure 0, APSS unchanged, interval 6.869 s / monotonic 1.867 s |
| Single-flag recovery | Crypto fallback, all 17 ICC providers, original USB policies and two camera captures before/after passed |
| Single-flag core cached state | 216 handles and identical clock samples, DDR/UFS zero, XO still 3/3, 16 checker negative controls passed |
| Single-flag real sleep | APSS 2314.170 s, interval 2316.079 s / monotonic 1.901 s, success 1 → 2 / failure 0 |
| Single-flag real DDR | D4 2254.884 s, 97.43812% of APSS, independent DDR sleep record 2253.087 s |
| Single-flag real battery | 45% → 43%, 0.076 Ah, approximately 1.77 W including 32.172 s awake settling, energy difference not established |
| Single-flag real recovery | QCE/ICC, USB policy, sampled counts, two camera captures and Wi-Fi passed |
| Real-sleep comparison | Final sampled clocks and RPMh requests match both-flags baseline, awake-only I2C/XO differences retained, no CX/AOSS collapse |
| No-flags boot | `ad3371d3-1d3f-473b-8424-a16a48b16dc2`, both options absent, native domain cleanup logged, expected kernel/modules |
| No-flags core callback | Passed, success 0 → 1 / failure 0, APSS unchanged, interval 6.875 s / monotonic 1.871 s |
| No-flags core comparison | 216 handles, identical awake/suspend clock samples, RPMh requests and batches, DDR/UFS zero, XO 3/3 |
| No-flags recovery | Crypto fallback, 17 synchronized ICC providers, original USB policy, Wi-Fi and camera before/after passed, QCE restored |
| No-flags controls | 16 callback-checker negative controls, real-sleep synthetic cases and captured-result reproduction passed |
| No-flags real sleep | APSS 1243.141 s, interval 1245.005 s / monotonic 1.856 s, success 1 → 2 / failure 0 |
| No-flags real DDR | D4 1211.312 s, 97.43963% of APSS, independent DDR sleep record 1210.346 s |
| No-flags real battery | 40% → 39%, 0.038 Ah, approximately 1.62 W including 32.172 s awake settling, energy difference unresolved |
| No-flags real recovery | QCE/ICC, original USB policies/counts, Wi-Fi and two discarded ten-frame camera captures passed |
| Three-boot comparison | Final sampled clocks and complete RPMh requests/batches identical, DDR/UFS zero, XO 3/3, CX/AOSS entries zero |
| Previous clock cleanup coverage | Five combined clock/domain providers retained `genpd_sync_state` only, missing their native clock sweeps |
| Clock/domain source candidate | Shared callback composition, original regression reproduced, candidate and seven mutation controls passed |
| Clean control build | Original Image reproduced except kernel and embedded-vDSO GNU build IDs, strict code-byte and malformed-note controls |
| Candidate image | Only common.o changed among 4,464 linked input objects, 26,950 source headers and generated ABI headers identical, same configuration and kernel exports |
| Candidate publication | New EFI payload, existing test entry reused, only kernel path/title changed, rollback and rejection controls passed |
| Candidate boot | `c4e15e7d-2d37-4595-b418-6aef7e7e6f56`, expected kernel/module notes, original USB, 17 synchronized ICC providers |
| Candidate clock cleanup | Six inspected providers use `qcom_cc_clk_genpd_sync_state`, native sweeps logged for all six, including the five previously missing providers |
| Candidate core callback | Passed on battery, success 0 → 1 / failure 0, APSS unchanged, interval 6.905795 s / monotonic 1.903079 s |
| Candidate core comparison | 216 handles, final clock samples and RPMh requests/batches match previous no-flags core, DDR/UFS zero, XO 3/3 |
| Candidate recovery | QCE/ICC and original USB policy/counts restored, Wi-Fi connected, two discarded camera captures before/after passed |
| Candidate controls | 16 negative controls and unchanged-input result reproduction passed, real-sleep checkers reproduced captured results |
| Candidate real sleep | APSS 590.117 s, interval 591.986 s / monotonic 1.860 s, success 1 → 2 / failure 0 |
| Candidate real DDR | D4 574.952 s, 97.43008% of APSS, independent DDR sleep record 574.493 s, CX/AOSS entries zero |
| Candidate real battery | 96% → 96%, reported charge unchanged, no watt estimate, 32.184 s awake settling |
| Candidate real comparison | Final clock samples and complete RPMh requests/batches match all three flag-only sleeps |
| Candidate real recovery | QCE restored, 17 synchronized ICC providers, USB policy/counts, Wi-Fi and two discarded camera captures passed |
| Normal QCE-loaded core | Success 2 → 3 / failure 0, APSS unchanged, interval 6.814513 s / monotonic 1.813856 s |
| Loaded-core requests | DDR 393600/393600 kB/s, initialization floors zero, ACV 0/8, MC0 46/374, DDR zero-vote goal not met |
| Loaded-core recovery | QCE remained loaded, generic crypto before/after, USB policy/counts, camera and Wi-Fi passed, 21 negative controls |
| Loaded overnight | APSS 31907.889 s, interval 31909.765 s / monotonic 1.869 s, success 3 → 4 / failure 0 |
| Loaded overnight battery | 92% → 70%, 0.836 Ah, approximately 1.574 W and 2.479 percentage points/hour including 32.182 s awake settling |
| Loaded overnight DDR | No sleep entries or D4 residency, 547 MHz for 31908.765 s, DDR zero-vote and low-power goals false |
| Loaded overnight recovery | QCE bound, 17 synchronized ICC providers, original USB policy/counts, generic crypto, Wi-Fi and two discarded camera captures passed |
| Loaded overnight controls | 21 negative controls, explicit failed-goal fixture and captured-result reproduction passed |
| Long QCE opt-out | APSS 20445.660 s, success 4 → 5 / failure 0, DDR D4/APSS 97.42549%, ADSP sleep/APSS 98.15485% |
| Long opt-out battery | 91% → 76%, reported charge 3471 → 2925 mAh, approximately 1.612 W including 32.173 s awake settling |
| Long opt-out recovery | QCE restored, 17 synchronized ICC providers, original USB policy/counts, generic crypto, Wi-Fi and camera passed, 16 negative controls |
| Same-candidate energy comparison | Loaded approximately 1.574 W, opt-out approximately 1.612 W, no established energy saving or regression |
| USB consumer rework | Original failures reproduced, five native objects per variant, 20 mutation controls |
| USB candidate build | Cached control reproduced, four non-debug USB object changes among 4,464 linked inputs, 13 debug-only changes |
| USB candidate staging | EFI validated and nondefault test entry updated, default/fallback/modules/initramfs/DTB unchanged |
| USB candidate boot | Expected kernel/module notes, eight PHYs at 1/1 with cached HOST_SS, six root hubs, original PHY drivers |
| USB candidate core | Success 0 → 1 / failure 0, APSS unchanged, DWC3 markers 0 → 1 → 1 → 0, xHCI accessible flags recovered |
| USB candidate recovery | QCE/17 ICC, original policies, camera, generic crypto and Wi-Fi passed, final clocks/RPMh unchanged |
| PCIe cached shutdown | Five-second core check, success 5 → 6 / failure 0, native shutdown path recorded despite L2 timeout, downstream power-off not skipped |
| PCIe diagnostic recovery | APSS unchanged, QCE loaded, 17 ICC providers synchronized, USB policy, camera, generic crypto and Wi-Fi passed |
| QCE blacklist | `1700000.interconnect` unsynchronized, QCE only non-active consumer, global ICC initialization floors retained |
| Readiness guard | Rejects boot-time blacklist, passes temporary unload after successful probe and synchronization |
| Windows preservation | BCD, BCD.LOG and BOOTSTAT.DAT changed across manual reboot, original failure retained, no writes or rollback to those files |

## Deployment

- Package: `packaging/book4-pm-modules/`, UFS/CSI only
- Module overrides: `/usr/lib/modules/7.2.0-book4-pciepm/updates/book4-pm/`
- Original module files: retained, no live UFS/CSI/USB replacement
- Preset: `/etc/mkinitcpio.d/book4-pm.preset`
- Rebuild: `mkinitcpio -p book4-pm`
- New image: `/boot/initramfs-book4-pm.img`
- Kernel: existing `/boot/vmlinuz-book4-pciepm.efi`, GPU fix and native PCIe PM, no 0012
- Existing CSI diagnostic code: retained in the tested module
- Verified reference baseline: **Arch Linux (PM baseline, QCE probe first)**
- Verified clock-only-change boot: **Arch Linux (PM test, no clk_ignore_unused)**
- Previous maintained boot: **Arch Linux (PM test, no ignore_unused flags)**
- Current running test: **Arch Linux (PM test, clock-domain sync)**
- Candidate EFI: `/boot/vmlinuz-book4-clksync.efi`
- Candidate build ID: `792e7ffafc2bc8093b384842a085067404d10c08`
- Candidate entry backup: `/var/log/book4-clock-kernel.KFFCOc/entry-before.conf`
- Candidate initramfs, DTB, options and installed modules: unchanged
- Release string unchanged, build-ID notes required for build identity
- Boot-time blacklist: absent, QCE probed normally
- Validated QCE test sequence: probe, synchronize, verify no users, temporary unload, restore
- Reference baseline: both `clk_ignore_unused` and `pd_ignore_unused` retained
- Previous no-flags boot: flag-only comparison completed without the composition fix
- Current boot: both options still absent, clock/domain composition added
- Initramfs, DTB, options and installed modules: unchanged
- Candidate: boot, native cleanup, core callbacks, short/overnight real sleep and camera recovery verified
- Normal QCE-loaded operation: core and overnight recovery passed, approximately 1.57 W, DDR power goals failed
- Six sampled clock providers: `state_synced=1`, combined callback names and native sweep messages independently verified
- Clock cleanup: native count and `CLK_IGNORE_UNUSED` guards retained, no live clock gating
- Default/fallback, executable bootloaders and historical kernel/initramfs images: unchanged
- Full historical preservation check: failed on three Windows data/configuration files, cause unconfirmed
- Independent Linux validation: passed, previous Windows differences unchanged on this reboot and left untouched
- Corrected baseline: boot, core callback, real sleep and camera recovery verified
- Clock-flag boot validator: new boot passed, old-boot/entry/flag rejection controls retained
- Both-flags entry backup: `/var/log/book4-clk-unused.pzWOJp/entry-before.conf`
- Clock-only-change entry backup: `/var/log/book4-pd-unused.dAD5En/entry-before.conf`
- Domain-flag staging controls: publication, validation-failure rollback, extra-option removal and old-boot/entry/flag rejection passed
- Domain-flag boot validation: passed, historical Windows differences unchanged

## Clock-cleanup gap in the previous kernel

- Cached runtime callback inspection: GCC, GPUCC, CAMCC, DISPCC and VIDEOCC use `genpd_sync_state`
- TCSRCC control: `clk_sync_state`, native clock-cleanup message present
- `qcom_cc_really_probe()`: GDSC registration before clock registration
- `of_genpd_add_provider_onecell()`: installs the domain synchronization callback first
- `__clk_register()`: requests `clk_sync_state`, existing different callback returns `-EBUSY`, return ignored
- Global late clock sweep: skips device-owned clocks
- Result: domain synchronization completes, per-provider clock cleanup missing for those five providers
- `pd_ignore_unused`: guards the late unused-domain pass, not `of_genpd_sync_state()`
- One-shot diagnostic: device locks and cached callback names only, no provider calls, no hardware writes, module unloaded
- Source ordering and runtime callback names verified, source copies and checker in `/var/log/book4-clk-baseline.6DJROR/sync-owner/`
- Original investigation: no live supplier synchronization or clock/domain source changes
- Current candidate: combined callbacks and native clock sweeps verified, no power-saving claim
- Four LDO cache entries differ from the earlier pre-camera core capture, complete requests match the camera-exercised real-sleep baseline

## Completed flag comparison

| Configuration | APSS sleep | DDR D4/APSS | Battery | Coarse W including settling |
|---|---:|---:|---:|---:|
| Both flags | 21 min 26 s | 97.43459% | 51% → 50% | 1.58 |
| Clock flag absent | 38 min 34 s | 97.43812% | 45% → 43% | 1.77 |
| Both flags absent | 20 min 43 s | 97.43963% | 40% → 39% | 1.62 |

- Common configuration: maintained patches, original USB, temporary post-probe QCE unload, battery only
- Final sampled clocks and RPMh requests: identical across all three tests
- Awake-only differences: UFS, I2C and shared XO counts, exact rows in `clock-comparison.json`
- CX/AOSS collapse: absent
- SOC resolution: approximately 1%, no established energy improvement or regression
- Normal QCE-loaded overnight: measured separately on the clock/domain candidate, not on these flag-only configurations

## Clock/domain candidate — sleep and recovery verified

- Patch and boundaries: [experimental clock synchronization](../patches/experimental/clock-sync/README.md)
- Default composition: clocks before domains, installed before either framework registers its callback
- Early board-clock ownership: recognized and upgraded
- Explicit callbacks: preserved, existing ICC wrapper extended with domain synchronization
- Non-ICC controllers: no `icc_sync_state()` call, global synchronization counter unchanged
- Census: 187 shared-probe driver sources, six explicit ICC callbacks matching six ICC descriptors
- Regression: actual selection fragment, callbacks and framework setter, original runtime assertion failure retained
- Candidate checks: shared driver, repeated setup, no-domain case, custom callbacks, ordering and ICC accounting
- Seven broken variants rejected by runtime assertions
- Native `common.o`: built against matching headers/config/compiler, exported symbol names unchanged, only new import `of_genpd_sync_state`
- Clean tree: `/home/hamza/Projects/linux-book4-clock-sync`, maintained 0001–0003, 0014–0011 plus candidate, original USB source
- Image-build proof: original control Image identical except two verified GNU build IDs, only common.o changed for candidate
- Module compatibility basis: matching headers/config/compiler/export table and isolated source/object delta
- `CONFIG_MODVERSIONS`: disabled, no symbol-CRC assurance or release-only claim
- Native disassembly: default clocks → domains, explicit ICC wrapper ICC → clocks → domains
- Compressed EFI payload: built Image recovered and compared
- Cached callback inspector: matching build, one-shot sample, independently unloaded, no provider calls
- Publication: default/fallback and all previous payloads retained, exactly two Arch entries
- Boot validator: new boot accepted, old-boot/kernel/payload/entry rejection controls retained
- Build failures retained: private-reference permissions, pinned weak-banner metadata shifting rodata, non-recursive make `-o`, embedded-vDSO build ID and missing `modules_prepare`
- Corrections: readable reference copies, separate metadata generation with tested recursive target freezing, explicit two-ID comparison and native module preparation
- Original failed comparisons: retained, no broad data/code exclusions
- Running callbacks: all six sampled controllers use `qcom_cc_clk_genpd_sync_state`
- Core recovery: QCE restored, original USB policies/counts, camera and Wi-Fi passed
- Final cached suspend state: identical to previous no-flags core
- Awake-only differences: shared divided-XO count 15 → 16 and active a94000 I2C clocks
- Unchanged cached counts: no proof that formerly unclaimed hardware gates were unchanged
- Real sleep: 590.117 s APSS, DDR D4/APSS 97.43008%, CX/AOSS entries zero
- Real-sleep cached clocks and complete RPMh requests/batches: match all three flag-only tests
- Real-sleep awake samples: match both-flags capture, differ in 8 rows versus clock-only and 26 versus no-flags
- Battery: 96% → 96%, charge drop unresolved, no energy-benefit claim
- Recovery: QCE/ICC, original USB policies/counts, camera and Wi-Fi passed

## Normal QCE-loaded follow-up

- Configuration: same candidate, both flags absent, original USB, no QCE removal
- Five-second core diagnostic: completed, success 2 → 3, failure 0, no APSS sleep
- QCE sleep client: tag 7, avg/peak 393600/393600 kB/s
- DDR initialization floors: 0/0, all 17 ICC providers synchronized
- Actual DDR sleep requests: 393600/393600 kB/s, not the rejected blacklist's INT_MAX floors
- BCM sleep requests: ACV 0/8, MC0 46/374
- RPMh sleep batches: seven rather than nine, ACV/SN0 absent, MC0/SH0 valid with 46/374
- Missing differential batch: not proof of zero sleep request
- Single-resource RPMh requests and suspend clock samples: match QCE-opt-out core
- DDR zero-vote goal: false, separate from successful callback/recovery validation
- Generic AF_ALG SHA/HMAC/AES known answers: passed before/after, QCE stayed loaded
- Explicit `sha1-qce` AF_ALG attempt: bind rejected with ENOENT, original failure retained
- Native `AF_ALG_CRYPTOAPI_MASK`: excludes ASYNC and KERN_DRIVER_ONLY, both flags set by QCE
- Explicit QCE execution: not tested, no API-mask bypass or hardware-failure inference
- Camera, USB policy/counts, Wi-Fi and module/ICC state: recovered
- Checker controls: 21 rejected violations, captured-result reproduction passed
- Overnight: Sep 24 02:05:29–10:57:19, APSS 8 h 51 min 47.889 s, success 3 → 4, failure 0
- Battery: 92% → 70%, 0.836 Ah, mean endpoint 16.707 V, approximately 13.967 Wh
- Coarse average: 1.574149 W over 8.872763 h including 32.182 s awake settling
- DDR: 0 sleep entries, 0 D4/d3/0x11 residency, 31909.765 s D0
- Active DDR: 547 MHz for 31908.765 s, active-frequency/D0 discrepancy 0.000004583 s
- DDR zero-vote and low-power goals: both false, callback and recovery checks passed separately
- CX/AOSS entries: 0/0
- ADSP: 3350217 entries, 27089.489 s sleep, 84.899% of APSS, approximately 105 entries per APSS second
- Final cached clocks, single-resource RPMh requests and batches: match loaded core
- QCE-opt-out short sleep comparison: same final clock samples/single requests, different bandwidth batches
- Awake clock differences: 15 rows versus loaded core and candidate opt-out short sleep
- Recovery: QCE remained loaded and bound, 17 ICC providers synchronized, original USB policies/counts, generic crypto, Wi-Fi and camera passed
- Controls: 21 rejected captured-data violations, failed DDR-goal fixture, unchanged-input replay and protected-file checks passed
- Original strict QCE-opt-out checkers: unchanged

## Overnight comparison limits

| Configuration | APSS sleep | DDR D4/APSS | ADSP sleep/APSS | Battery | Coarse W |
|---|---:|---:|---:|---:|---:|
| Historical QCE opt-out, older kernel/fixes | 8 h 20 min | 97.44059% | 98.16879% | 76% → 55% | 1.57461 |
| Candidate QCE opt-out, short test | 9 min 50 s | 97.43008% | 98.41896% | 96% → 96% | Unresolved |
| Candidate QCE loaded | 8 h 52 min | 0% | 84.89903% | 92% → 70% | 1.57415 |

- Historical full-charge capacity: 3.9 Ah, candidate captures: 3.8 Ah
- Historical kernel, UFS/CSI state, SOC range and duration: different
- Short candidate opt-out capture: charge drop unresolved
- Similar historical overnight watts: no isolated QCE or clock-composition energy conclusion
- ADSP counter contrast: observed, not proof of a QCE-caused firmware wake mechanism

## Same-candidate long QCE comparison

- Long opt-out: Sep 24 11:33:25–17:14:13, daytime run, planned eight hours
- APSS: 20445.660292 s, approximately 5 h 40 min 46 s
- Interval: 20447.658763 s, monotonic: 1.988472 s, success 4 → 5, failure 0
- Kernel, boot, options, modules, USB policies and reported full-charge capacity: same as loaded overnight
- Changed test state: QCE temporarily unloaded after normal probe and ICC synchronization
- DDR sleep request: 0/0 kB/s, ACV/MC0 zero, UFS 0/0, XO still 3/3
- DDR: 204498 sleep entries, independent sleep record 19903.403988 s, D4 19919.285380 s
- DDR D4/APSS: 97.42549%, D0 528.373920 s, active-frequency discrepancy −0.774640 s retained
- ADSP: 204717 entries, 20068.406280 s sleep, 98.15485% of APSS, approximately 10.013 entries per APSS second
- CX/AOSS entries: 0/0
- Final clock samples and single-resource RPMh requests: same as loaded overnight, bandwidth batches different
- Awake clock differences: 19 rows, preserved in `same-candidate-comparison.json`
- Recovery: QCE restored and bound, generic crypto, ICC, original USB policies/counts, Wi-Fi and two discarded camera captures passed
- Checks: captured-input replay, 16 negative controls, synthetic real-sleep controls and protected-file validation passed

| Same candidate | QCE loaded | QCE opt-out |
|---|---:|---:|
| APSS sleep | 8 h 52 min | 5 h 41 min |
| DDR D4/APSS | 0% | 97.42549% |
| ADSP sleep/APSS | 84.89903% | 98.15485% |
| Displayed battery | 92% → 70% | 91% → 76% |
| Reported charge drop | 0.836 Ah | 0.546 Ah |
| Mean endpoint voltage | 16.707 V | 16.7985 V |
| Estimated energy | 13.967052 Wh | 9.171981 Wh |
| Average including settling | 1.574149 W | 1.612276 W |

- Opt-out minus loaded estimate: +0.038126 W, not an established regression
- QCE opt-out: DDR/ADSP residency improvement, no demonstrated battery-drain improvement
- No further repeated overnight test scheduled, remaining USB/XO and physical PCIe blockers unresolved

## Battery measurement qualification

- `CHARGE_NOW`: EC-reported remaining mAh × 1000, not reconstructed from integer SOC
- `CAPACITY`: integer-truncated remaining/full percentage
- Long opt-out endpoints: 3471/3800 mAh and 2925/3800 mAh, displayed 91% and 76%
- Correct reported charge drop: 546 mAh, not 15% × 3800 = 570 mAh
- Loaded endpoints: 3496/3800 and 2660/3800 mAh, coincident with integer SOC values
- Full-charge capacity: 3800 mAh throughout both candidate long tests
- Existing `coarse_soc_resolution_percent: 1`: displayed percentage granularity, not a universal charge-now quantization bound
- Energy calculation: reported charge drop × mean endpoint voltage, includes awake settling
- Limits: one pair, unequal durations/SOC ranges, firmware gauge accuracy and voltage integration error unestablished
- Saved captures and result calculations: unchanged, no rescaling or claimed integrated-power measurement

## Existing AOSS/QDSS deferral

- AOSS `state_synced=0`, same 32 pending trace consumers logged on the previous no-flags boot
- `CONFIG_CORESIGHT_TPDM` and `CONFIG_CORESIGHT_TPDA`: disabled
- QDSS cached prepare/enable counts: 0/0
- QDSS provider: prepare/unprepare commands, no `is_prepared` operation
- CCF fallback: software prepare count, no inferred firmware clock state at count zero
- Interpretation: synchronization deferral, not proof of a retained firmware sleep vote or drain cause
- No trace-driver loading, forced synchronization, reference decrements or QMP writes
- Existing QMI initialization and APM timeout messages: also present on the previous boot

## USB consumer rework — empty-port boot/core verified

- Two patches under `patches/experimental/usb-rework/`, maintained series unchanged
- Parent-owned PHY lifetime without `XHCI_SKIP_PHY_INIT`, root-hub hooks retained
- Host PHY gets before register access, successful gets unwound on failure
- DWC3 system-suspend marker: xHCI resume and completion blocked after failed core resume
- Native objects: USB `phy.o`/`hcd.o`, DWC3 `core.o`/`host.o`/`dwc3-qcom.o`, before and candidate
- Existing DWC3 field offsets and size unchanged, new flag in padding, stripped Qualcomm glue object identical
- Extracted-helper tests: original failures reproduced, 100 cycles, null/unsupported PHYs, positive returns, modeled get failures and retries
- Mutation controls: 18 native assertion failures, two property-wiring/terminator failures
- Isolated source tree: `/home/hamza/Projects/linux-book4-usb-rework`, exact tested patch bodies
- Supplier counterexample: runtime-active PHY child returns 1 before provider resume, zero parent resume attempts
- System prepare reference: can keep PHY child active, failed supplier resume not necessarily visible through the get result
- Runtime-PM-disabled PHY: `-ENOTSUPP`, no supplier-readiness guarantee
- Scope limit: reported DWC3 callback errors only, not permission to enable 0014/0015
- Remaining gating work: supplier readiness, mode-aware wake, shared lifetime and mixed runtime/system transitions
- Full link and EFI embedding: passed, cached build reused rather than a clean recompile
- Control Image: equivalent to previous clock-only candidate except verified kernel and vDSO GNU build IDs
- Control ID: `005eb5f29962e165c715edd5c6f9d6eb626f5775`
- Candidate ID: `1e24968b6e9d63b835a5fc12fdfc3689787d666b`
- Linked inputs: 4,464, non-debug changes limited to USB `hcd.o`/`phy.o` and DWC3 `core.o`/`host.o`
- Other changed inputs: 13 debug-only USB objects, debug-stripped comparisons passed
- Header checks: 26,955, changes confined to `drivers/usb/core/phy.h` and `drivers/usb/dwc3/core.h`
- Public/generated ABI headers, configuration and kernel exports unchanged, `MODVERSIONS` disabled
- Battery build: explicit authorization, four jobs, tested 30%/invalid-telemetry stop, guard not triggered
- EFI: `/boot/vmlinuz-book4-usbowner.efi`, 16,638,464 bytes
- EFI SHA256: `963949ae82b3dc3e654a6a5f40dad11155c137f20964cd24e0ffe1312dc93d68`
- Staging: existing test entry, title/kernel path only, exactly two Arch entries
- Default/fallback, previous clock kernel, installed modules, initramfs, DTB and options preserved
- Current-hash Windows checks passed, historical BCD/BCD.LOG/BOOTSTAT.DAT qualification unchanged
- Controls: six candidate input/image failures, two-ID normalization, publication rollback/forbidden deltas and four boot-validator failures
- Hardware stage: original PHY drivers, empty ports, original `power/control=on` and wake policies
- Boot: `89e5a84a-e198-4e7f-8c09-167f8807635f`, expected kernel/module notes, QCE normally probed
- Clock cleanup: all six inspected composite callback owners retained, 17 ICC providers synchronized
- Observer: matching native root-hub/PHY/HCD/DWC3 offsets and HCD bitfield, live module notes verified
- Initial GDB failure: reduced `hcd.o` lacked nested USB-bus members, matching `vmlinux` resolved offsets
- Eight USB PHYs: init/power 1/1 and cached mode 5 `USB_HOST_SS` in all four phases
- Six root hubs: no skip-PHY flag, five parent-owned PHY lists
- Multiport shared root: no separate list by native allocation design, four PHYs present in its primary root
- Three DWC3 markers: awake 0, final suspend 1, early syscore resume 1, awake-post 0
- Six xHCI accessible flags: 1 → 0 → 0 → 1
- Test: five-second `pm_test=core`, success 0 → 1 / failure 0, APSS unchanged
- Interval: 6.997589 s, monotonic: 1.992069 s, no real-sleep or energy result
- DDR: 393600/393600 kB/s with QCE loaded throughout, UFS request zero, XO retained
- Final 216-handle clock samples and full RPMh requests/batches: identical to preceding QCE-loaded PCIe core
- Awake comparison: nine I2C/XO rows differ, retained without causal attribution
- Recovery: PHY references/modes, USB policies, QCE/17 ICC, generic crypto and Wi-Fi passed
- Camera: two discarded ten-frame captures before and after, existing CCI autosuspend respected
- Capture controls: 21 existing violations and 20 USB violations rejected, replay inputs/results unchanged
- Observer, hook and test units removed, `pm_test=none`
- Pending: peripherals, hardware fault injection, supplier readiness, mixed transitions, wake and real sleep
- No reboot or suspend scheduled

## PCIe shutdown path — callback evidence

- Unchanged clock/domain kernel, original USB, QCE loaded throughout
- Test: five-second `pm_test=core`, success 5 → 6 / failure 0
- Interval: 6.915247 s, monotonic: 1.912554 s, APSS unchanged
- Observer: cached fields only, matching kernel notes and native private-prefix/field-offset checks
- Preflight: load/unload passed, no controller or PHY register access
- Independent post-capture load: live observer build-ID notes match, module file hash unchanged

| Phase | Controller suspended | Skip downstream power-off | Skip L2 wait |
|---|---:|---:|---:|
| Awake | 0 | 0 | 0 |
| Final suspend | 1 | 0 | 0 |
| Early syscore resume | 1 | 0 | 0 |
| Awake after cleanup | 0 | 0 | 0 |

- Callback owner: `qcom_pcie_host_deinit`
- DesignWare timeout: nonfatal, continuation through link stop and host deinit
- Qualcomm deinit: PERST assertion, downstream power-off call, PHY power-off and controller deinit
- Recorded state: shutdown path completed, PME-dependent downstream power-off skip not selected
- Not established: physical rail collapse, PHY reference ownership, real-sleep power or PCIe drain attribution
- Recovery: QCE/ICC, original USB policies, camera, generic crypto and Wi-Fi passed
- Checkers: 21 existing controls, four PCIe outcomes accepted, eight malformed/inconsistent captures rejected
- Cached awake/final clocks and full RPMh requests/batches: identical to the earlier QCE-loaded core
- DDR: 393600/393600 kB/s, zero-vote goal false, no energy measurement
- Observer and temporary hook removed, `pm_test=none`, nothing scheduled

## Next tests

1. Manual USB-A peripheral connection, mouse or keyboard preferred, enumeration and disconnect/reconnect checks
2. Coordinated USB-C/SuperSpeed, wake and real-sleep checks after peripheral recovery, original PHY drivers and policies
3. Supplier-readiness and mode/lifetime corrections before any USB PHY clock gating
4. GCC and physical PCIe rail/reference review, no inference from the L2 warning alone
5. QCE request/PM lifetime review, no boot blacklist or assumed battery saving
6. Further real sleep only for a distinct candidate or hypothesis, manual wake required
7. Cold-hibernation reset investigation remains separate

## Boundaries

- Unchanged battery percentage alone: no zero-drain conclusion, inspect reported remaining charge
- `pm_test=core`: callback exercise, not real deep sleep
- Awake `clk_summary`: not final suspend state, provider runtime resumes possible
- QCE fallback coverage: common tested algorithms only, no IPsec or explicit hardware-driver guarantees
- Incidental sleep: `hypridle` request, Sep 22 23:52:59 → Sep 23 00:37:38 wall-clock log interval, success 1 / failure 0
- Incidental sleep: original USB experiment still loaded, no before/after APSS/XO/battery capture, not an energy result
- Initial final-health assertion: zero-suspend assumption rejected, separate post-incident health capture retained
- Blacklist failure mechanism: device links defer supplier sync, `icc_sync_state()` waits for every provider, initial floors affect every RPMh bucket
- Equal wake/sleep floors: no differential sleep BCM batch, not proof of zero vote
- Original strict power checker: unchanged, separate outcome checker verifies failed goal and successful recovery
- Clock/domain flags: suspects, no measured benefit yet
- USB source/mock checks: no peripheral-wake or consumer-resume safety proof
- PCIe: L2 timeout persists, native shutdown path observed in a core diagnostic, physical rails unmeasured
- QCE opt-out: workaround, not a driver PM fix
- Hibernate: cold-resume reset stage unresolved
- RTC alarm: unavailable, manual wake required
- Latest coordinated real sleep: QCE opt-out, planned eight hours, manually ended after approximately 5 hours 41 minutes
- Additional uncontrolled sleeps: Sep 23 15:45:07–16:11:26 and 16:41:51–20:03:15, success 2 → 4 / failure 0, no controlled power measurement
- Known warnings retained: PCIe L2 timeout, IRQ-affinity failures and Wi-Fi hwmon parent-sleep warning
- No reboot scheduled, default/fallback unchanged
- Earlier post-callback inhibitor race: preserved, corrected by waiting for logind sleep completion and verifying the owned inhibitor PID
- No wake-policy changes or pending experiment timers
- Temporary inhibitor released before manual handoff
