# Linux on the Samsung Galaxy Book4 Edge 15.6" (NP750XQA)

- SoC: Snapdragon X Plus X1P42100
- Contents: device tree, kernel patches/config, EC driver, firmware, userspace
- Status: daily-driver configuration, as-is, unsupported
- Base: `zensanp/linux-book4-edge @ 2685c75587ff`
- Branch: `x1e80100-book4e-7.2-14-tmp`, Linux 7.2
- Kernel config: `config/book4-edge.config`
- Board DTS: `dts/`, identical to patch 0003

## What works

| Function | State |
|---|---|
| Display (KDB KD156N2030A03 eDP), backlight | Working, patch 0001 |
| Boot splash | `userspace/boot-splash`, incompatible with Plymouth |
| GPU (Adreno X1-45, freedreno/turnip) | Working, devfreq floor in `userspace/udev/90-book4-gpu-floor.rules` |
| Keyboard, touchpad | Working, tablet-misdetection workaround in `userspace/udev/61-…` |
| UFS storage | Working |
| Wi-Fi (WCN7850) | Working, board file from `scripts/make-board-2.sh` |
| Bluetooth | Working, manual address configuration |
| Speakers (2x WSA883x), 4 DMICs | Working, EQ/limiter and echo cancellation in `userspace/audio` |
| Headset jack | Unverified |
| Camera (OV02C10, 2 MP) | Working through libcamera, `userspace/camera` required |
| USB-C charging | Input-limit correction in source, hardware validation pending |
| Battery, AC, EC temperatures, fan level | `driver/samsung-galaxybook-ec` |
| Suspend | Experimental DDR low-power residency, remaining drain ~2.5 percentage points/hour, [evidence](reports/suspend-investigation.md) |
| Hibernate | In-place `test_resume` successful, cold resume reset |
| HDMI out, SD card, second USB2 port | Not wired / untested |
| Video decode (iris) | Driver built, DT node disabled |
| RTC | Probe deferred, stale time until NTP |

## Build

```sh
git clone https://github.com/zensanp/linux-book4-edge && cd linux-book4-edge
git checkout 2685c75587ff
git am ../patches/*.patch                 # Maintained series 0001–0006
cp ../config/book4-edge.config .config && make olddefconfig
make -j"$(nproc)" Image vmlinuz.efi modules dtbs
sudo make modules_install
```

### Userspace and EC driver

```sh
sudo ./install.sh                                     # Firmware, charging, memory, audio, camera, udev
cd userspace/camera/libcamera && makepkg -si           # OV02C10 libcamera helper
cd driver/samsung-galaxybook-ec && sudo dkms install .  # EC driver
scripts/make-board-2.sh && sudo cp board-2.bin /usr/lib/firmware/ath12k/WCN7850/hw2.0/
sudo userspace/boot-splash/install.sh                  # Optional splash and msm gate
```

### Boot files

| Item | Destination / requirement |
|---|---|
| `arch/arm64/boot/vmlinuz.efi`, DTB, initramfs | Boot partition |
| Loader entry | `boot/loader-entry-example.conf` |
| Kernel option | `efi=noruntime` |
| EFI variables at runtime | Unavailable |
| systemd-boot on internal disk | `EFI/Microsoft/Boot/bootmgfw.efi` |

## Suspend and hibernate

- Clock/domain candidate, QCE loaded: 92% → 70% over 8 h 52 min, approximately 1.57 W, no DDR low-power residency
- Same candidate, temporary QCE unload: 91% → 76% over 5 h 41 min, approximately 1.61 W, DDR low-power residency 97.43%
- QCE opt-out: residency improved, battery-drain improvement not demonstrated, unequal durations and gauge-estimate limits
- Overnight battery suspend: unsafe for unattended use
- Hibernate: working in-place `test_resume`, cold-resume dark screen and reset
- Daily use: `systemctl poweroff`, hibernate disabled
- Optional lid action: poweroff, saved work required

```sh
sudo mkdir -p /etc/systemd/logind.conf.d
printf '[Login]\nHandleLidSwitch=poweroff\nHandleLidSwitchExternalPower=poweroff\nHandleLidSwitchDocked=poweroff\n' | sudo tee /etc/systemd/logind.conf.d/10-lid.conf
```

- Activation: next reboot
- Desktop lid inhibitors: possible logind override, actual-action verification required
- Shutdown power consumption: unmeasured

## Prebuilt snapshot

| Item | Value |
|---|---|
| Release archive | `book4-edge-<version>.tar.zst` |
| Contents | Kernel image, DTB, initramfs with DSP firmware, modules |
| Checksums | `SHA256SUMS` |
| Source | Tagged commit, one-time snapshot |
| Boot files | `boot/*` → boot partition |
| Modules | `lib/modules/<version>` → `/lib/modules/` |
| Module dependencies | `depmod <version>` |
| Loader | Local root/resume options required |
| Userspace | `install.sh` |
| Later kernels | Source builds |

