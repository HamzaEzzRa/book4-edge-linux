# USB ownership and local resume-error rework

- 0001–0002: empty-port boot, keyboard callbacks and empty-port real suspend/recovery passed
- 0003: boot, normal callbacks and USB-A runtime → system-suspend callbacks passed
- Base: `2685c75587ff`, maintained 0001–0006 and experimental clock/domain composition
- Historical USB 0007–0010: excluded, unchanged under `../usb/`
- Scope: consumer ownership, reported provider/core resume errors and host runtime/system transitions
- PHY clock gating: absent
- Running kernel: supplier-guard candidate with clock/domain composition
- Modules, initramfs and fallback/default: unchanged
- USB policies: restored after temporary controller/xHCI runtime checks, wake settings unchanged
- Test entry only: `Arch Linux (PM test, USB supplier guards)`

| Patch | Scope |
|---|---|
| 0001 | DWC3 owns generic-PHY lifetime through a software property, root-hub mode/calibration/notifications retained |
| 0002 | PHY gets before host register access, balanced error unwind, xHCI and completion guards after failed DWC3 core resume |
| 0003 | Explicit provider resume, host runtime-resume preparation, failed-resume runtime and Qualcomm IRQ guards |

## Behavior check

```sh
python3 scripts/test-usb-pm-rework.py /path/to/kernel-with-all-three-patches
```

## Ownership kernel checks, 0001–0002

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
- USB-A keyboard: enumeration, bindings and static capabilities preserved through callbacks, no typing or wake test
- Empty-port real sleep: 707.982 s APSS, recovery passed, loaded stock QCE retained DDR vote
- Hardware fault injection, peripheral wake, SuperSpeed/DisplayPort and energy: pending

## Supplier guard checks, 0003

- Genuine prior coverage gaps: active PHY hiding provider failure, host runtime/system transitions, glue failure guard
- Original helper: register-access assertion failed with a suspended provider and runtime-active PHY child
- Candidate: explicit provider resume before core restore, no extra reference ownership
- PM prepare references: retained until completion, supplier ordering traced in the PM core
- Failed provider resume: no core register access, runtime/xHCI/completion guards retained
- Qualcomm wake-IRQ guard: retained until core resume succeeds
- Host prepare: resume before system suspend, positive runtime return normalized to zero
- Modeled provider failures, disabled providers, callback retry and 100 mixed-transition cycles passed
- Four unsafe variants rejected by native behavior assertions
- Native ARM64 control/candidate objects and cached full-kernel link passed
- 4,464 linked inputs: only `dwc3/core.o` and `dwc3/dwc3-qcom.o` changed
- 26,955 headers, configuration, exports and DWC3 layout unchanged
- No hardware fault injection or full PM-engine simulation
- Build battery: 33% → 32%, four jobs, 30%/invalid-telemetry guard not triggered
- Boot identity, original QCE/PHY drivers and 17 synchronized ICC providers verified
- Normal and mixed-transition `pm_test=core`: success 0 → 2 / failure 0, no real sleep
- USB-A controller/xHCI: naturally runtime-suspended before system sleep, original `on` policies restored
- Recovery: USB ownership, PHY references, camera, Wi-Fi and generic crypto passed
- Final cached clocks, RPMh sleep batches and BCM votes matched normal callbacks
- Additional camera LDO wake requests retained in the mixed capture, no energy comparison
- USB-C supplier usage increments: pre-existing PM-core link references, ordinary runtime cycle released accumulated references
- No forced decrements, PHY gating or energy improvement
- Real sleep and peripheral wake/recovery on 0003: pending

## Gating blockers

- `phy_pm_runtime_get_sync()`: runtime-active child can return success before checking its provider
- System prepare: temporary child reference can preserve that active state
- Runtime-PM-disabled PHY: `-ENOTSUPP`, no provider resume attempt
- Extracted-branch counterexample: failed provider, active child returns 1, zero parent resume attempts
- 0003: reported runtime-PM provider errors checked independently of active PHY children
- Runtime-PM-disabled PHYs: skipped, no new gating authorized for those providers
- Required before PHY clock gating: hardware validation, mode-aware wake handling, HS-PHY L2 readiness and suspend-failure unwind
- QMP combo: shared USB/DisplayPort lifetime and non-DWC3 consumers require coverage
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
- Keyboard callbacks: `/var/log/book4-usb-keyboard.oNKD5Q/`
- Ownership real sleep: `/var/log/book4-suspend-usbowner.IrE7zZ/`
- Supplier source/native work: `/var/log/book4-usb-supplier.jAjBST/`
- Supplier build/publication: `/var/log/book4-usb-supplier-build.NK37ym/`
- Supplier source tree: `/home/hamza/Projects/linux-book4-usb-supplier`
- Running EFI: `/boot/vmlinuz-book4-usbguard.efi`
- Running build ID: `a2049bc6b325058edb90198ca657ecfa8ced1aca`
- Supplier boot/normal callbacks: `/var/log/book4-usb-supplier-boot.D83npA/`
- Mixed-transition callbacks: `/var/log/book4-usb-mixed.ckw5Ok/`
- Native supplier-reference release: `/var/log/book4-usb-linkrefs.dr0igx/`
- Next input: charger and USB-A keyboard, no reboot or real sleep scheduled
