# Kernel config

- Full config: `book4-edge.config`
- Base: `zensanp/linux-book4-edge @ 2685c75587ff`
- Architecture: `arm64`

## Changes from the initial config

| Option | Purpose |
|---|---|
| `INPUT_UINPUT=m` | `/dev/uinput`, ydotool, on-screen keyboards |
| `UHID=m`, `HIDRAW=y` | HID-over-GATT, raw HID access |
| `BT_RFCOMM=m`, `BT_RFCOMM_TTY=y` | HFP/HSP microphone support, missing-RFCOMM startup error |
| `PKCS8_PRIVATE_KEY_PARSER=m` | EAP-TLS PKCS#8 keys, iwd module loading |
| `ZRAM=m`, `ZSMALLOC=m`, LZ4 + ZSTD backends | Compressed swap, `userspace/memory` |
| Other options | Unchanged |

## Experimental PCIe suspend test

| Item | Value |
|---|---|
| Fragment | `pcie-pm-test.config` |
| Build | Separate kernel, retained working fallback |
| Boot option | `pcie_port_pm=force` |
| Native hotplug ownership | Prerequisite for root-port D3 |
| `pm_test=core` | Five-second callback test, no real sleep or RTC alarm |
| Verified combination | GPU patch 0004, native PCIe PM, temporary `qcrypto` removal |
| Boot, callback test, real-sleep resume | Pass |
| Overnight DDR D4 residency | 97.44% of APSS sleep |
| Overnight battery | 76% → 55% in 8 h 20 min, approximately 1.6 W |
| CX/AOSS collapse | None |
| QCE sleep vote | Unchanged by this fragment |
| PCI power-state checks and bandwidth safeguards | Unchanged |
| Suspend drain | Unresolved, [evidence](../reports/suspend-investigation.md) |
