# Cached suspend observer

- Experimental diagnostic, no automatic installation or loading
- Kernel source base: `2685c75587ff`, `config/pcie-pm-test.config`
- Private kernel types: identical declarations and matching build/config required
- Source-layout check: necessary, not an ABI guarantee across configs or kernels
- Syscore samples: cached references/votes, not physical rail measurements
- Explicit platform coverage only, no complete firmware inventory
- Existing source/captures: `reports/suspend-investigation.md`

```sh
python3 driver/book4-sleep-votes/check-layout.py /path/to/kernel
make -C /path/to/kernel LOCALVERSION= M="$PWD/driver/book4-sleep-votes" modules
```

- Loading/unloading: coordinated tests only
- No boot-time module configuration
- Cleanup: unload `sleep_votes`, restore original PM policies and QCE state
