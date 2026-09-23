# Clock/domain synchronization candidate

- Status: offline candidate, excluded from maintained patches 0001–0006
- Base: `2685c75587ff`, shared `drivers/clk/qcom/common.c`
- Evidence: `/var/log/book4-clock-sync-fix.3Q99z4/`
- Running kernel, boot entries, installed modules and kernel worktree: unchanged
- Native object build only, no new kernel image or hardware test

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

## Remaining validation

1. Clean maintained-source kernel build and module-ABI checks, USB experiments excluded
2. Manual test-entry boot, fallback and previous payloads preserved
3. Runtime callback ownership, actual per-provider cleanup messages, QCE/ICC readiness
4. Camera, USB, Wi-Fi, storage and five-second core diagnostic
5. Coordinated real sleep and recovery
6. Longer battery measurement, including normal QCE-loaded operation

- No live supplier synchronization or provider replacement
- Source/model checks: no proof of hardware-access safety or energy savings
- Existing experimental kernel worktree: unsuitable for an unfiltered full rebuild
