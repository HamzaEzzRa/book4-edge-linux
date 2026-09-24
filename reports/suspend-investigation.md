# Suspend investigation — current status

## Decision

- Maintained baseline: patches 0001–0006, native PCIe PM, original USB drivers
- USB experiments 0007–0010: excluded from the maintained series and next test boot
- USB blockers: [review findings](../patches/experimental/usb/README.md)
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
- Clean candidate build and publication: `/var/log/book4-clock-kernel.KFFCOc/`, manual boot pending

## Verified

| Item | Evidence |
|---|---|
| GPU 0004 | Boot/resume verified, DDR frequency hold removed |
| UFS 0005 | Runtime/callback verified, sleep request cleared |
| CSI 0006 | Camera before/after real suspend verified, idle clocks released after CCI autosuspend |
| Earlier overnight | QCE unloaded, 76% → 55% over 8 h 20 min, approximately 1.6 W |
| DDR low-power residency | Approximately 97.44% of APSS sleep with GPU fix, native PCIe PM and QCE removal |
| CX/AOSS collapse | Still absent in measured tests |
| 0010 boot | Expected code loaded, incidental suspend/resume completed, no controlled test or promotion |
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
| Clock cleanup coverage | Native sweeps logged for some providers, five combined clock/domain providers retain `genpd_sync_state` only |
| Clock/domain source candidate | Shared callback composition, original regression reproduced, candidate and seven mutation controls passed |
| Clean control build | Original Image reproduced except kernel and embedded-vDSO GNU build IDs, strict code-byte and malformed-note controls |
| Candidate image | Only common.o changed among 4,464 linked input objects, 26,950 source headers and generated ABI headers identical, same configuration and kernel exports |
| Candidate publication | New EFI payload, existing test entry reused, only kernel path/title changed, rollback and rejection controls passed, no new boot yet |
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
- Kernel: existing `/boot/vmlinuz-book4-pciepm.efi`, GPU fix and native PCIe PM, no 0007
- Existing CSI diagnostic code: retained in the tested module
- Verified reference baseline: **Arch Linux (PM baseline, QCE probe first)**
- Verified clock-only-change boot: **Arch Linux (PM test, no clk_ignore_unused)**
- Current running kernel: **Arch Linux (PM test, no ignore_unused flags)**, maintained configuration
- Published next test: **Arch Linux (PM test, clock-domain sync)**
- Candidate EFI: `/boot/vmlinuz-book4-clksync.efi`
- Candidate build ID: `792e7ffafc2bc8093b384842a085067404d10c08`
- Candidate entry backup: `/var/log/book4-clock-kernel.KFFCOc/entry-before.conf`
- Candidate initramfs, DTB, options and installed modules: unchanged
- Release string unchanged, build-ID notes required for build identity
- Boot-time blacklist: absent, QCE probed normally
- Validated QCE test sequence: probe, synchronize, verify no users, temporary unload, restore
- Reference baseline: both `clk_ignore_unused` and `pd_ignore_unused` retained
- Previous boot: `clk_ignore_unused` absent, `pd_ignore_unused` retained
- Current boot: both options absent, only `pd_ignore_unused` changed relative to the previous boot
- Running kernel/initramfs/DTB and callback-conflict code: unchanged
- Candidate: clock/domain composition compiled, no hardware result
- Six sampled clock providers: `state_synced=1`, not proof of clock-cleanup execution
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

## Clock-cleanup coverage gap

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
- Running kernel and kernel worktree unchanged, no live supplier synchronization or power-saving claim
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
- Normal QCE-loaded overnight drain: not measured on this configuration

## Clock/domain candidate — boot pending

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
- Clean tree: `/home/hamza/Projects/linux-book4-clock-sync`, maintained 0001–0006 plus candidate, original USB source
- Image-build proof: original control Image identical except two verified GNU build IDs, only common.o changed for candidate
- Module compatibility basis: matching headers/config/compiler/export table and isolated source/object delta
- `CONFIG_MODVERSIONS`: disabled, no symbol-CRC assurance or release-only claim
- Native disassembly: default clocks → domains, explicit ICC wrapper ICC → clocks → domains
- Compressed EFI payload: built Image recovered and compared
- Cached callback inspector: rebuilt against clean tree, not loaded
- Publication: default/fallback and all previous payloads retained, exactly two Arch entries
- Boot validator: rejects current boot, old loaded kernel, wrong payload hash and old entry
- Build failures retained: private-reference permissions, pinned weak-banner metadata shifting rodata, non-recursive make `-o`, embedded-vDSO build ID and missing `modules_prepare`
- Corrections: readable reference copies, separate metadata generation with tested recursive target freezing, explicit two-ID comparison and native module preparation
- Original failed comparisons: retained, no broad data/code exclusions
- Running callbacks: unchanged, candidate not booted

## Next tests

1. Manual boot into **Arch Linux (PM test, clock-domain sync)** with charger connected
2. Verify kernel/module notes, callback ownership and cleanup logs, QCE/ICC readiness, device recovery and core diagnostic
3. Coordinated real sleep and recovery after successful boot/core checks
4. Overnight drain on the intended daily-use configuration, including normal QCE-loaded operation
5. USB ownership/wake/error-path work with consumer-side recovery coverage

## Boundaries

- Unchanged coarse battery percentage: unresolved drain, not zero watts
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
- PCIe: physical L2-entry timeout unresolved despite logical D3 and DDR vote release
- QCE opt-out: workaround, not a driver PM fix
- Hibernate: cold-resume reset stage unresolved
- RTC alarm: unavailable, manual wake required
- Latest coordinated sleep: planned ten minutes, manually ended after approximately 20 minutes 43 seconds
- Additional uncontrolled sleeps: Sep 23 15:45:07–16:11:26 and 16:41:51–20:03:15, success 2 → 4 / failure 0, no controlled power measurement
- Known warnings retained: PCIe L2 timeout, IRQ-affinity failures and Wi-Fi hwmon parent-sleep warning
- No reboot scheduled, default/fallback unchanged
- Earlier post-callback inhibitor race: preserved, corrected by waiting for logind sleep completion and verifying the owned inhibitor PID
- No wake-policy changes or pending experiment timers
- Temporary inhibitor released before manual handoff
