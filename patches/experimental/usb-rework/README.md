# USB ownership and local resume-error rework

- Status: source and native-object checks only, not installed or promoted
- Base: `2685c75587ff`, maintained 0001–0006 and experimental clock/domain composition
- Historical USB 0007–0010: excluded, unchanged under `../usb/`
- Scope: consumer ownership and reported DWC3 resume errors, no PHY clock gating
- Running kernel, modules, initramfs, boot entries and USB policies: unchanged

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
- Full kernel link, boot, hardware fault injection, peripheral wake and energy: pending

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
- Next build: AC required, control/candidate identity checks before publication
