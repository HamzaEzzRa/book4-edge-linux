# Suspend investigation — 2026-09-20–22

## Status

| Item | Result |
|---|---|
| Machine | Samsung NP750XQA |
| Original test kernel | `7.2.0-book4-gc0bd8540b4a5` |
| PCIe test kernel | `7.2.0-book4-pciepm` |
| GPU-held DDR frequency | Fixed, patch 0004 |
| DDR low-power residency | 97.44% of APSS sleep with GPU fix, native PCIe PM, temporary QCE removal |
| Overnight battery | 76% → 55% over ~8 h 20 min, approximately 1.6 W |
| UFS reference leak | Fixed, patch 0005, sleep request 1/1 → 0/0 |
| Main XO request | Sleep/wake 3/3, remaining USB2 reference-gate path identified |
| CX/AOSS collapse | Unresolved |
| CSI correction 0006 | Boot, camera captures before/after real suspend, zero idle camera references after CCI autosuspend |
| DWC3 correction 0007 | Boot/ownership and selected empty-port USB-A runtime-PM verified |
| QMP correction 0008 | Combo boot and both empty-port runtime-PM checks verified, system-suspend gap corrected by 0009 |
| QMP correction 0009 | Boot/callback verification with `auto` and original `on`, battery-only real suspend/resume passed with `on` |
| USB2 candidate 0010 | Boot verified, suspend untested, USB mode and resume-error handling under review |
| UFS/CSI/USB energy benefit | Unresolved, S8 battery 59% → 59% at approximately 1% resolution |
| Cold hibernation | Reset stage unknown |
| Scheduled reboot or PM experiment | None |

## Measurement boundaries

- Qualcomm timer: 19.2 MHz
- `pm_test=core`: five-second callback diagnostic, no real deep sleep
- Success criteria: kernel counters, complete observer output, strict result checker
- Service completion or post hook alone: insufficient
- Awake snapshots: not final suspended-state votes
- CCF counts: shared clock counts, not per-device ownership
- Observer coverage: bound platform DT consumers and Linux caches, incomplete firmware inventory
- Battery resolution: approximately 1% steps
- Settled samples: awake-time contribution
- Immediate post-resume telemetry: frequently unavailable
- Numerical pre-fix energy baseline: unavailable
- RTC alarm: unavailable, manual wake for real suspend
- Coordinated tests: untouched keyboard, touchpad and lid
- Wake handling: unchanged
- QCE removal: temporary, restoration after each coordinated test
- Prohibited shortcuts: forced clock gating, manual reference decrements, live UFS/CSI unbind or unload

## Real-sleep measurements

| Test | Configuration | Boottime s | Monotonic s | APSS sleep s | DDR result | New CX/AOSS entries |
|---|---|---:|---:|---:|---|---:|
| S1 | Original, QCE loaded | 137.769 | 1.432 | 136.330 | No collapse | 0/0 |
| S2 | Original, QCE unloaded | 176.070 | 1.409 | 174.656 | No collapse | 0/0 |
| S3 | Original, final-vote observer | 295.092 | 1.445 | 293.640 | 4224 MHz throughout | 0/0 |
| S4 | GPU fix, QCE loaded | 466.718 | 1.447 | 465.263 | 547 MHz for 466.061 s, 4224 MHz for 0.014 s | 0/0 |
| S5 | GPU fix, QCE unloaded | 240.367 | 1.573 | 238.783 | 200 MHz for 198.816 s, 547 MHz for 40.731 s | 0/0 |
| S6 | GPU fix, native PCIe PM, QCE unloaded | 213.724 | 2.064 | 211.651 | D4 for 206.238 s, D0 for 7.486 s | 0/0 |
| S7 | Same combination, overnight | 29992.117 | 1.879 | 29990.226 | D4 for 29222.655 s, D0 for 769.463 s | 0/0 |
| S8 | Added UFS/CSI/DWC3/combo/QMP system-PM fixes, QCE unloaded, USB `on` | 616.882 | 1.879 | 614.994 | D4 for 599.243 s, D0 for 17.639 s | 0/0 |

| Test | ADSP entries | ADSP sleep s | Battery evidence |
|---|---:|---:|---|
| S1 | 14567 | 121.045 | Insufficient telemetry |
| S2 | 18620 | 154.696 | Insufficient telemetry |
| S3 | 31207 | 259.271 | Unchanged coarse settled reading, no wattage estimate |
| S4 | 48874 | 396.070 | 3510000 → 3471000 µAh, one coarse step |
| S5 | 25048 | 203.643 | No reliable energy estimate |
| S6 | 2330 | 209.520 | 2769000 µAh / 71% before and settled, not zero-drain evidence |
| S7 | 300177 | 29441.044 | 76% → 55% |
| S8 | 6349 | 605.273 | 59% → 59%, unresolved charge loss, no wattage estimate |

- Resume: successful for S1–S8
- S3 suspend successes: 3 → 4, failures 0
- S4 DDR 547 MHz: 99.86% of capture interval
- S5 DDR 200 MHz: 82.71% of capture interval
- S6 DDR sleep record: 2117 entries, 206.074 s
- S6 D4 residency: 97.44249% of APSS sleep
- S6 active-frequency sum: equal to D0 duration
- DDR sleep record and D4 mode record: independent counters
- Cleanup: QCE restored, temporary hooks/observer removed, `pm_test=none`

### Overnight energy and accounting

| Measurement | S7 value |
|---|---:|
| Battery sample interval including settling | 8.339770 h |
| Awake settling interval | 31.054 s |
| Charge loss | 0.819 Ah |
| Full charge | 3.9 Ah |
| Mean endpoint voltage | 16.034 V |
| Estimated energy | 13.13 Wh |
| Estimated average power | 1.5746 W |
| SOC loss rate | 2.5181 percentage points/hour |
| DDR sleep entries | 299960 |
| DDR sleep record | 29199.432 s |
| D4 / APSS sleep | 97.44059% |
| Active-frequency duration sum | 766.940 s |
| D0 minus active-frequency sum | **2.522993 s** |

- Endpoints: discharging, AC offline
- Energy method: SOC-derived charge × mean endpoint voltage, not integrated energy
- Duration discrepancy: explicit checker output, no counter rescaling
- All DDR mode durations: sum equal to capture interval
- Final Linux DDR sleep votes: 0/0
- Root port and Wi-Fi: cached D3hot
- PCIe L2 acknowledgement: unresolved timeout
- Link retraining and Wi-Fi reconnection: successful

## DDR statistics and cached observer

| Item | Finding / implementation |
|---|---|
| Statistics node | `/soc@0/sram@c3f0000` |
| Missing link | `qcom,qmp` |
| Consequence | Skipped AOSS DDR `freqsync`, stale duration fields |
| Board correction | `qcom,qmp` reference to `aoss_qmp`, patch 0003 |
| Validation | Temporary overlay/reload, advancing counters, later boot-DTB verification |
| Original DTB | Preserved |
| Temporary GPU-floor check | 1107 → 666 MHz, 16500000 → 8171875 kB/s, DDR residency at 2092 MHz |
| GPU floor after check | 1107 MHz restored |
| Syscore observation | Cached ICC, BCM, PCI, RPMh and CCF data |
| Observer ICC paths | Four zero-vote rows |
| RPMh cache locking | Nonblocking, same constraint as `rpmh_flush()` |
| Private layouts | Source-validated RPMh caches and `clk_core` prefix through `prepare_count` |
| CCF handles | Normal clock/device references, no prepare/enable |
| Provider status APIs | Excluded, possible runtime resume and hardware access |
| Callback restrictions | No hardware commands, RPC, allocation or sleeping locks |
| `0xffffffff` | Unset request |
| BCM `0x40000000` | COMMIT bit, not bandwidth |
| Tag 3 | Active/wake buckets |
| Tag 7 | Active/wake/sleep buckets |
| Provider synchronization | RPMh domains, clocks and interconnect at `state_synced=1` |
| AOSS `state_synced=0` | No provider `sync_state` callback, not failed synchronization evidence |
| `clk_ignore_unused`, `pd_ignore_unused`, AOSS power controls | Unchanged |

### Initial final-vote capture, S3/S4

| Request | Tag | Sleep avg/peak kB/s or x/y |
|---|---:|---:|
| DDR aggregate | — | 393600/393600 |
| `1dfa000.crypto` | 7 | 393600/393600 |
| `1c08000.pci` | 7 | 0/1 |
| `24091000.pmu` | 3 | 0/800000, excluded from sleep |
| ACV | — | 0/8 |
| MC0 | — | 46/374 |

