# Suspend investigation — current status

## Decision

- Maintained baseline: patches 0001–0006, native PCIe PM, original USB drivers
- USB experiments 0007–0010: excluded from the maintained series and next test boot
- USB blockers: [review findings](../patches/experimental/usb/README.md)
- Original chronology and failures: [2026-09-20–22 archive](archive/suspend-2026-09-20-22.md)
- Checkpoint including observer: `74f1210`
- Deployment evidence: `/var/log/book4-review-fixes.5t5Ufq/`
- Baseline boot/callback evidence: `/var/log/book4-pm-baseline.PfGPx7/`

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
| Maintained boot | `ff0e1b57-9220-401a-a454-864e8c0826d5`, expected kernel/modules, original USB drivers |
| Baseline core callback | Success 0 → 1, failure 0, APSS duration unchanged, 6.842 s interval / 1.839 s monotonic |
| Baseline recovery | UFS sleep request 0/0, six CSI clocks released, original USB policy/wakeup/counts restored, two camera captures passed |
| Power goal | Failed, DDR sleep avg/peak and init values 2147483647, ACV 0/8, MC0 255652/2045222 |
| QCE blacklist | `1700000.interconnect` unsynchronized, QCE only non-active consumer, global ICC initialization floors retained |
| Readiness guard | Crypto checks pass, new synchronization check correctly rejects this boot |
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
- Next entry: **Arch Linux (PM baseline, QCE probe first)**
- Boot-time blacklist: removed from next entry, current boot still blacklisted
- Next QCE test: allow probe and ICC synchronization, verify no users, unload temporarily, restore afterward
- Both `clk_ignore_unused` and `pd_ignore_unused`: retained for the baseline
- Default/fallback, executable bootloaders and historical kernel/initramfs images: unchanged
- Full historical preservation check: failed on three Windows data/configuration files, cause unconfirmed
- Independent Linux validation: passed, observed Windows changes recorded separately and left untouched
- Corrected baseline: manual reboot required, no real-sleep measurement on the rejected blacklist setup

## Next tests

1. Boot without the QCE blacklist, verify QCE binding, all ICC providers synchronized and initialization floors cleared
2. Temporarily unload unused QCE, run crypto/PM-readiness checks, repeat callback baseline before real sleep
3. Remove only `clk_ignore_unused` for a separate boot and equivalent checks
4. Test `pd_ignore_unused` separately, without simultaneous driver or policy changes
5. Measure overnight drain on the intended daily-use configuration
6. Resume USB ownership/wake/error-path work only with consumer-side recovery coverage

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
- Five-second core callback exercised, no assistant-initiated real sleep or reboot
- Post-callback inhibitor attempt raced logind completion and failed, recorded separately, replacement inhibitor acquired during diagnosis
- No wake-policy changes or pending experiment timers
- Temporary inhibitor released before manual handoff