## Packages

```text
linux-firmware linux-firmware-qcom linux-firmware-atheros
mesa vulkan-freedreno pipewire wireplumber alsa-ucm-conf
swh-plugins i2c-tools earlyoom iwd networkmanager bluez bluez-utils dtc
```

- Camera: three packages from `userspace/camera/libcamera/`
- Adreno X1-45: Mesa ≥ 26.2
- Packaged Wi-Fi setup: NetworkManager with iwd, `userspace/network/`
- Eduroam diagnostic: verified PEAP/MSCHAPv2 with CA and server-name validation
- Time synchronization: `systemd-timesyncd`, no working RTC

## Initramfs

- Config: `boot/mkinitcpio-book4.conf` → `/etc/mkinitcpio.conf.d/`
- Early modules: display, storage, DSPs
- Embedded files: DSP firmware
- Rebuild required after firmware installation
- Maintained PCIe test image: [UFS/CSI module package and preset](packaging/book4-pm-modules/README.md)
- Test-image rebuild: `mkinitcpio -p book4-pm`, fixes selected from installed module overrides

```sh
mkinitcpio -k <kernel version> -g /boot/initramfs-book4.img
```

## Firmware

| Item | Source / scope |
|---|---|
| Board directory | `/usr/lib/firmware/qcom/x1p42100/SAMSUNG/NP750XQA/` |
| Installation | Ten files from `firmware/`, via `install.sh` |
| Audio DSP, battery/charger service | `qcadsp8380.mbn` |
| Compute DSP | `qccdsp8380.mbn` |
| DSP device trees | Two DT blobs |
| GPU zap shader | `qcdxkmsucpurwa.mbn` |
| Five signed board files | Samsung Windows drivers, absent from linux-firmware |
| Redistribution licence | Unavailable, `firmware/README.md` |
| Missing signed firmware | Console-only boot, no GPU/audio/battery state |
| Local extraction | `scripts/extract-firmware.sh`, checks against `firmware/SHA256SUMS` |
| Other GPU/Bluetooth/Wi-Fi firmware | linux-firmware |
| Wi-Fi board file | Local build via `scripts/make-board-2.sh`, redistribution prohibited |

## Pieces

| Path | Contents |
|---|---|
| `dts/` | Board file, BSD-3-Clause, header credits |
| `config/` | Kernel config and option differences |
| `driver/samsung-galaxybook-ec/` | ENE KB9058 over I2C, battery/AC/three temperatures/fan level, read-only default, out-of-tree or DKMS |
| `driver/book4-sleep-votes/` | Version-specific cached suspend observer, private-layout check, no automatic loading |
| `packaging/book4-pm-modules/` | Maintained UFS/CSI module overrides and initramfs preset |
| `userspace/charging/` | S2MM006 PD and ISL9241 charging |
| `userspace/memory/` | Half-RAM zstd zram, earlyoom, out-of-tree `zram-mod/build.sh` for kernels without ZRAM |
| `userspace/audio/` | Samsung ALSA UCM, four-slot FL/RL/FR/RR mapping, measured EQ/limiter, echo cancellation |
| `userspace/camera/` | libcamera 0.7.2, OV02C10 sensor helper/tuning, CPU software ISP |
| `userspace/boot-splash/` | DRM splash and msm modprobe gate, paired installation required |
| `scripts/` | Firmware extraction, Wi-Fi board builder, vendored ISC `ath12k-bdencoder` from qca-swiss-army-knife |
| `reports/` | EC/PD protocols, DSDT disassembly, panel EDID, suspend evidence |
| `docs/camera-debugging.md` | Camera diagnostic methods |

### Kernel patches

| Patch | Change | Validation |
|---|---|---|
| 0001 | panel-edp panel entry | Working display |
| 0002 | Board-specific front-camera HFLIP | Working camera |
| 0003 | Board DTS, DDR-statistics QMP link | Boot and counter refresh verified |
| 0004 | GPU power-down guard | Boot/resume verified, DDR frequency hold removed |
| 0005 | UFS clock-reference guard | Boot/runtime-PM/callback verified, UFS sleep vote cleared, power benefit unmeasured |
| 0006 | Camera-PHY probe reference removal | Boot and camera captures before/after real suspend verified, idle camera clocks released |
| `patches/experimental/usb/` 0007–0010 | USB ownership and PHY PM experiments | Excluded from maintained builds, unresolved mode/wake/error propagation, [review](patches/experimental/usb/README.md) |
| `patches/experimental/clock-sync/` | Clock/domain callback composition | Boot/core/short and overnight recovery passed, energy benefit unresolved, [candidate](patches/experimental/clock-sync/README.md) |
| `patches/debug/` | CSIPHY diagnostics | Present in verified kernel, not a fix |