- GPU/USB Linux sleep requests: removed before observation
- QCE source: probe-time bandwidth request, no PM callbacks
- S5 without QCE: DDR 0/1, MC0 0/1, ACV 0/8
- Remaining S5 sleep client: PCIe

## GPU correction 0004

| Item | Value |
|---|---|
| Source | `drivers/gpu/drm/msm/adreno/a6xx_gmu.c` |
| Helper | `a6xx_rpmh_stop()` |
| Defect | Inverted `GMU_STATUS_FW_START` guard |
| Result before correction | Skipped RSC/PDC sleep after firmware startup |
| Audited callers | Normal shutdown, forced shutdown, resume error cleanup |
| Introducing commit | `f248d5d5159a` |
| Installed-original disassembly | Inverted branch confirmed |
| Regression | Original failure, corrected pass |
| Cases | No firmware, startup, repeated stop, repeated cycles, both register variants |
| Module imports | 758, unchanged and resolved to expected live providers |
| Modpost input | Live export ownership via `KBUILD_EXTRA_SYMBOLS`, MODVERSIONS disabled |
| Deployment | Reboot, no live GPU replacement |
| Loaded build ID | Corrected artifact match |
| Boot and real-suspend resume | Pass |
| GPU/RSC shutdown errors | None in corrected test |
| GPU floor and charging policy | Unchanged |

- GPU backup/build evidence: `/var/backups/book4-gmu-sleep.XhF7kO/`
- Fallback initramfs: `/boot/initramfs-book4-gmu-sleep.img`
- Fallback DTB: `/boot/dtbs/book4-gmu-sleep.dtb`, statistics-link-only delta
- Pre-GPU recovery payload: retained original MSM, early loading, omitted display gate
- Original initramfs/DTB and battery-driver blacklist: preserved

## Native PCIe PM

| Item | Value |
|---|---|
| Root port / Wi-Fi | `0004:00:00.0` / `0004:01:00.0` |
| Initial root flags | `bridge_d3=0 hotplug=1 pciehp=1 no_d3cold=0` |
| Missing prerequisite | `CONFIG_HOTPLUG_PCI_PCIE` with `CONFIG_ACPI=y` |
| Rejection path | `pciehp_is_native()` → `pci_bridge_d3_possible()` |
| Boot option alone | Insufficient without native hotplug ownership |
| S5 cached states | Wi-Fi 3 (`D3hot`), root 5 (`PCI_UNKNOWN`) |
| Root state 5 | Not a physical D0 measurement |
| Controller prerequisite | `pci_host_common_d3cold_possible()` checks root and endpoint |
| Native candidate | Root `bridge_d3=1`, native `pciehp` bound |
| Candidate source | `/home/hamza/Projects/linux-book4-pcie-pm`, base `2685c75587ff` |
| Candidate config | `config/pcie-pm-test.config`, `pcie_port_pm=force` |
| Existing camera diagnostics | Retained |
| Build scope | Full kernel/modules, rebuilt EC module, matching observer |
| Module validation | 1456 matching vermagics, no unresolved depmod symbols |
| Toolchain | GCC 16 versus original GCC 13 |
| New toolchain features | LSUI, RELR, GCC plugins disabled |
| DDR safeguards / cached PCI flags | No manual overrides |
| L2 timeout | `Timeout waiting for L2 entry! LTSSM: 0x11` |
| LTSSM 0x11 | L0 |
| DesignWare timeout behavior | Nonfatal after 10 ms, PCIe 7.0 §5.3.3.2.1 |
| Resume | Gen3 x2 retraining, Wi-Fi recovery around 18 s |
| Existing warnings | FAT dirty volume, audio/deferred probes, IRQ affinity, hwmon parent |

## Core diagnostics

| Capture | Boottime s | Monotonic s | Successes | Failures | APSS sleep increase |
|---|---:|---:|---|---|---:|
| C1 native PCIe | 6.955803 | 1.953269 | +1 | 0 | 0 s |
| C2 pre-UFS RPMh | 6.952407 | 1.948698 | +1 | Unchanged | 0 s |
| C3 UFS aborted | 1.825894 | — | 1 → 1 | 0 → 2 | 0 s |
| C4 UFS retry | 6.891270 | 1.887273 | 1 → 2 | 2 → 2 | 0 s |
| C5 CCF inventory | 6.880734 | 1.875556 | 0 → 1 | 0 → 0 | 0 s |

- Successful captures: both PCI devices D3hot, Linux DDR sleep 0/0
- C1 ACV/MC0: 0/0
- C2–C5: nine BCM sleep commands, valid=false, x=y=0
- C2 battery: AC connected, 79%, charging
- C4 battery: 88%, discharging, unchanged settled reading
- C5 battery: 74%, discharging, unchanged settled reading
- Energy conclusions from core diagnostics: none
- Cleanup: QCE restored, observer/hook removed, `pm_test=none`, `mem_sleep=deep`

### RPMh requests

| Resource | Address | C2 awake sleep/wake | C2 suspended | C4/C5 suspended |
|---|---|---:|---:|---:|
| CX | `0x30000` | 5/5 | 0/0 | 0/0 |
| MX | `0x30010` | 1/1 | 0/0 | 0/0 |
| MMCX | `0x30080` | 1/1 | 0/0 | 0/0 |
| MXC | `0x300a0` | 2/2 | 0/0 | 0/0 |
| XO | `0x300e0` | 3/3 | 3/3 | 3/3 |
| UFS reference | `0x45504` | 1/1 | 1/1 | **0/0** |

- Inventory: 93 identical addresses
- C2 → C4 changed decoded requests: UFS reference only
- UFS aliases: `clka8/rfclka8+4`, Linux `clk8` / `RPMH_LN_BB_CLK3`
- Radio ownership: not established by the `rfclka8` alias
- Other ARC requests: unset sleep, zero cached wake/active
- VRM unset sleep: not equivalent to zero active demand
- Cached requests: not proof of hardware application or complete firmware-vote coverage

### Aborted UFS diagnostic, C3

| Item | Evidence |
|---|---|
| Time | 15:27, battery 90% discharging |
| Kernel messages | `Wakeup pending. Abort CPU freeze`, `Non-boot CPUs are not disabled` |
| Failure point | `freeze_secondary_cpus()`, `-EBUSY`, before syscore |
| Wake IRQ | 131 → 141 |
| IRQ 141 | Keyboard `5-0005`, GPIO67 |
| Touchpad | `3-0040`, GPIO3, IRQ140 |
| Keyboard event-count delta | +3, physical trigger unknown |
| systemd fallback | s2idle, incompatible with `pm_test=core` |
| Suspended RPMh block / five-second wait | Absent |
| Final UFS/XO evidence | Unavailable |
| Outer service | Initially success despite abort |
| Strict result checker | Failure, unchanged criteria |
| Separate failure checker | `check-abort.py`, `abort-results.json` |
| Retry runner | Strict checker before success |
| Kernel failure counters | Preserved |
| UFS settled references/errors | 0 / 0 |
| Failed systemd state | Archived before reset |
| Wakeup policy | Unchanged |

## UFS correction 0005

| Item | Finding / validation |
|---|---|
| Source | `drivers/ufs/host/ufs-qcom.c` |
| Leaking clocks | `clk8`, `gcc_ufs_phy_axi_clk`, `gcc_ufs_phy_unipro_core_clk` |
| Pre-fix counts | 283 → 530 → 542 → 594 |
| Defect | Repeated `ufs_qcom_enable_lane_clks()` without already-enabled guard |
| Existing disable | Flag-guarded, single reference release |
| Callers | Clock setup, vendor resume, HCE initialization |
| Duplicate path | Parent Hibern8 resume followed by WL child resume |
| Clock group | All eight controller clocks via `devm_clk_bulk_get_all()` |
| Fix | Early return for `is_lane_clks_enabled` |
| Regression | Original failure, 100 corrected cycles and failure/retry pass |
| Imports | 88, unchanged |
| Initramfs delta | Only embedded `ufs-qcom.ko`, modes/symlinks/other bytes unchanged |
| Initramfs module count | 367 matching vermagics |
| Build method | Native mkinitcpio with isolated module-root copy |
| Early loading | Corrected UFS before root mount |
| Installed root UFS | Original, unchanged |
| Release-string distinction | Insufficient, loaded build-ID comparison required |
| First UFS boot | `b10700b6-a412-4c3d-af55-890ef8f6c3af` |
| Direct-read test | Eight 4 KiB reads, `/dev/sda4` → `/dev/null`, four-second intervals |
| Corrected reference range | 0–2 |
| Runtime-suspended delta | 383 ms |
| Storage errors | None |
| C4 counts | 0 before, 2 immediately after, 0 settled |
| C4 sleep request | 0/0 |
| Power benefit | Unmeasured |

