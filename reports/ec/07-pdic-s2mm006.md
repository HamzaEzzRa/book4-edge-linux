# S2MM006 PDIC: the USB-C PD controller and the real charging gap

The S2MM006 PD controller, not the EC, is the charging path.

## Non-PD 5 V input limitation — 2026-09-21

| Item | Finding |
|---|---|
| Source | USB wall outlet, estimated 5–10 W, actual capability unverified |
| Attachment | Detected, S2MM006 attach `0x09` |
| Charging input | Switch status `0x00`, AC offline, battery discharging |
| PD capabilities | Cached Source_Capabilities zero-filled |
| Confirmed software block | `rearm_pd_bus()` requires `source_caps()` before enabling the input |
| Code | `userspace/charging/book4-pd-charge:120` |
| Offline control | Missing PD capabilities rejected, synthetic 5 V-only PD source eligible |
| Distinction | PD-message requirement, not a higher-voltage requirement |
| DT / Type-C integration | I2C buses enabled, PMIC-GLINK/UCSI declared and bound, corresponding RPMsg endpoint absent, no Type-C ports |
| Firmware or specific DT defect | Unproven |
| Hardware acceptance of non-PD 5 V | Unverified |
| Evidence | `/var/log/book4-wall-usb.zvxc81pe/` |

- Follow-up: non-PD source detection, power-role validation, advertised current decoding through CC or BC1.2 as applicable
- Charger limits: board current-sense scaling and safe input-current limit validation
- Prohibited shortcut: removing the PD guard without a validated non-PD input path
- Preserved policy: no firmware, DTB, PD-control or charging-helper changes during this check
- Historical bus numbers below: resolve current adapters by physical controller address

## Bus map (exact)

DSDT controller base addresses matched against the DT nodes:

| DSDT | base | Linux bus | devices |
|---|---|---|---|
| IC10 | 0xA84000 | i2c-10 | PDIC port 0 @ 0x33 |
| IC16 | 0xA9C000 | i2c-11 | PDIC port 1 @ 0x33 |
| IC21 | 0x890000 | i2c-12 | charger @ 0x09, battery @ 0x0B |
| IC19 | 0x888000 | i2c-0 | ptn3222 redrivers @ 0x43/0x4F |

i2c-10/11/12 only exist after `insmod ~/book4-edge/i2c-wake/i2c-wake.ko`.

## The PD controller

`Device (EMEC)` / SAM0604 ("Emulated EC") is `EmuEc.sys`'s device. The PD chip is a
Samsung S2MM006 PDIC (strings `S2MM006_REG_BC_INT`, `S2MM006_REG_PD_CTRL1`,
`s2mm006_select_pdo`, `S2MM006xxx_init`). Same family as the GPL s2mm005
(Galaxy phone kernels), but not the same register layout.

Access protocol (verified on hardware, read and write both work): 2-byte
big-endian register address, then data.

    read :  i2ctransfer -y 10 w2@0x33 <hi> <lo> r<N>
    write:  i2ctransfer -y 10 w3@0x33 <hi> <lo> <byte>

From `EmuEc.sys`: read `0x140039fe8(port, reg, buf)` -> `0x140007628(bank, uxth(reg), buf, 1)`;
write `0x14003a128(port, reg, buf)` -> `0x1400077e8(...)`. `uxth` confirms 16-bit regs.

## Register findings (port 0, cable attached)

- `0x02..0x07`: interrupt status, write-back-to-clear. Read `09 5e 1e 00 00 00`
  while wedged; writing those values back cleared them to zero and they stayed clear.
  Doing so did not restart negotiation, so the chip was not stalled on interrupts.
- `0x0E` = 0x03 attached / 0x00 detached. `0x11`, `0x12`, `0x14` also track attach.
- `0x4E`: command register; `EmuEc` writes it 9 times, more than any other.
  Reads `0x12` on the attached port, `0x00` on the idle port.
- `0x50..0x58`: parameter block (`EmuEc` writes 0x50,0x51,0x52,0x56,0x57,0x58).
- `0x59`: received Source_Capabilities, 4-byte little-endian PDOs, standard
  USB-PD fixed-supply encoding. Decoded from the live chip:

  | # | raw | decoded |
  |---|---|---|
  | 1 | 0x0A01912C | 5 V 3 A |
  | 2 | 0x0002D12C | 9 V 3 A |
  | 3 | 0x0003C1F4 | 12 V 5 A |
  | 4 | 0x0004B1B1 | 15 V 4.33 A |
  | 5 | 0x00064145 | 20 V 3.25 A |

  A 65 W adapter, decoded correctly, so PD messaging works and VBUS is present at
  5 V. The chip received the source's capabilities.

## Where the failure actually is

- Historical PD observation: default PDO 1 at 5 V, missing Linux higher-PDO selection after replug
- `EmuEc` log: `PDO is not selected yet by default`
- Current helper: guarded higher-PDO requests implemented
- Earlier claim of a required input above 17 V: unverified, not a measured hardware limit
- Non-PD 5 V input: separate limitation described above

Confirmed by writing the charger directly (i2c-12 0x09): ChargingVoltage `0x4358`
and ChargingCurrent `0x0400` both stuck for 8 s with the battery still discharging;
the charger is healthy and programmable, it simply has no input power.

The S2MM005 command encoding does not work here: writing
`0x03 0x03 <pdo>` then `0x03 0x02 0x11` to `REG_I2C_SLV_CMD` (0x0010) was accepted on
the bus but ignored, and register 0x0010 did not change.

## Next step

`EmuEc`'s sequence writes `0xFF`, then `0x09`, then `0x12` to register `0x4E`, each
followed by `0x140032848` (delay/notify). Not attempted: a blind `0xFF` to a PD
controller command register sits next to a `W33_PDIC_Set_Firmware_Download` string,
and a wrong guess there risks bricking the chip.

Get the evidence instead: `book4-charge-capture.service` captures full state ~30 s and
~90 s after boot into `~/book4-edge/charging-debug/state-working*.txt`. Diff that
against `state-wedged.txt`: the delta in `0x4E` and `0x50..0x58` between a working
(UEFI-negotiated) link and a wedged one gives the exact command to send, with no
guessing. Remove the unit when done:
`systemctl disable --now book4-charge-capture.service`.