- Maintained test deployment: packaged UFS/CSI overrides, ordinary preset rebuild verified, original USB drivers
- Historical USB images: isolated snapshots, not maintained configurations
- Reference baseline: both unused-resource flags retained, probe-first QCE opt-out
- QCE boot blacklist: withdrawn, blocked interconnect synchronization and retained maximum initialization votes
- Post-probe QCE unload: crypto/PM-readiness, core callbacks and 21-minute real sleep passed, final DDR/UFS sleep requests zero
- Short baseline: DDR D4 97.43% of APSS sleep, battery 51% → 50%, no precise energy comparison or CX/AOSS collapse
- Clock-flag test: boot/core/camera and 38-minute real sleep passed, DDR D4 97.44%, battery 45% → 43%, no established energy benefit
- Maintained no-flags reference: boot/core/camera and 20-minute real sleep passed
- Current test: **Arch Linux (PM test, clock-domain sync)**, boot/core/short and overnight recovery passed, unchanged initramfs/DTB/modules
- No-flags real sleep: DDR D4 97.44%, battery 40% → 39%, approximately 1.62 W from coarse SOC endpoints, no established energy benefit
- Three-boot comparison: final sampled clocks and RPMh requests identical, no CX/AOSS collapse, QCE and original device policies restored
- Clock-cleanup gap: corrected in the running candidate, six composite callbacks verified, previously missing native sweeps now logged
- Candidate real sleep: 9m50s, DDR D4 97.43%, cached clocks/RPMh requests unchanged, battery 96% → 96% below measurement resolution
- Normal QCE-loaded core: recovery passed, DDR sleep request 393600/393600 kB/s, initialization floors zero
- Normal QCE-loaded overnight: 8h52m, battery 92% → 70%, approximately 1.57 W, no DDR D4 or CX/AOSS entries, recovery passed
- Same-candidate long QCE opt-out: 5h41m, battery 91% → 76%, approximately 1.61 W, DDR D4 97.43%, recovery passed
- No established battery saving from QCE opt-out, no further overnight test scheduled
- Default `arch.conf`: older GPU-fixed fallback, unchanged
- Current status: [suspend investigation](reports/suspend-investigation.md), full history archived separately

### Charging constraints

- Daemon operations: consumer-switch closure, higher-rail request, charger programming
- Provider ports: excluded from switch control, PD negotiation and input-limit selection
- Re-arming: one open input
- Multiple closed inputs: deferred PD and limit changes
- Input limit: supplying port's last Request and selected source PDO
- Existing 20 V / 3 A setup: 3000 register target
- Hardware validation pending: contract acceptance, register scaling, ownership
- PDIC notes: `reports/ec/07-pdic-s2mm006.md`
- Bad PD transmission: reported machine reset
- `i2c-wake/`: runtime overlay for DTBs without the three Type-C I2C buses

### Audio and camera constraints

- UCM: missing Samsung profile in alsa-ucm-conf
- UCM matching: full card long name including SKU suffix, installer-generated include name
- Microphone low-pass: disabled, unnecessary with the DTS's 2.4 MHz DMIC clock
- OV02C10 helper: required for AGC gain increases
- Camera GPU software ISP: missing AGC statistics, black image in dim rooms
- Firefox/Zen: `media.webrtc.camera.allow-pipewire = true`
- Chromium: `WebRtcPipeWireCamera`, `docs/browsers.md`

## Bluetooth address

- Default without `local-bd-address`: QCA address
- Address source: Windows Device Manager → Bluetooth adapter → Advanced
- DTS option: reversed address bytes in `bluetooth`
- Runtime option: `btmgmt -i hci0 public-addr XX:XX:XX:XX:XX:XX`

## What is verified

| Scope | Result |
|---|---|
| Working hardware table | Original base with patches 0001–0003 |
| Initial running-config differences | Zram/hidraw-related options in `config/README.md` |
| DTS versus original running DTB | Three Type-C I2C buses and DDR-statistics QMP link |
| GPU guard | Regression/build/boot/deep-resume pass, DDR 4224 → 547 MHz |
| [Experimental PCIe PM](config/README.md#experimental-pcie-suspend-test) + GPU fix + temporary QCE removal | ~97% DDR D4 residency over 8 h 20 min |
| Overnight battery, experimental kernel with temporary QCE removal | 76% → 55%, approximately 1.6 W |
| CX/AOSS collapse | None |
| Suspend drain | Unresolved, [investigation](reports/suspend-investigation.md) |
| Original snapshot build | Fresh-clone build complete |
| Second-install snapshot boot and camera without debug patches | Pending |

## Credits

- zensanp: base kernel
- Kirill A. Korinsky, Valentin Manea: X1E80100 Book4 Edge DTS
- Jens Glathe: ThinkBook 16 eDP power/backlight wiring
- saddytech: EC mailbox protocol
- libcamera, linux-firmware projects

## Licences

| Component | Licence |
|---|---|
| Kernel patches, EC driver, scripts | GPL-2.0-only |
| Device tree | BSD-3-Clause |
| libcamera patches | LGPL-2.1-or-later |
| Tuning file | CC0-1.0 |