- Image: `/boot/initramfs-book4-pciepm-ufs.img`
- SHA256: `9dd0aa1e809d000e2d47f2d44a628227653c7c9bf59566b70249dbf263070651`
- Separate lid suspend: 14:59:00–15:03:10, same boot, APSS 248.239 s
- Lid-suspend QCE: loaded
- Lid-suspend DDR/CX/AOSS collapse: none
- Lid-suspend counters: success=1, failure=0
- Lid-suspend final-vote/energy measurements: unavailable
- Initial zero-counter assertion: rejected intervening lid suspend
- Eduroam: restored PEAP/MSCHAPv2, CA/server-name verification, successful reconnection
- Temporary credential backup: deleted as requested

## CSI correction 0006 and CCF inventory

| Item | Finding / validation |
|---|---|
| Source | `drivers/phy/qualcomm/phy-qcom-mipi-csi2-core.c` |
| Probe defect | Unbalanced clock enable, including later probe failures |
| Streaming ownership | Separate balanced `power_on()` / `power_off()` references |
| Probe register access | None |
| CSI IRQ diagnostics | Separate patch, not the leak source |
| Fix | Six-line probe enable/error block removal |
| Regression | Original rejection, 100 corrected power cycles, regulator/rate/clock failures |
| Imports | 29, unchanged |
| Corrected module | `/var/log/book4-xo-clocks.HXZCD4/csiphy-fixed.ko` |
| Deployment / streaming test | Not installed, not hardware-tested |
| CAMSS status during observation | Runtime-suspended |
| CSI PHY runtime PM | Unsupported |
| Initial awake CCF capture | 216 handles, 124 nonzero rows |
| CCF parser checks | Synthetic valid/truncated replay |
| C5 boot ID | `269930a2-7b0d-4609-ae87-9c87f5e34dda` |
| C5 time | 18:04 |
| C5 awake inventory | 216 handles, 141 rows, 95 clocks |
| C5 suspended inventory | 216 handles, 55 rows, 28 clocks |
| C5 `bi_tcxo` prepare/enable | 8/8 |
| C5 `bi-tcxo-div2-clk` prepare/enable | 7/7 |

| Camera clocks | Awake and suspended prepare/enable |
|---|---:|
| CSIPHY0, CSIPHY4 | 1/1 each |
| CSI0/CSI4 PHY timers | 1/1 each |
| Shared camera AXI/AHB | 2/2 each |

- Retained USB clocks: primary/secondary AUX, COM_AUX, PIPE, multiport PIPE/AUX/COM_AUX, USB2/USB4/multiport reference gates
- Shared XO rows: no per-consumer ownership attribution
- LPASS SCMI clocks: separate interpretation required
- Unavailable OF lookups: explicit errors, mostly unregistered GCC parent inputs
- Camera power cost: unmeasured

## Awake USB runtime-PM test

| Item | Value |
|---|---|
| Time | 18:33:28–18:33:48 |
| PHY | `88e3000.phy` |
| Controller / xHCI | `a400000.usb` / `xhci-hcd.0.auto` |
| Topology | Six suspended root hubs, no peripherals or external displays |
| Initial policy | Driver-default runtime forbid, not a userspace override |
| Sequence | PHY auto, then controller/xHCI auto |
| Rollback | `finally` and systemd `ExecStopPost` |
| Sleep inhibitor | Active during test |
| DWC3 wakeup | Enabled, unchanged |
| xHCI system wakeup | Disabled beforehand, unchanged |
| System suspend / reboot / driver unbind | None |
| QCE | Loaded throughout |

| Stage | PHY | DWC3 | xHCI | PIPE0 / shared AUX |
|---|---|---|---|---|
| Before | Active | Active | Active | 1 / 2 |
| PHY auto | Active | Active | Active | 1 / 2 |
| All auto | **Active** | Suspended | Suspended | **1 / 2** |
| Restored | Active | Active | Active | 1 / 2 |

- Suspended durations: PHY 0 ms, DWC3 10570 ms, xHCI 16058 ms
- PHY clock-release goal: **failed**
- Strict checker/service: failed, evidence retained
- Separate outcome/rollback checker: pass
- Restored: all three `control=on`, statuses, wakeup settings, sampled leaf counts
- Variable awake XO ancestors: explicitly excluded from exact leaf-restoration comparison
- System suspend counters: success=1, fail=0, unchanged
- USB kernel warnings: none captured
- Peripheral/hotplug/wake/DisplayPort/deep-sleep/energy validation: absent

### DWC3 ownership, patch 0007

| Item | Finding |
|---|---|
| DWC3 PHY ownership | Existing `phy_init()` and `phy_power_on()` |
| Duplicate owner | xHCI root-hub PHY inventory via parent firmware node |
| Missing flag | `XHCI_SKIP_PHY_INIT` |
| Runtime suspend | `hcd_bus_suspend()` without `usb_phy_roothub_suspend()` |
| Remaining reference | USB core ownership after DWC3 runtime put |
| Three observed HCDs | `skip_phy=0`, root-hub PHY inventory present |
| Four observed USB3 PHYs | Init=2, power=2, runtime usage=2 |
| Correction | Native quirk in shared DWC3 xHCI platform data, `xhci.h` include |
| New policy/callback/wakeup restrictions | None |

### QMP provider self-reference, patch 0008

| Item | Finding |
|---|---|
| CCF registration | Snapshot of provider `pm_runtime_enabled()` |
| Prepared PIPE source | Runtime reference on its PHY provider |
| Circular dependency | PHY suspend callback required for PIPE release |
| Observed providers | `fd5000.phy::pipe_clk`, `fda000.phy::pipe_clk` |
| Cached provider state | rpm_enabled=1, prepare=1, usage=2 including default forbid |
| Multiport GCC PIPE gates | No CCF parents in this source |
| USB-A test failure attribution | Duplicate ownership, not the observed USB-C self-reference |
| Corrected order | Software-clock registration → PM enable → generic PHY creation |
| Drivers | USB, legacy USB, combo, USBC |
| Clock operations | Fixed-rate / cached DP rate, no PHY register access |
| Default forbid | Retained |
| PCIe/UFS PHY drivers | Unchanged |

### USB offline validation

- Observer evidence: `observer-ownership/`, exact private layouts, HCD/PHY counts, combo providers, stable camera counts
- Initial ICC checker failure: legitimate awake UFS bandwidth variation
- Revised ICC allowances: observed UFS request levels/four aggregates, tag-3 BWMON variation, four zero observer rows
- Original rejected capture/checker: retained
- Regression source: actual DWC3 initializer, extracted CCF helpers, actual probe-order replay
- Negative cases: original ownership failure, host-only self-vote failure, five independent source reversions
- Normal-provider control: balanced runtime get/put
- Builds: DWC3 host object, four QMP modules
- Legacy override: make-only `CONFIG_PHY_QCOM_QMP_USB_LEGACY=m`, saved config unchanged
- Import counts: USB 49, combo 67, USBC 58, legacy 45
- Configured-driver import sets: unchanged
- Legacy installed comparison: unavailable
- Patch application/reversal: exact source round trips
- Full probe-error paths, peripherals/hotplug/wake/DisplayPort and power validation: pending
- Historical captures/source snapshots: unchanged by documentation/comment cleanup

## Boot menu and DWC3-only candidate

