# Suspend investigation — current status

## Decision

- Maintained baseline: patches 0001–0006, native PCIe PM, original USB drivers
- USB experiments 0007–0010: excluded from the maintained series and next test boot
- USB blockers: [review findings](../patches/experimental/usb/README.md)
- Original chronology and failures: [2026-09-20–22 archive](archive/suspend-2026-09-20-22.md)
- Checkpoint including observer: `74f1210`
- Current evidence: `/var/log/book4-review-fixes.5t5Ufq/`

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
| QCE fallback | Kernel AF_ALG SHA-1, SHA-256, both HMAC variants and AES-CBC known answers passed with QCE absent |
| QCE cleanup | Restored after both the failed harness attempt and successful retry |

## Deployment

- Package: `packaging/book4-pm-modules/`, UFS/CSI only
- Module overrides: `/usr/lib/modules/7.2.0-book4-pciepm/updates/book4-pm/`
- Original module files: retained, no live UFS/CSI/USB replacement
- Preset: `/etc/mkinitcpio.d/book4-pm.preset`
- Rebuild: `mkinitcpio -p book4-pm`
- New image: `/boot/initramfs-book4-pm.img`
- Kernel: existing `/boot/vmlinuz-book4-pciepm.efi`, GPU fix and native PCIe PM, no 0007
- Existing CSI diagnostic code: retained in the tested module
- Next entry: **Arch Linux (PM baseline, QCE off)**
- QCE opt-out: `module_blacklist=qcrypto`, test entry only
- Baseline test cleanup: preserve initial QCE absence, no forced reload
- Both `clk_ignore_unused` and `pd_ignore_unused`: retained for the baseline
- Default/fallback, Windows and historical boot images: retained
- Baseline boot and suspend: pending manual selection and coordinated testing

## Next tests

1. Boot maintained baseline, verify kernel/module notes, QCE absence and normal device recovery
2. Establish callback and real-sleep baseline
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
- First AF_ALG harness attempt: socket polling timeout, corrected to a process deadline, original failure preserved
- Kernel patch check: initial shared-object permission failure, isolated object store used, no Git ownership changes
- Clock/domain flags: suspects, no measured benefit yet
- USB source/mock checks: no peripheral-wake or consumer-resume safety proof
- PCIe: physical L2-entry timeout unresolved despite logical D3 and DDR vote release
- QCE opt-out: workaround, not a driver PM fix
- Hibernate: cold-resume reset stage unresolved
- RTC alarm: unavailable, manual wake required
- No assistant-initiated reboot or suspend, no wake-policy changes or experiment timers
- Temporary sleep inhibitor during final checks, removed before manual boot request
