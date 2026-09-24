# Clock/domain synchronization candidate

- Status: boot/core/short real sleep verified, energy benefit unresolved, excluded from maintained patches 0001–0006
- Base: `2685c75587ff`, shared `drivers/clk/qcom/common.c`
- Source-regression evidence: `/var/log/book4-clock-sync-fix.3Q99z4/`
- Image-build and publication evidence: `/var/log/book4-clock-kernel.KFFCOc/`
- Clean source tree: `/home/hamza/Projects/linux-book4-clock-sync`
- Candidate: `/boot/vmlinuz-book4-clksync.efi`
- Test entry: **Arch Linux (PM test, clock-domain sync)**
- Running kernel: candidate build verified by notes
- Installed modules, initramfs, DTB and default/fallback: unchanged
- Boot/core evidence: `/var/log/book4-clock-baseline.0PgY4A/`
- Real-sleep evidence: `/var/log/book4-suspend-clock.qB0ZiX/`
- QCE-loaded core evidence: `/var/log/book4-qce-loaded-core.mp3Myn/`
- Hardware coverage: native cleanup, core callbacks, short real sleep and recovery passed
- Energy benefit: unresolved, normal QCE-loaded overnight pending

## Mechanism

- Existing registration: GDSC callback first, conflicting CCF callback rejected with ignored `-EBUSY`
- Global late CCF sweep: device-owned clocks skipped
- Candidate: shared default callback installed before provider registration
- Default order: `clk_sync_state()` → `of_genpd_sync_state()`
- Early board-clock `clk_sync_state` callback: upgraded to the same composite
- Explicit callbacks: preserved
- Existing `qcom_cc_sync_state`: ICC → clocks → domains
- Non-ICC providers: no `icc_sync_state()` call
- ICC constraint: global call counter, no per-device provider check
- Native clock reference counts, ignore flags, runtime-PM handling and domain guards: unchanged

## Checks

| Check | Result |
|---|---|
| Caller census | 187 driver source files using shared probe entry points |
| Explicit callbacks in those callers | Six `qcom_cc_sync_state` users, matching six ICC descriptors |
| Early board clocks | APQ8084, MSM8974, IPQ806x, MSM8960 and MSM8916 |
| Original source | Runtime assertion failure, clock cleanup missing |
| Candidate source fragments | Default and early-clock owners, repeated setup, shared driver, domain-less devices and explicit callbacks passed |
| Ordering | Clock cleanup before domain power-off, ICC first for explicit ICC providers |
| Seven mutations | Runtime assertions rejected missing/reordered cleanup, lost early-clock handling, custom override and false ICC participation |
| Native object | Matching kernel headers/config/compiler, exported symbol names unchanged |
| New undefined symbol | `of_genpd_sync_state` only |

```sh
python3 scripts/test-qcom-cc-sync.py /path/to/patched/kernel
```

## Image validation

- Maintained 0001–0006 plus this candidate, original USB source
- Clean control Image: identical to original apart from kernel and embedded-vDSO GNU build IDs
- Metadata reproduction: original weak banner and empty built-in archive timestamps
- Original one-ID comparison failure: retained, separate two-ID checker with code-byte and malformed-note rejection
- Candidate delta: only `drivers/clk/qcom/common.o` among 4,464 linked input objects
- Headers: 26,950 source headers and generated ABI headers identical
- Configuration and kernel export table: identical
- `CONFIG_MODVERSIONS`: disabled, no symbol-CRC assurance or vermagic-only claim
- Native disassembly: clocks → domains, explicit ICC wrapper ICC → clocks → domains
- Embedded compressed Image: verified against the built Image
- Kernel build ID: `792e7ffafc2bc8093b384842a085067404d10c08`
- EFI SHA256: `5d578e363ec9b479fe1fd1c986dac44bd75c10d987860f806fe5e01534115ceb`
- Release: `7.2.0-book4-pciepm`, build notes required for identification
- Cached callback inspector: six composite callbacks verified, unloaded afterward
- Publication controls: rollback and forbidden option/initramfs/DTB/kernel changes rejected
- Boot controls: same boot, old loaded kernel, bad payload hash and old entry rejected
- Historical Windows data/configuration differences: unchanged, full historical preservation still unproven

## Boot and core result

- Boot: `c4e15e7d-2d37-4595-b418-6aef7e7e6f56`
- GCC/GPUCC/CAMCC/DISPCC/VIDEOCC/TCSRCC: composite callback and native clock-sweep messages verified
- Core diagnostic: success 0 → 1, failure 0, APSS unchanged
- Interval: 6.905795 s, monotonic: 1.903079 s, no real deep sleep
- Final cached clocks and RPMh requests: identical to previous no-flags core
- DDR/UFS: zero sleep requests, XO: 3/3
- QCE/ICC, original USB policy/counts, Wi-Fi and discarded camera captures before/after: passed
- Sixteen checker negative controls and captured-result reproduction: passed
- Native cleanup coverage: corrected, no energy-saving claim

## Real sleep and normal QCE-loaded core

- Real sleep with temporary QCE opt-out: APSS 590.117 s, success 1 → 2, failure 0
- DDR D4/APSS: 97.43008%, no CX/AOSS entries
- Final cached clock samples and RPMh requests/batches: match all three flag-only real sleeps
- Battery: 96% → 96%, unresolved charge drop, no zero-watt claim
- QCE/ICC, USB policy/counts, camera and Wi-Fi recovery: passed
- Normal QCE-loaded core: success 2 → 3, failure 0, APSS unchanged
- Loaded-core DDR requests: 393600/393600 kB/s, initialization floors zero, zero-vote goal false
- Loaded-core generic crypto and device recovery: passed, 21 negative controls
- Explicit QCE AF_ALG execution: excluded by native API mask, not a hardware execution test

## Remaining validation

1. Normal QCE-loaded overnight drain and real-sleep recovery
2. Longer matched energy comparison, cold hibernation remains separate

- No live supplier synchronization or provider replacement
- Source/model checks: no proof of hardware-access safety or energy savings
- Existing experimental kernel worktree: unsuitable for an unfiltered full rebuild