| Item | State |
|---|---|
| Arch entries | Exactly two |
| Default | `arch.conf`, **Arch Linux (fallback, GPU fix)** |
| Reused entry at DWC3-only stage | `arch-pcie-ufs-pm.conf`, **Arch Linux (GPU + UFS + DWC3 test)** |
| Windows | Unchanged |
| Deleted obsolete entry files | `arch-before-gmu.conf`, `arch-pcie-pm.conf`, `arch.conf.bak.20260920-161950` |
| Recovery kernels/initramfs/DTBs | Retained |
| New menu-entry backups | None |
| New kernel image | `/boot/vmlinuz-book4-pciepm-dwc3.efi` |
| Candidate release | `7.2.0-book4-pciepm`, build #2 |
| GNU build ID | `5471dc0286ca7c1fcd7f9c2b58cb828bb47d7df4` |
| Image SHA256 | `90b4856c10c4bb787e83946cf43a6707fe2b0635577f2b918756d6354db04c85` |
| New functional change | Patch 0007 only |
| External initramfs | Existing `/initramfs-book4-pciepm-ufs.img`, unchanged |
| DTB / command line | Unchanged |
| Embedded drivers | Fixed GPU/UFS, original CSI/QMP, loaded-note matches |
| Excluded corrections | 0006, 0008 |
| Installed root modules | Unchanged |
| Original PCIe kernel | Retained |
| Raw Image delta | 48 bytes: quirk bit, GNU build ID, version/timestamp strings, three built-in initramfs mtimes |
| Symbol addresses | Byte-identical System.map |
| Config/compiler/built-in inventory/exports | Unchanged |
| Rejected build attempt | Forced metadata, unintended read-only-data layout changes |
| Final build | Native version-header flow |
| Artifact checks | Exact reconstructed Image, embedded EFI gzip payload, preserved boot/module hashes |
| Negative validator check | Rejected unrelated instruction-byte mutation |
| Publication | Image first, compare/fsync/rename, atomic existing-entry replacement |
| DWC3-only preservation checker | `validate.py --installed` in DWC3 staging directory, former entry expectations |
| Earlier menu-cleanup checker | Historical title/path expectations, not current-entry validation |
| Boot verification | Pass, cached ownership correction confirmed |
| Boot-check preflight | Previous boot rejected before observer load |
| Post-boot checks | Kernel/module notes, HCD skip flag, absent root-hub PHY inventory, active PHY init/power=1 |
| Post-boot observer | Brief cached-state load/unload, no PM policy writes |
| EFI one-shot selection | Unavailable with `efi=noruntime` |
| Test entry selection | Manual, unchanged fallback default |
| Reboot / automatic PM test | Not scheduled |

### DWC3-only boot verification

| Item | Result |
|---|---|
| Boot ID | `a971deff-43b2-4d7e-916d-df6f4e4537a7` |
| Kernel / loaded driver notes | Candidate kernel, fixed GPU/UFS, original CSI/QMP |
| Three HCDs | `skip_phy=1`, no root-hub PHY inventory |
| Four USB3 generic PHYs | Init=1, power=1, runtime usage=1, previously 2 each |
| USB2 generic PHYs | Init=1, power=1, runtime PM still unsupported |
| Multiport `a400000.usb` | `xhci-hcd.3.auto`, USB buses 5/6 |
| Primary `a600000.usb` | `xhci-hcd.0.auto`, USB buses 1/2 |
| Secondary `a800000.usb` | `xhci-hcd.1.auto`, USB buses 3/4 |
| Initial checker failure | Fixed automatic-ID expectation 0/1/2 versus actual 0/1/3 |
| Corrected identity check | Exactly one bound xHCI child per physical controller |
| Parser regression | Saved-capture pass, five malformed/incorrect HCD cases rejected |
| Original failure evidence | `first-boot-check/`, unchanged capture and checker |
| Final evidence | `boot-validation.json`, `boot-observer.log`, `boot-health.json` |
| Connected USB devices | Six suspended root hubs only |
| External displays | Disconnected |
| PHY/controller/xHCI runtime policies | `on`, active, unchanged |
| DWC3 / xHCI wakeup settings | Enabled / disabled, unchanged |
| USB-C PIPE self-references | Still present, correction 0008 uninstalled |
| Camera probe references | Still present, correction 0006 uninstalled |
| QCE / observer | QCE loaded, observer unloaded |
| Suspend counters | Success=0, fail=0 |
| Failed systemd units | None |
| PM policy writes / system suspend | None |
| Runtime clock release / energy savings | Subsequent awake test below / unmeasured |

### DWC3-only awake runtime-PM result

- Capture: `/var/log/book4-usb-dwc3.51tldC/`
- Time: 20:37:04–20:37:14, 10.454 s including restoration
- Targets: `88e3000.phy`, `a400000.usb`, `xhci-hcd.3.auto`
- Selection: physical controller parent, shared target list for runner/checker/cleanup
- Build notes: corrected DWC3 kernel, fixed GPU/UFS, original CSI/QMP
- Guards: sleep inhibitor, empty USB topology, no external display
- Rollback: Python `finally` and systemd `ExecStopPost`, same-boot guard

| Stage | PHY | DWC3 | xHCI | PIPE0 | PIPE1 | Shared AUX / COM_AUX |
|---|---|---|---|---:|---:|---:|
| Before | Active | Active | Active | 1 | 1 | 2 / 2 |
| PHY auto only | Active | Active | Active | 1 | 1 | 2 / 2 |
| All three auto | **Suspended** | Suspended | Suspended | **0** | 1 | **1 / 1** |
| Restored | Active | Active | Active | 1 | 1 | 2 / 2 |

- Clock values: matching cached prepare/enable counts
- Runtime-suspended deltas: PHY 1167 ms, DWC3 1167 ms, xHCI 7421 ms
- Original-kernel comparison: same target PHY/controller and policy sequence, PHY retention failure
- DWC3-only result: PHY runtime suspension and expected clock-reference release
- Strict checker/service: pass, exit 0
- Checker regression: synthetic success and six negative controls
- Restored: controls, statuses, wakeup settings, sampled leaf counts
- Other PHY/controller policies, USB2 reference gates, camera counts: unchanged
- QCE: loaded throughout
- USB kernel warnings: none captured
- Wi-Fi: connected after test
- System suspend counters: 0/0, unchanged
- New system-suspend/reboot jobs: none
- Peripheral/hotplug/wake/DisplayPort operation, system-suspend benefit, energy savings: untested

## Combo-only QMP test preparation

| Item | Value |
|---|---|
| Staging | `/var/log/book4-qmp-boot.z6SR7q/` |
| New image | `/boot/initramfs-book4-pciepm-qmp.img` |
| Reused entry | `arch-pcie-ufs-pm.conf`, **Arch Linux (GPU + UFS + DWC3 + QMP test)** |
| Entry changes | Title and initramfs path only |
| Kernel | Existing DWC3-corrected image, unchanged |
| New correction | Patch 0008, USB-C combo driver only |
| Changed embedded file | `phy-qcom-qmp-combo.ko` |
| Image SHA256 | `cd7dfe09b82647e06bf286340fc43598cde269ffcee5b3d9623b10caa7bdff4e` |
| Fixed combo build ID | `ff3c0a5277cbb756f4b2f190398672a331aeb3c8` |
| Fixed combo SHA256 | `c8e552d6ea111cb09faa916aa8b8214edc2de53a50119a4a5f558c31a00de67a` |
| GPU/UFS corrections | Retained |
| USB-A, USBC, legacy QMP module variants | Unchanged |
| CSI correction 0006 | Excluded |
| Build | Single combo module, native mkinitcpio, isolated module-root copy |
| Image comparison | Exactly one changed file, identical other contents/modes/owners/symlinks |
| Module vermagics | 367 matching |
| Combo imports | 67, unchanged |
| Early loading | Combo and corrected UFS before root mount |
| Depmod errors / new initramfs warnings | None |
| Patch regression | Combo-only reverse/forward match, original-order rejection |
| Preserved inventory | 3077 file hashes, two symlinks, except authorized test-entry replacement |
| Default / Windows / installed root modules | Unchanged |
| Previous test/recovery payloads | Retained |
| Arch entry count / new entry backups | Two / none |
| Publication | Image first, compare/fsync/rename, existing-entry replacement |
| Preservation checker at publication | `validate.py --installed` in QMP staging directory |
| Older validators | Historical title/initramfs expectations, not current-entry checks |
| Combo module at preparation | Original, unchanged |
| Corrected combo validation | Subsequent boot/runtime results below |
| Reboot / automatic PM test | Not scheduled |

