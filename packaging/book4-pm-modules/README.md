# Maintained Book4 test modules

- Target: `7.2.0-book4-pciepm`, existing GPU-fixed/native-PCIe kernel
- Scope: UFS 0005 and CSI 0006 modules, initramfs config, preset and package-update hook
- Prerequisite: matching configured and fully built kernel source with patches 0001–0006
- PCIe config: `config/pcie-pm-test.config`, exact compiler/config compatibility required
- Current tested CSI module: existing CSIPHY diagnostic patch retained
- Full kernel/DTB packaging: not included
- USB experiments 0007–0010: not installed
- Build from this repository, normal user

```sh
cd packaging/book4-pm-modules
KERNEL_TREE=/path/to/matching-built-kernel makepkg -si
sudo mkinitcpio -p book4-pm
modinfo -k 7.2.0-book4-pciepm -n ufs_qcom
modinfo -k 7.2.0-book4-pciepm -n phy_qcom_mipi_csi2
```

| Item | Location |
|---|---|
| Corrected modules | `/usr/lib/modules/7.2.0-book4-pciepm/updates/book4-pm/` |
| Original modules | Existing `kernel/` paths, unchanged |
| Config | `/etc/mkinitcpio-book4-pm.conf` |
| Preset | `/etc/mkinitcpio.d/book4-pm.preset` |
| Rebuilt image | `/boot/initramfs-book4-pm.img` |
| Update hook | `91-book4-pm.hook`, depmod then preset rebuild |
| Source/config updates | Rebuild package and initramfs, verify notes before testing |
| Boot-entry selection | Separate manual step, package does not change the default |

## Rollback

- Select the unchanged fallback entry before removing the package
- Restore the saved experimental entry only if deliberately returning to that experiment
- Package removal does not delete historical boot images or edit loader entries

```sh
sudo pacman -R book4-pm-modules
sudo depmod 7.2.0-book4-pciepm
modinfo -k 7.2.0-book4-pciepm -n ufs_qcom
modinfo -k 7.2.0-book4-pciepm -n phy_qcom_mipi_csi2
```

- Expected post-removal module locations: original `kernel/` paths
- Maintained image after package removal: stale snapshot, not automatically rebuilt
- Boot-time `module_blacklist=qcrypto`: rejected, blocks interconnect synchronization and retains initialization bandwidth floors
- QCE tests: allow probe, verify interconnect synchronization, unload temporarily only with no users, restore afterward
- Readiness check after unload: `python3 scripts/test-qce-fallback.py`
- No global crypto blacklist, no changes to USB wake policies
