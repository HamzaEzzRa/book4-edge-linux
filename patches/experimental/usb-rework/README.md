# USB ownership and local resume-error rework

- Status: empty-port boot and normal core-callback/recovery checks passed, experimental
- Base: `2685c75587ff`, maintained 0001–0006 and experimental clock/domain composition
- Historical USB 0007–0010: excluded, unchanged under `../usb/`
- Scope: consumer ownership and reported DWC3 resume errors, no PHY clock gating
- Running kernel: ownership/local-error candidate with clock/domain composition
- Modules, initramfs, fallback/default and USB policies: unchanged
- Test entry only: `Arch Linux (PM test, USB ownership)`

| Patch | Scope |
|---|---|
| 0001 | DWC3 owns generic-PHY lifetime through a software property, root-hub mode/calibration/notifications retained |
| 0002 | PHY gets before host register access, balanced error unwind, xHCI and completion guards after failed DWC3 core resume |

## Checks

```sh
python3 scripts/test-usb-pm-rework.py /path/to/kernel-with-rework
```

- Extracted root-hub and DWC3 helpers, actual generic-PHY get/put wrappers
- Parent-owned and ordinary root hubs, wake/no-wake paths, mode fallback and `HOST_SS`
- Calibration and connect/disconnect callbacks retained
- 100 cycles, init/power failures, each modeled USB2/USB3 get failure and retry
- Null PHY, runtime-PM-unsupported PHY and positive get result
- Reported core-init and runtime-state errors, xHCI guard and completion guard
- Original ownership regression reproduced, original resume body rejected
- 20 mutation controls: 18 native assertion failures, two property-wiring/terminator failures
- Native ARM64 objects: USB core `phy.o`/`hcd.o`, DWC3 `core.o`/`host.o`/`dwc3-qcom.o`
- Existing `struct dwc3` offsets and size unchanged, new boolean consumes padding at offset 971
- Qualcomm glue object: identical after debug stripping
- Patch round trip: isolated source tree, exact match to tested candidate
- Full kernel link and embedded EFI Image validation: passed
- 4,464 linked inputs: four non-debug USB object changes, 13 debug-only changes
- 26,955 header checks: only two private USB headers changed, public/generated ABI headers unchanged
- Configuration and kernel exports unchanged, `MODVERSIONS` disabled
- Cached build reused, control Image reproduced except two verified GNU build IDs, not a clean recompile
- Boot: expected kernel/module build-ID notes, six clock/domain callback owners, 17 ICC providers synchronized
- Eight USB PHYs: init/power counts 1/1, cached `USB_HOST_SS`, root-hub inventory retained
- Six root hubs: `skip_phy=0`, five parent-owned PHY lists, multiport shared root intentionally empty
- Five-second `pm_test=core`: success 0 → 1 / failure 0, APSS unchanged, not real sleep
- DWC3 markers: 0 → 1 → 1 → 0, xHCI accessible flags: 1 → 0 → 0 → 1
- Recovery: original policies, single PHY references, camera, generic crypto, QCE/ICC and Wi-Fi passed
- Final cached clocks/RPMh requests: unchanged from the preceding QCE-loaded core diagnostic
- Capture checkers: 21 existing controls, 20 USB violations rejected, unchanged-input replay passed
- Hardware fault injection, peripherals, wake, real sleep and energy: pending

## Gating blockers

- `phy_pm_runtime_get_sync()`: runtime-active child can return success before checking its provider
- System prepare: temporary child reference can preserve that active state
- Runtime-PM-disabled PHY: `-ENOTSUPP`, no provider resume attempt
- Extracted-branch counterexample: failed provider, active child returns 1, zero parent resume attempts
- New guards: reported DWC3 callback status, not independent PHY supplier readiness
- Required before PHY clock gating: supplier-readiness/error handling, mode-aware wake handling and mixed runtime/system transition coverage
- No global PHY-core changes, forced references, wake-policy changes or hibernation callback expansion
- First hardware stage: ownership/local-error rework only, original PHY drivers and `power/control=on`

## Evidence

- Source/native work: `/var/log/book4-usb-rework.dWCMR6/`
- Candidate source: `/home/hamza/Projects/linux-book4-usb-rework`
- Source validation: `source-validation.json`, `negative-final/`, `native-build-local-headers.log`
- Supplier counterexample: `check-supplier-gap.py`, `supplier-gap.c`, `supplier-gap.json`
- Separate unchanged-kernel PCIe diagnostic: `/var/log/book4-pcie-cache.GBGFdS/`
- Build/publication: `/var/log/book4-usb-build.vCO9zz/`
- Battery build: explicitly authorized, tested 30% cutoff and invalid-telemetry stop
- EFI: `/boot/vmlinuz-book4-usbowner.efi`
- Kernel build ID: `1e24968b6e9d63b835a5fc12fdfc3689787d666b`
- Six candidate rejection controls, two-ID normalization controls, publication rollback and four boot-validator controls passed
- Entry delta: title and kernel path only, existing default/fallback and historical payloads retained
- Boot/core evidence: `/var/log/book4-usb-owner-boot.qvP15L/`
- Native observer: private-layout and live module-note checks, cached fields only
- Next input: connect a USB mouse or keyboard to USB-A, no reboot or real sleep scheduled