- Post-boot helper: `check-boot.py`, kernel/module notes and physical-controller mapping
- Observer change: explicit cached PIPE-provider `rpm_enabled=0/1`, no PM policy writes
- Observer regression: actual C helper, both flag values, original-filter rejection
- Expected combo state: prepared PIPE sources with `rpm_enabled=0`
- Boot-parser controls: retained self-vote, unprepared source, missing provider, incomplete CCF block rejected
- Preflight boot check: previous boot rejected before observer load
- At preparation: runtime clock release, peripheral/wake/DisplayPort behavior and energy benefit untested
- Incidental suspend request during preparation: `systemctl`, PID 57642, `user@1001.service`, 20:46:14
- Incidental kernel entry/exit: 20:46:15 → 20:46:17, success=1, fail=0
- Incidental warnings: existing PCIe L2 timeout and IRQ-affinity failures, no captured USB/UFS errors
- Incidental evidence: `incidental-suspend*.log` and `.json`, original combo driver, no coordinated vote/energy capture

### Combo-only boot verification

| Item | Result |
|---|---|
| Boot ID | `998210eb-a8c9-4f7c-bd94-0b83e08ae853` |
| Loaded combo note | Fixed build `ff3c0a5277cbb756f4b2f190398672a331aeb3c8` |
| Kernel / GPU / UFS | Previous corrected variants retained |
| CSI / USB-A PHY modules | Original variants retained |
| `fd5000.phy` and `fda000.phy` PIPE providers | CCF `rpm_enabled=0`, previously 1 |
| PIPE prepare/enable counts | 1/1, unchanged under default forbid |
| Combo parent runtime usage | 1 each, previously 2 |
| USB3 generic PHY init/power | 1/1 each |
| HCD ownership | All three `skip_phy=1`, no root-hub PHY inventory |
| CCF inventory | Complete awake block, 216 handles |
| PHY/controller/xHCI policies | `on`, active, unchanged |
| USB topology / external displays | Six suspended root hubs only / disconnected |
| AC | Offline |
| QCE / observer | Loaded / unloaded |
| Suspend counters | Success=0, fail=0 |
| Wi-Fi / failed units | Connected / none |
| PMIC GLINK device-link warnings | Also present in preceding DWC3-only boot |
| Runtime clock release / energy at boot check | Not tested |

- Initial checker failure: `/efi/loader/random-seed` hash change across reboot
- Boot-loader behavior: per-boot seed rotation, `systemd-boot(7)`
- Narrow allowance: changed boot ID, exact seed path, regular 32-byte seed
- Seed contents: not logged, not modified, not pinned
- Remaining preserved hashes and symlinks: unchanged, authorized test-entry replacement excluded
- Negative controls: same-boot seed change and protected-kernel mutation rejected
- Failure evidence: `boot-check-before-seed.log`, `validate-before-seed.py`
- Final evidence: `boot-validation.json`, `boot-observer.log`, `boot-health.json`
- Artifact-only validation: `validation.json`, separate from boot results
- At boot check: no automatic suspend or USB runtime-PM test

### Both USB-C empty-port runtime-PM checks

| Item | Primary | Secondary |
|---|---|---|
| Evidence | `/var/log/book4-usbc-runtime.QcQmyC/primary/` | `/var/log/book4-usbc-runtime.QcQmyC/secondary/` |
| PHY | `fd5000.phy` | `fda000.phy` |
| DWC3 / xHCI | `a600000.usb` / `xhci-hcd.0.auto` | `a800000.usb` / `xhci-hcd.1.auto` |
| Service duration, including restoration | 10.533 s | 10.344 s |
| PHY / controller suspended-time increase | 1084 / 1084 ms | 1140 / 1140 ms |
| xHCI suspended-time increase | 7222 ms | 7022 ms |
| PHY, DWC3 and xHCI runtime suspension | Pass | Pass |
| AUX / COM_AUX / PIPE counts | Each 1 → 0 → 1 | Each 1 → 0 → 1 |
| Shared AUX source counts | 2 → 0 → 2 | 2 → 0 → 2 |
| PIPE mux/source chain counts | Each 1 → 0 → 1 | Each 1 → 0 → 1 |
| Generated PIPE-provider counts | 1 → 0 → 1 | 1 → 0 → 1 |
| `tcsr_usb4_1_clkref_en` | Unchanged | 1 → 0 → 1 |
| Checker / service / rollback | Pass / exit 0 / complete | Pass / exit 0 / complete |

- Order: primary, full restoration, secondary, full restoration
- PHY-only opt-in: active PHY/controller/xHCI, unchanged sampled clock counts
- Clock values: cached prepare and enable references, matching counts
- Other USB3 PHYs, USB2 reference gates and sampled camera clocks: unchanged
- Controls, statuses, wakeup settings and sampled leaf references: restored
- Variable shared `bi_tcxo` and `bi-tcxo-div2-clk`: excluded from exact awake restoration comparison
- Guards: matching kernel/modules/boot, six root hubs only, no external display, AC offline
- Rollback: Python `finally`, independent systemd `ExecStopPost`, same-boot guard
- Regression: synthetic success and nine negative controls per controller
- QCE: loaded throughout, no diagnostic observer
- Captured USB warnings: none
- System suspend counters: 0/0, unchanged
- Boot payloads, root modules, default entry and Windows: preservation check passed
- Failed units / scheduled PM jobs: none
- Peripheral/hotplug/wake/DisplayPort behavior, system-suspend benefit and energy savings: untested

### Phone attachment and MTP access

| Item | Result |
|---|---|
| Evidence | `/var/log/book4-usbc-phone.3MjP6V/` |
| Initial user report | Unlocked phone, no charging or enumeration, same cable/phone working on desktop |
| Initial host state | USB-C PHY/controllers active, controls `on`, no connected USB device |
| Charging-daemon action | Consumer switch request at 21:46:38, input-limit update to 1000 mA |
| Daemon state | Paused for diagnosis, enablement unchanged |
| Linux Type-C control | UCSI driver bound, no Type-C ports, no PMIC GLINK RPMsg endpoint |
| Physical power flow | Unmeasured, no forced role/switch/negotiation commands |
| Phone-side direction change | Followed by USB enumeration and MTP access |
| Phone | Samsung SM-A336E, VID:PID `04e8:6860` |
| USB path | `3-1`, `a800000.usb`, `xhci-hcd.1.auto` |
| Speed | 480 Mbit/s, USB 2.0 |
| MTP check | `mtp-detect` as `hamza`, exit 0, internal storage accessible |
| Phone file contents / writes | None / none |
| Current power direction | Not established by MTP success |
| SuperSpeed data path | Not tested by this USB 2.0 connection |
| Suspend counters | 0/0, unchanged |

- Pausing the daemon: no reversal of prior PD/charger register writes
- Daemon restart: normal boot enablement retained, paused in this boot
- Cached PD buffers: historical messages, not proof of current power flow
- Desktop access: Dolphin `mtp:/`

## CSI suspend-fix test preparation

| Item | Value |
|---|---|
| Evidence | `/var/log/book4-csi-boot.7Hyb13/` |
| New image | `/boot/initramfs-book4-pciepm-csi.img` |
| Reused entry | `arch-pcie-ufs-pm.conf`, **Arch Linux (GPU + UFS + DWC3 + QMP + CSI test)** |
| New correction | Patch 0006, unmatched CSI probe clock enable removed |
| Retained corrections | GPU 0004, UFS 0005, DWC3 0007, combo-only QMP 0008 |
| Changed driver | `phy-qcom-mipi-csi2.ko` only |
| CSI build ID | `9bebb4cb3f9a2c4b0d0fde9ec04147b547ac4603` |
| Initramfs SHA256 | `cd67b5cce5714e41ff15c705c38d7d6341a2f766219af37de7f67fd175388d5e` |
| Archive differences | CSI module, `config`, `buildconfig` |
| Configuration difference | Explicit early `phy_qcom_mipi_csi2` loading, root-installed original excluded from first load |
| Other archive files/modes/owners/symlinks | Unchanged |
| CSI imports / matching module vermagics | 29 unchanged / 367 |
| Source validation | Patch reverse/forward match, original regression rejected, fixed power helpers pass |
| Boot-clock checker | Six idle camera clocks must have zero prepare/enable references |
| Checker controls | Zero-count pass, six retained-reference rejections, previous-boot rejection |
| Kernel / DTB / installed root modules | Unchanged |
| Default / Windows / prior payloads | Unchanged / unchanged / retained |
| Arch entry count / entry changes | Two / test title and initramfs path only |
| Preservation checker at publication | `validate.py --installed` in CSI staging directory |
| CSI module after requested reboot | Corrected build, matching loaded note |
| Camera streaming / callback resume / energy benefit | Verified below / verified below / unmeasured |
| Automatic reboot / suspend | None |

