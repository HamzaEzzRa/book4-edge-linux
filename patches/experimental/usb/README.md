# USB experiments — excluded from the maintained series

- Original patch bodies and historical validation statements preserved, not recommended for installation
- Historical evidence: `reports/suspend-investigation.md`
- Source/mock tests: lifetime bookkeeping, not controller recovery or peripheral wake
- `scripts/test-usb-phy-pm.py`, `scripts/test-qmp-system-pm.py`, `scripts/test-eusb2-system-pm.py`: experimental source tree only

| Patch | Remaining blocker |
|---|---|
| 0012 | Global removal of root-hub hooks, calibration and `HOST_SS` mode propagation |
| 0013 | Four drivers changed, only combo deployed, probe-failure and DisplayPort coverage incomplete |
| 0014 | Hibernation callbacks absent, DisplayPort and peripheral wake unverified |
| 0015 | `HOST_SS` excluded, unlocked `init_count`, consumers can resume after clock-enable failure |

- DWC3 `dwc3_resume_common()`: ignored `phy_pm_runtime_get_sync()` results, register access before PHY runtime gets
- PM core: supplier resume errors do not automatically block consumers
- Required USB correction: ownership without lost hooks, mode-preserving wake setup, consumer-side error recovery
- Partial rework: [ownership and local-error candidate](../usb-rework/README.md), empty-port boot/core/recovery passed, peripheral/wake pending, no PHY clock gating
- Additional blocker: runtime-active PHY child can hide failed provider resume, get-result checking alone insufficient
- No blind `SYSTEM_SLEEP_PM_OPS()` substitution: additional hibernation behavior
- Maintained baseline: patches 0001–0003, 0014–0011, original USB drivers, native PCIe PM