- Suspend investigation priority: CSI boot verification, camera regression, callback/vote comparison, real-sleep energy measurement
- USB-C charging/role failure: separate regression, no speculative EC/PD or DT changes
- Manual boundary: test-entry selection, real-sleep wake

## CSI boot and camera verification

| Item | Result |
|---|---|
| Boot | `41000b07-d58b-44b3-a574-3fc06e236411` |
| Evidence | `/var/log/book4-csi-boot.7Hyb13/boot-validation.json` |
| Retained fixes | GPU, UFS, DWC3 ownership, combo PIPE registration |
| CSI binding | `ace4000.csiphy`, `acec000.csiphy` |
| Six idle camera clocks | Prepare/enable 0/0 |
| Camera cycles | Two ten-frame captures before callback test, two afterward |
| Completed buffers | Sequence 0–9 each cycle, 8386560 bytes each |
| Saved images | None |
| Post-capture clock references | All six 0/0 after every cycle |
| Libcamera warnings | Existing OV02C10 static-properties and sensor-delay defaults |
| Camera checks | `check-camera.py`, `camera-start-stop.json`, per-cycle logs |
| Post-callback camera evidence | `/var/log/book4-pmtest-csi-usb.I2K9AN/camera-after/` |
| Charging daemon | Active after reboot, enablement unchanged |

## C6 — CSI/USB callback comparison

| Item | Result |
|---|---|
| Evidence | `/var/log/book4-pmtest-csi-usb.I2K9AN/` |
| Mode | Five-second `pm_test=core`, no real sleep |
| Temporary changes | Ten USB PHY/controller/host controls `on` → `auto`, QCE removal |
| Wakeup policy | Unchanged |
| Before system suspend | All ten targets runtime-suspended, six camera and eleven USB3 clocks 0/0 |
| Kernel suspend counters | Success 0 → 1, fail 0 → 0 |
| Interval / monotonic | 6.889297 s / 1.887309 s |
| APSS sleep | 0 s |
| Final CCF inventory | 216 handles, 42 prepared rows, 21 distinct clocks |
| Camera at syscore | Six tracked clocks and CSI source references absent |
| USB3 at syscore | AUX/COM_AUX/PIPE clocks restored to active counts, secondary reference gate 1/1 |
| UFS / XO sleep requests | 0/0 / 3/3 |
| Linux DDR sleep / ACV / MC0 | Zero |
| CX / MX / MMCX / MXC requests | 0/0 |
| RPMh cache versus C5 | Same sleep values for 93 shared addresses, four added `ldoc1`/`ldoc2` entries |
| PCIe | Both devices D3hot, existing L2 timeout, Gen3 x2 restored |
| Strict USB clock goal | Failed, original checker and service failure retained |
| Independent outcome | CSI release verified, USB failure explicit, complete policy/clock/QCE/observer rollback |
| Checker controls | Actual USB failure rejected, hypothetical release accepted, five rollback violations rejected |
| Energy measurement | None |

- Source path: `xhci_plat_suspend_common()` → `pm_runtime_resume()` → parent DWC3/PHY resume
- PM preparation: `device_prepare()` holds extra provider and generic-PHY runtime references
- DWC3 system suspend: runtime puts cannot release prepared PHY references
- QMP USB/combo PM tables: runtime callbacks only before 0009
- Result boundary: successful awake runtime suspension, failed system-suspend clock release

## QMP system-suspend correction 0009

| Item | Value |
|---|---|
| Evidence | `/var/log/book4-qmp-system.hJimk0/` |
| Correction | USB and combo `.suspend` / `.resume` → native `pm_runtime_force_suspend` / `pm_runtime_force_resume` |
| Driver change | Four added lines, existing autonomous wake mode and error handling retained |
| Hibernation / default runtime policy | Unchanged |
| Source regression | Actual PM tables and extracted native helpers, 100 cycles, both policies, already-suspended/unused/error paths |
| Negative controls | Each original PM table rejected |
| Patch roundtrip | Forward/reverse/forward source match, malformed-prefix attempt retained separately |
| Native build | USB/combo pass, no warnings |
| USB deployment source | Original USB driver plus 0009 only, 0008 registration change excluded |
| Combo deployment source | Existing 0008 plus 0009 |
| New image | `/boot/initramfs-book4-pciepm-usbsleep.img` |
| Reused entry | **Arch Linux (GPU + UFS + CSI + USB sleep test)** |
| Archive changes | USB and combo modules only |
| Imports | USB 49 → 51, combo 67 → 69, native forced-PM helper pair only |
| Vermagics | 367 matching modules |
| USB build ID | `06c2c1b9670c9b47c9c4824ec359f25735afc3ce` |
| Combo build ID | `b46fe7137c759e5268faf7ff9e41cccbf28c8aae` |
| Initramfs SHA256 | `d77a83f23d79d48b36e5f83b2a642177bcd3e372858fbf62a78ad6c84d58ea91` |
| Preserved inventory | 3079 files, two symlinks, authorized test-entry replacement only |
| Kernel / DTB / installed root modules | Unchanged |
| Default / fallback / Windows / prior payloads | Preserved |
| Arch entries | Two |
| Current preservation checker | `/var/log/book4-qmp-system.hJimk0/validate.py --installed` |
| Boot / callback validation | Verified below |
| Real-sleep / wake / DisplayPort / energy validation | Pending |
| Automatic reboot or further suspend | None |

## QMP system-PM boot and C7/C8 verification

| Item | Result |
|---|---|
| Boot | `1513ae6a-a47f-41a6-9f40-615d69bc973e` |
| Boot evidence | `/var/log/book4-qmp-system.hJimk0/boot-validation.json` |
| Kernel and loaded modules | Matching notes, USB/combo 0009 loaded, earlier fixes retained |
| Boot payload preservation | 3079 protected files and two symlinks, authorized entry replacement, expected boot-seed rotation |
| PIPE providers | Combo self-votes absent, prepared providers `rpm_enabled=0` |
| HCD ownership | Three hosts `skip_phy=1`, no root-hub PHY inventory, active USB3 PHY init/power 1/1 |
| Idle camera clocks | Six tracked clocks 0/0 |
| Power at boot verification | AC online, battery charging at 57%, source identity unconfirmed |
| Charging interpretation | No demonstrated non-PD fix or attribution to 0009 |

| Check | C7 | C8 |
|---|---|---|
| Evidence | `/var/log/book4-pmtest-usbsleep.WYwcoJ/` | `/var/log/book4-pmtest-usbsleep-on.WKr5AM/` |
| USB policy | Temporary `auto`, restored to `on` | Original `on`, no USB policy writes |
| USB before system suspend | Runtime-suspended, tracked USB3 clocks 0/0 | Active, tracked USB3 clocks at original counts |
| Diagnostic | Five-second `pm_test=core` | Five-second `pm_test=core` |
| Temporary QCE removal | Yes, restored | Yes, restored |
| AC online | Yes | Yes |
| Interval / monotonic seconds | 7.001644 / 2.000325 | 6.903875 / 1.898242 |
| Kernel success / fail counters | 0 → 1 / 0 → 0 | 1 → 2 / 0 → 0 |
| Camera and USB3 clock goal | All 17 tracked clocks released at syscore | All 17 tracked clocks released at syscore |
| Final CCF | 216 handles, 22 prepared rows, seven distinct clocks | Identical suspended rows |
| RPMh cache | 93 requests | Identical sleep/wake values |
| UFS / XO requests | 0/0 / 3/3 | 0/0 / 3/3 |
| Linux DDR / ACV / MC0 sleep votes | Zero | Zero |
| PCIe | Both D3hot, existing L2 timeout, Gen3 x2 restored | Same |
| Service / strict checker | Success / pass | Success / pass |
| Checker controls | Captured pass, nine negative cases rejected | Captured pass, nine negative cases rejected |
| APSS sleep / energy measurement | 0 s / none | 0 s / none |
| Wake settings / stable clock references | Restored | Unchanged / restored |
| QCE / PM test / observer / hook | Loaded / none / absent / absent | Loaded / none / absent / absent |

- Remaining prepared clocks: `tcsr_usb2_1_clkref_en` 2/2, `tcsr_usb3_mp0_clkref_en` 1/1, `tcsr_usb3_mp1_clkref_en` 1/1
- Other sampled prepared clocks: `bi_tcxo` 3/3, `LPASS_HW_MACRO` 2/2, `LPASS_HW_DCODEC` 2/2, `xo-board` 1/1
- C6 → C7: 42 → 22 prepared rows, 21 → seven distinct clocks, unchanged sleep values for 93 shared RPMh requests
- Comparison caveat: C6 on battery, C7/C8 on AC, no energy comparison
- Native system callbacks: USB runtime-PM opt-in unnecessary for tested clock-release goal
- Post-C8 camera: two ten-frame captures, no saved images, all six camera counts returned to 0/0
- Post-C8 camera evidence: `camera-after/` under C8
- Captured warnings: existing PCIe L2 and IRQ-affinity warnings, no USB clock imbalance or storage errors
- Subsequent real-sleep check: S8 below

## S8 real suspend with UFS/CSI/USB corrections

| Item | Result |
|---|---|
| Evidence | `/var/log/book4-suspend-usbsleep.yulfJf/` |
| Boot | `1513ae6a-a47f-41a6-9f40-615d69bc973e` |
| Configuration | GPU/UFS/CSI/DWC3, combo-only 0008, USB/combo 0009, native PCIe PM |
| Mode | `pm_test=none`, `mem_sleep=deep`, battery-only, manual wake |
| USB policy | Original `on`, no policy or wakeup writes |
| QCE | Temporarily removed, restored after wake |
| Requested / measured sleep | Ten minutes / 614.994 s APSS |
| Observation / monotonic interval | 616.881857 / 1.878619 s |
| Success / failure counters | 2 → 3 / 0 → 0 |
| DDR sleep record | 6153 entries, 598.765862 s |
| D4 / APSS | 599.242754 s / 97.43877% |
| D0 minus active-frequency duration sum | −0.044595 s, within one-second check tolerance |
| CX / AOSS entries | 0 / 0 |
| Final Linux DDR / ACV / MC0 sleep votes | Zero |
| Camera / USB3 clock goal | All 17 tracked clocks released at syscore |
| Final CCF inventory | 216 handles, 22 prepared rows, seven distinct clocks |
| UFS / XO sleep-wake requests | 0/0 / 3/3 |
| PCIe | Both devices D3hot, existing L2 timeout, Gen3 x2 link and Wi-Fi restored |
| Battery endpoints | 59% → 59%, discharging, AC offline |
| Battery sample / awake settling interval | 647.940210 / 31.058353 s |
| Energy interpretation | Unresolved charge change, no wattage estimate or measured improvement |
| Service / both strict checkers | Success / pass |
| Cleanup | QCE loaded, observer/hook/armed absent, `pm_test=none`, policies/wakeup/stable clocks restored |
| Boot preservation | Passed, recovery entries and installed modules unchanged |

- DDR sleep record and D4 duration: independent counters, no rescaling
- Checker controls: synthetic real sleep accepted, core-only/zero-APSS cases rejected, unchanged charge not converted to zero watts
- Initial camera check: two successful ten-frame captures, immediate shared bus-clock counts 1/1, strict failure retained in `camera-after/`
- CCI source: `i2c-qcom-cci.c`, one-second autosuspend, shared CAMNOC/CPAS clocks
- Corrected camera sampling: two further ten-frame captures, bounded settling, CCI active → suspended in 1.217 s each, all six counts 0/0
- Camera evidence: `camera-after-settled/`, images discarded, original checker unchanged
- Energy follow-up: longer battery-only measurement, coordinated manual wake
- Normal QCE-loaded suspend: not the tested configuration

### Remaining USB2 → XO clock path

| Prepared gate | Sampled USB2 PHY consumers | Gate prepare/enable | Cached parent |
|---|---|---:|---|
| `tcsr_usb2_1_clkref_en` | `fd3000.phy`, `fd9000.phy` | 2/2 | `bi_tcxo` |
| `tcsr_usb3_mp0_clkref_en` | `88e1000.phy` | 1/1 | `bi_tcxo` |
| `tcsr_usb3_mp1_clkref_en` | `88e2000.phy` | 1/1 | `bi_tcxo` |

- Consumer drivers: `snps-eusb2-hsphy`, runtime PM unsupported
- TCSR source: fixed single parent, index `DT_BI_TCXO_PAD`
- Parent read: cached `core->parent->name`, no provider status call
- CCF rule: one parent prepare reference per prepared child, independent of child reference multiplicity
- Three prepared gates: account for suspended `bi_tcxo` prepare/enable counts 3/3
- RPMh `xo.lvl=3`: fixed on-level, not a reference count
- Normal `bi_tcxo` state mask: includes sleep, active-only peer excludes sleep
- USB2 source: reference clock enabled in PHY init, disabled in exit, no runtime/system PM callbacks
- Wake-capable DWC3 host path: retained PHY initialization, runtime puts without USB2 provider callbacks
- Attribution boundary: Linux clock/request path identified, sole cause of CX/AOSS inhibition or drain not established
- Safety requirement: validated USB2 low-power/wake sequence before clock release, no blind gating or wake disabling
- Evidence: `usb2-xo-chain.json`, `usb2-source/`, `check-usb2-xo.py`, captured pass and three rejected negative cases

## USB2 system-suspend candidate 0010

| Item | Result |
|---|---|
| Evidence | `/var/log/book4-usb2-pm.ixcKh0/` |
| Patch | `0010-phy-snps-eusb2-suspend-Qualcomm-host-reference-clocks.patch` |
| Driver | `drivers/phy/phy-snps-eusb2.c`, 45 insertions, one deletion |
| Eligibility | Initialized SM8550-compatible PHY, host mode only |
| Suspend | Release owned reference-clock enable/prepare, retain PHY supplies and repeater |
| Resume | Restore clock, propagate enable failure, retain suspended flag for retry |
| Failed-resume exit | Skip duplicate clock disable, retain normal regulator/repeater cleanup |
| Exclusions | Exynos, device/unknown mode, uninitialized PHYs |
| Unchanged | Runtime PM, wake policy, hibernation callbacks, PHY register programming |
| Generic-PHY pointer | Assigned at probe, native init count for initialization guard |
| PM ordering | Existing consumer → generic PHY → provider device links |
| Native controller sequence | Host suspend/SUSPHY, QCOM L2 check and wake IRQ setup, then PHY provider suspend |
| Offline check | Actual init/exit/PM helpers, 100 cycles, four PHYs sharing three gates |
| Error paths | Seven init failure stages, repeated suspend/resume, resume failures/retry, exit after failure |
| Negative controls | Original source and six guard/error-path mutations rejected |
| Native build | No warnings, 30 unchanged imports, matching vermagic |
| Patch check | Forward/reverse/forward source roundtrip, extracted-helper regression passed |
| New image | `/boot/initramfs-book4-pciepm-usb2sleep.img` |
| Archive delta | Only `phy-snps-eusb2.ko`, 367 matching module vermagics, unchanged metadata and other content |
| Image SHA256 | `37465b3d279e65a82da9def1da25b8542ff72458bd062790662af92273231f32` |
| Entry | Existing `arch-pcie-ufs-pm.conf`, title `Arch Linux (GPU + UFS + CSI + USB2 sleep test)` |
| Retained fixes | GPU/UFS/CSI/DWC3, combo-only 0008, USB/combo 0009 |
| Preservation | 3080 protected files, two symlinks, authorized entry replacement only |
| Recovery | Default `arch.conf`, fallback, Windows, previous images and installed root modules unchanged |
| Publication | Image first, entry last, fsync and atomic rename, installed validation passed |
| Hardware at publication | Original eUSB2 module loaded, no live replacement or PM-policy changes |
| Verified boot | `8dfc6ffc-9398-4bab-860d-e9af8f1bfda8`, expected kernel/module notes, original policies, observer removed |
| New-boot suspend counters | Success 0, failure 0, no 0010 suspend test |
| Review boundary | USB mode and resume-failure audit before further suspend testing |

- Downstream reference: [Qualcomm eUSB2 host bus suspend](https://github.com/LineageOS/android_kernel_qcom_sm8550/blob/lineage-21/drivers/usb/phy/phy-msm-snps-eusb2.c#L780-L823)
- Reference blob: `df26b5e02b7c54430370cab7b7a044b63aae3778`, fetched contents checked against Git blob hash
- Downstream host path: clock stop only, no regulator disable or repeater reset
- Downstream controller prerequisite: `dwc3_msm_prepare_suspend()`, L2 check before PHY suspend
- Native controller limitation: missing L2 acknowledgement logged rather than fatal, no independent PHY L2-status probe added
- S8 native L2 warnings: none, not hardware proof for the new module
- Initial harness gap: Exynos clock check after resume only, guard-removal mutation incorrectly accepted
- Harness correction: unchanged Exynos clocks required immediately after suspend, original false acceptance retained in `negative-first/`
- Roundtrip execution failure: root-only evidence directory, corrected group access, original `PermissionError` retained
- Staging negative controls: old boot rejected before observer load, altered staged kernel entry rejected and restored
- Hardware clock release, XO request removal, USB wake, CX/AOSS collapse and energy improvement: unverified

## USB wall-outlet charging check

| Item | Result |
|---|---|
| Evidence | `/var/log/book4-wall-usb.zvxc81pe/` |
| Reported source | USB wall outlet, estimated 5–10 W, capability unverified |
| Boot | `41000b07-d58b-44b3-a574-3fc06e236411` |
| Battery / AC | 30%, discharging, AC offline |
| Battery readings | 14.963–14.977 V, discharge 270–332 mA, approximately 4–5 W net battery output |
| Attached port | `a9c000.i2c`, attach `0x09`, switch status `0x00` |
| Other port | `a84000.i2c`, attach/switch `0x00` |
| Cached Source_Capabilities | Both ports zero-filled, no valid PD capabilities |
| Charging daemon | Active, installed script matches repository, no charging actions logged this boot |
| Input re-arm guard | `userspace/charging/book4-pd-charge:120`, valid PD Source_Capabilities required before consumer-switch request |
| Offline guard reproduction | Actual helper, attached/open status, zero capabilities rejected, synthetic 5 V-only PD advertisement accepted |
| Reproduction artifacts | `check-rearm-guard.py`, `rearm-guard-result.log`, no hardware commands |
| Non-PD input | No validated alternate enable path in current helper |
| Live DT I2C controllers | Three enabled/bound buses, no child-device descriptions for the PD controllers or charger |
| DT Type-C path | PMIC GLINK/UCSI declared, driver bound, corresponding RPMsg endpoint absent, no Type-C ports |
| Attribution boundary | Confirmed helper limitation, missing working Type-C integration, firmware defect or specific DT correction unproven |
| Hardware input-voltage limits | Unverified, older higher-than-pack input requirement not established by these tests |
| Diagnostic operations | Status/capability reads only, no PD controls, no policy changes |
| Interpretation | Consistent with a basic non-PD source, not proof of outlet/cable failure or hardware charging limits |
| Next comparison | Known-good USB-C PD laptop charger and cable, manual connection |

## Remaining work

| Area | Gap / constraint |
|---|---|
| DWC3 0007 | Global root-hub hook removal, calibration and host-mode semantics need review, peripheral/hotplug/wake untested |
| QMP mode selection | `HOST` versus `HOST_SS` selects different autonomous wake interrupts, 0007 suppresses root-hub mode update |
| QMP | Peripherals/hotplug/wake/DisplayPort and energy comparison |
| CSI | Energy comparison |
| USB2 `phy-snps-eusb2.c` | 0010 boot verified, `HOST_SS` excluded without 0007, init-count synchronization and consumer resume after clock failure need review |
| Wake-capable DWC3 suspend | Retained PHY initialization, USB2 runtime puts return `-ENOTSUPP` |
| USB2 safeguards | No blind gating or disabled wakeup |
| QCE | Proper PM handling, no permanent blacklist |
| Unused-clock/domain flags | Separate test-entry boots without `clk_ignore_unused`, then `pd_ignore_unused`, recovery entry retained |
| Clock-summary boundary | Awake snapshot, `clk_pm_runtime_get_all()` can resume providers, no proof of final sleep state |
| GCC | Existing `GDSC_SLEEP_ENA_VOTE` clear at `0x52224`, safety/relevance unresolved |
| PCIe | Physical L2 timeout |
| XO and energy | Verify 0010, compare final XO/CX/AOSS results, longer coordinated battery measurement |
| RTC | `efi=noruntime` versus `qcom,uefi-rtc-info`, ADSP-owned alarm, no ownership bypass |
| Cold hibernation | Reset stage unknown, remoteproc/shared-memory restoration hypothesis unproven |

## Evidence index

| Scope | Local directory |
|---|---|
| S1 | `/var/log/book4-suspend-check.pwaEdU/` |
| S2 | `/var/log/book4-suspend-noqcrypto.pTMRC1/` |
| S3 | `/var/log/book4-suspend-votes.TXypw5/` |
| S4 | `/var/log/book4-suspend-gmufix.8HO4pf/` |
| S5 | `/var/log/book4-suspend-gmufix-noqce.x6Dm0d/` |
| S6 | `/var/log/book4-suspend-pcie.jZz1E4/` |
| S7 | `/var/log/book4-suspend-overnight.kkHmV4/` |
| S8 / remaining USB2-XO path / post-sleep camera | `/var/log/book4-suspend-usbsleep.yulfJf/` |
| DDR statistics | `/var/tmp/book4-stats-qmp/` |
| Original observer | `/var/tmp/book4-sleep-votes/` |
| GPU build/deployment | `/var/backups/book4-gmu-sleep.XhF7kO/` |
| PCIe build/boot | `/var/log/book4-pcie-pm.16plHM/` |
| C1 | `/var/log/book4-pmtest-pcie.zisWUQ/` |
| Awake RPMh | `/var/log/book4-rpmh-votes.pyQf8E/` |
| C2 and UFS source/build | `/var/log/book4-pmtest-rpmh.HyvvhD/` |
| UFS staging | `/var/log/book4-ufs-boot.D9mRHI/` |
| UFS runtime | `/var/log/book4-ufs-runtime.JU75q9/` |
| C3 | `/var/log/book4-pmtest-ufs.cCB8JJ/` |
| C4 | `/var/log/book4-pmtest-ufs-retry.390NIe/` |
| CSI / awake CCF | `/var/log/book4-xo-clocks.HXZCD4/` |
| C5 / menu cleanup | `/var/log/book4-pmtest-xo.gHQdDc/` |
| USB runtime / source / builds | `/var/log/book4-usb-runtime.TNR1KI/` |
| DWC3-only candidate | `/var/log/book4-dwc3-boot.TEm2nD/` |
| DWC3-only awake USB test | `/var/log/book4-usb-dwc3.51tldC/` |
| Combo-only QMP preparation and boot | `/var/log/book4-qmp-boot.z6SR7q/` |
| Both USB-C runtime-PM checks | `/var/log/book4-usbc-runtime.QcQmyC/` |
| Phone role/attachment/MTP | `/var/log/book4-usbc-phone.3MjP6V/` |
| CSI preparation / boot / camera | `/var/log/book4-csi-boot.7Hyb13/` |
| C6 / post-callback camera | `/var/log/book4-pmtest-csi-usb.I2K9AN/` |
| QMP system-suspend source / build / staging / boot | `/var/log/book4-qmp-system.hJimk0/` |
| C7, temporary USB `auto` | `/var/log/book4-pmtest-usbsleep.WYwcoJ/` |
| C8, original USB `on`, camera regression | `/var/log/book4-pmtest-usbsleep-on.WKr5AM/` |
| USB2 candidate 0010, source/build/staging | `/var/log/book4-usb2-pm.ixcKh0/` |

## Repository checks

```sh
sudo -u hamza python3 scripts/test-suspend-fixes.py
sudo -u hamza python3 scripts/test-gmu-sleep.py /home/hamza/Projects/linux-book4-pcie-pm
sudo -u hamza python3 scripts/test-ufs-clocks.py /home/hamza/Projects/linux-book4-pcie-pm
sudo -u hamza python3 scripts/test-csiphy-clocks.py /home/hamza/Projects/linux-book4-pcie-pm
sudo -u hamza python3 scripts/test-usb-phy-pm.py /home/hamza/Projects/linux-book4-pcie-pm
sudo -u hamza python3 scripts/test-qmp-system-pm.py /home/hamza/Projects/linux-book4-pcie-pm
sudo -u hamza python3 scripts/test-eusb2-system-pm.py /home/hamza/Projects/linux-book4-pcie-pm
sudo -u hamza git diff --check
```
