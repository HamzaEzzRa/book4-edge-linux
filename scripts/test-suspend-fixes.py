#!/usr/bin/env python3
"""Offline regression checks. Run: python3 scripts/test-suspend-fixes.py"""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "userspace/charging/book4-pd-charge").read_text()
# Load the real definitions and loop, omitting live bus discovery. Override every
# hardware entry point before running the loop, with two simulated polls.
constants = source[source.index("MAX_CURRENT_MA="):source.index("# Find the controllers")]
functions = source[source.index("pd_read(){"):source.index("declare -A tx_count")]
loop = source[source.index("declare -A tx_count"):]


def charge(temp="0x0bb8", current="0x1150", voltage="0x4358", fail=False,
           confirm="0x0000", ac="1", resume=False):
    with tempfile.TemporaryDirectory() as d:
        mocks = r'''
PD0=2; PD1=4; CHG=1; polls=0; writes=0
ac(){ if [ "$polls" = 0 ]; then echo 1; else echo "$AC"; fi; }
pd_read(){ echo 0x00; }
active_pd_bus(){ return 1; }
i2ctransfer(){ echo 'UNEXPECTED PD ACCESS' >&2; exit 99; }
i2cget(){
  case "$4" in
    0x08) result=$TEMP;;
    0x15)
      if [ "$RESUME" = 1 ] && [ "$polls" -gt 0 ]; then result=0x4358
      else result=$VOLTAGE; fi;;
    0x14)
      if [ "$RESUME" = 1 ] && [ "$polls" -gt 0 ]; then result=0x1150
      elif [ -e "$STATE/read" ]; then result=$CONFIRM
      else result=$CURRENT; touch "$STATE/read"; fi;;
    *) return 99;;
  esac
  [ "$result" != ERROR ] || return 1
  echo "$result"
}
i2cset(){
  writes=$((writes + 1))
  echo "WRITE $4 $5"
  [ "$FAIL" != 1 ] || [ "$writes" != 2 ]
}
sleep(){ polls=$((polls + 1)); [ "$polls" -lt 2 ] || exit 0; }
'''
        result = subprocess.run(
            ["bash", "-uc", constants + functions + mocks + loop],
            env={"PATH": "/usr/bin:/bin", "STATE": d, "TEMP": temp,
                 "CURRENT": current, "CONFIRM": confirm, "VOLTAGE": voltage,
                 "FAIL": str(int(fail)), "AC": ac, "RESUME": str(int(resume))},
            text=True, capture_output=True, timeout=5, check=True)
        assert not result.stderr, result.stderr
        lines = result.stdout.splitlines()
        writes = [line for line in lines if line.startswith("WRITE ")]
        assert all(line.split()[1] in ("0x14", "0x15") for line in writes)
        return writes, result.stdout


# Cap valid requests. Do not repeatedly write unchanged requests.
writes, _ = charge(confirm="0x1150")
assert writes == ["WRITE 0x15 0x4358", "WRITE 0x14 0x05dc"], writes
# Recover from transient zero. Stop on confirmed zero or failed reads.
assert charge(current="0x0000", confirm="0x1150")[0] == writes
for value in ("0x0000", "0xffff", "ERROR", "garbage"):
    w, _ = charge(current=value, confirm=value)
    assert w == ["WRITE 0x14 0x0000"] * 2, w
w, log = charge(current="0x0000", confirm="0x0000", voltage="0x0000")
assert w == ["WRITE 0x14 0x0000"] * 2
assert log.count("battery requests zero charge current") == 1
assert "invalid" not in log and "unavailable" not in log
w, _ = charge(current="0x0000", confirm="0x0000", voltage="0x0000", resume=True)
assert w == ["WRITE 0x14 0x0000", "WRITE 0x15 0x4358", "WRITE 0x14 0x05dc"]
# Invalid temperature/voltage cannot leave the previous charge request running.
for value in ("0x0000", "0xffff", "ERROR", "garbage", "0x0e94", "0x0c6e"):
    assert charge(temp=value)[0] == ["WRITE 0x14 0x0000"] * 2
for value in ("0x0000", "0xffff", "ERROR", "0x5000"):
    assert charge(voltage=value)[0] == ["WRITE 0x14 0x0000"] * 2
# Do not cache failed writes as success. Stop, then retry.
w, log = charge(fail=True, confirm="0x1150")
assert w == writes + ["WRITE 0x14 0x0000"] + writes, w
assert log.count("charger write accepted") == 1
assert charge(ac="0")[0] == writes

def packet(header, words):
    data = header.to_bytes(2, "little") + bytes(2)
    data += b"".join(w.to_bytes(4, "little") for w in words)
    return " ".join(f"0x{b:02x}" for b in data)


def adapter(port="4", rails=((5000, 3000), (9000, 3000), (15000, 3000), (20000, 3000)),
            pos=4, operating=3000, maximum=None, bad="", program=False, observed=False):
    maximum = operating if maximum is None else maximum
    request = packet(0x1482, [(pos << 28) | (3 << 24) | (operating // 10 << 10) | maximum // 10])
    caps = packet(0x1a1 | len(rails) << 12,
                  [(v // 50 << 10) | a // 10 for v, a in rails] + [0] * (5 - len(rails)))
    if observed:
        request = "0x82 0x14 0x00 0x00 0x2c 0xb1 0x04 0x43"
        caps = ("0xa1 0x41 0x00 0x00 0x2c 0x91 0x01 0x08 "
                "0x2c 0xd1 0x02 0x00 0x2c 0xb1 0x04 0x00 "
                "0x2c 0x41 0x06 0x00 0x00 0x00 0x00 0x00")
    if bad == "short":
        caps = caps.rsplit(" ", 1)[0]
    if bad == "malformed":
        caps = "garbage " + caps.split(" ", 1)[1]
    if bad == "extended":
        caps = caps.replace("0x41", "0xc1", 1)
    with tempfile.TemporaryDirectory() as d:
        mocks = r'''
PD0=2; PD1=4; CHG=1
rd(){
  [ "$BAD" != read ] || return 1
  if [ "$PORT" = both ] || [ "$1" = "$PORT" ]; then
    if [ "$2" = 0x0e ]; then echo 0x07; else echo 0x0a; fi
  else echo 0x00; fi
}
rd8(){
  if [ "$BAD" = changed ] && [ -e "$STATE/request" ]; then echo 0x00
  else touch "$STATE/request"; echo "$REQUEST"; fi
}
i2ctransfer(){
  [ "$2" = "$PORT" ] || return 99
  echo "$CAPS"
}
i2cget(){
  [ "$BAD" != charger_read ] || return 1
  if [ -e "$STATE/$4" ]; then cat "$STATE/$4"; else echo 0x01c4; fi
}
i2cset(){
  echo "WRITE $4 $5"
  [ "$BAD" != write ] || return 1
  [ "$BAD" = readback ] || echo "$5" > "$STATE/$4"
}
'''
        result = subprocess.run(["bash", "-uc", constants + functions + mocks +
                                 ("check_input" if program == "check" else
                                  "set_adapter_limit" if program else "adapter_limit_target")],
                                env={"PATH": "/usr/bin:/bin", "PORT": port,
                                     "REQUEST": request, "CAPS": caps, "BAD": bad,
                                     "STATE": d}, text=True, capture_output=True, timeout=5)
        assert not result.stderr, result.stderr
        return result.returncode, result.stdout.strip()


# Captured hardware bytes retain the existing 3000 register target.
assert adapter(observed=True) == (0, "3000")
# Either supplying port retains the measured setup's 3000 target.
for port in ("2", "4"):
    assert adapter(port=port) == (0, "3000")
# A stronger 15 V PDO must not override a selected 20 V / 2 A PDO.
assert adapter(rails=((5000, 3000), (9000, 3000), (15000, 3000), (20000, 2000)),
               operating=2000) == (0, "2000")
assert adapter(pos=1, operating=1000) == (0, "1000")
assert adapter(operating=1990) == (0, "1988")
assert adapter(pos=0)[0] != 0
assert adapter(pos=5)[0] != 0
assert adapter(operating=3010)[0] != 0
assert adapter(operating=2000, maximum=1000)[0] != 0
for port in ("both", "none"):
    assert adapter(port=port)[0] != 0
for bad in ("short", "malformed", "extended", "read", "changed"):
    assert adapter(bad=bad)[0] != 0
rc, log = adapter(program=True)
assert rc == 0 and "WRITE 0x3b 0x0bb8" in log and "WRITE 0x3f 0x0bb8" in log
for bad in ("charger_read", "write", "readback"):
    rc, log = adapter(program=True, bad=bad)
    assert rc != 0 and "verified" not in log
rc, log = adapter(program="check", observed=True)
assert rc == 0 and "Last-Request limit target: 3000" in log and "WRITE" not in log

def ports(left, right, ac_error=False, fail_attach=False, tx_fail=False, stage_fail=False):
    with tempfile.TemporaryDirectory() as directory:
        state = Path(directory)
        for bus, role in (("2", left), ("4", right)):
            (state / f"{bus}.role").write_text(role)
            (state / f"{bus}.sent").write_text(packet(0x1082, [0x13019064]))
        mocks = r'''
PD0=2; PD1=4; CHG=1
now_s(){ echo $((100 + poll * 31)); }
sleep(){ :; }
ac(){
  [ "$AC_ERROR" != 1 ] || return 1
  if grep -qx sink "$STATE/2.role" "$STATE/4.role"; then echo 1; else echo 0; fi
}
i2ctransfer(){
  local bus=$2 role hi=$4 lo=$5 value=${6:-} k
  role=$(cat "$STATE/$bus.role")
  if [ "$3" = w3@0x33 ]; then
    echo "$bus $lo $value" >> "$STATE/pd-writes"
    case "$lo" in
      0x4e) echo sink > "$STATE/$bus.role";;
      0x50)
        [ "$TX_FAIL" != 1 ] || return 1
        for ((k=128; k<136; k++)); do cat "$STATE/$bus.$k"; done |
          xargs > "$STATE/$bus.sent";;
      *)
        [ "$STAGE_FAIL/$lo" != 1/0x83 ] || return 1
        echo "$value" > "$STATE/$bus.$((lo))";;
    esac
    return
  fi
  case "$hi/$lo" in
    0x00/0x0e)
      if [ "$FAIL_ATTACH" = 1 ]; then return 1
      elif [ "$TX_FAIL" = 1 ] && [ $((poll % 2)) -eq 0 ]; then return 1
      elif [ "$role" = none ]; then echo 0x00; else echo 0x07; fi;;
    0x00/0x1c)
      case "$role" in sink) echo 0x0a;; storage) echo 0x09;; *) echo 0x08;; esac;;
    0x00/0x50) echo 0x00;;
    0x06/0xa0) cat "$STATE/$bus.sent";;
    0x09/0x00) echo "$CAPS";;
    0x00/0x80)
      for ((k=128; k<136; k++)); do cat "$STATE/$bus.$k"; done | xargs;;
    *) return 99;;
  esac
}
i2cget(){
  if [ "$3" = 0x0b ]; then
    case "$4" in 0x08) echo 0x0bb8;; 0x14) echo 0x1150;; 0x15) echo 0x4358;; esac
  elif [ -e "$STATE/charger.$4" ]; then cat "$STATE/charger.$4"
  else echo 0x01c4; fi
}
i2cset(){ echo "$5" > "$STATE/charger.$4"; }
'''
        result = subprocess.run(
            ["bash", "-uc", constants + functions + mocks + loop.replace("while true; do", "for poll in 1 2 3 4 5; do", 1)],
            env={"PATH": "/usr/bin:/bin", "STATE": directory,
                 "CAPS": packet(0x31a1, [0x0801912c, 0x0004b12c, 0x0006412c, 0, 0]),
                 "AC_ERROR": str(int(ac_error)), "FAIL_ATTACH": str(int(fail_attach)),
                 "TX_FAIL": str(int(tx_fail)), "STAGE_FAIL": str(int(stage_fail))},
            text=True, capture_output=True, timeout=10, check=True)
        assert not result.stderr, result.stderr
        writes_file = state / "pd-writes"
        writes = writes_file.read_text().splitlines() if writes_file.exists() else []
        limit_file = state / "charger.0x3f"
        limit = limit_file.read_text().strip() if limit_file.exists() else None
        return writes, limit


# Storage advertises stale Source_Capabilities in this mock. Provider role wins.
for left, right, expected_bus in (("sink", "storage", "2"), ("storage", "sink", "4"),
                                  ("open", "storage", "2"), ("storage", "open", "4")):
    w, limit = ports(left, right)
    assert w and all(line.startswith(expected_bus + " ") for line in w), w
    assert sum(" 0x50 " in line for line in w) == 1, w
    assert limit == "0x0bb8", limit
# Choose only one initially open source. Preserve an existing input path.
w, limit = ports("open", "open")
assert w and all(line.startswith("2 ") for line in w) and limit == "0x0bb8"
w, limit = ports("sink", "open")
assert w and all(line.startswith("2 ") for line in w) and limit == "0x0bb8"
assert ports("sink", "sink") == ([], None)
assert ports("storage", "storage") == ([], None)
assert ports("open", "storage", ac_error=True) == ([], None)
assert ports("sink", "storage", fail_attach=True) == ([], None)
w, _ = ports("sink", "storage", tx_fail=True)
assert sum(" 0x50 " in line for line in w) == 2, w
w, _ = ports("sink", "storage", stage_fail=True)
assert not any(" 0x50 " in line for line in w), w

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    brightness, state = d / "brightness", d / "saved"
    hook = (root / "userspace/suspend/book4-backlight").read_text()
    hook = hook.replace("/sys/class/backlight/backlight/brightness", str(brightness))
    hook = hook.replace("/run/book4-backlight", str(state)).replace("sleep 2", ":")

    def run(phase):
        subprocess.run(["sh", "-c", hook, "hook", phase, "suspend"],
                       check=True, capture_output=True)

    brightness.write_text("0\n")
    run("pre")
    brightness.write_text("80\n")
    run("post")
    assert brightness.read_text() == "0\n" and not state.exists()
    run("post")  # No stale state to replay.
    state.write_text("bad\n")
    run("post")
    assert brightness.read_text() == "0\n"
    brightness.unlink()
    state.write_text("80\n")
    run("pre")  # Failed save must discard old state.
    assert not state.exists()

assert not (root / "userspace/suspend/book4-battery").exists()
assert subprocess.run(["git", "check-ignore", "userspace/camera/libcamera/new-file"],
                      cwd=root, capture_output=True).returncode == 1
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    journal = d / "journalctl"
    journal.write_text("#!/bin/sh\nprintf 'test journal line\\n'\n")
    journal.chmod(0o755)
    capture = root / "scripts/capture-sleep-journal.py"
    output = d / "capture.log"
    args = ["python3", str(capture), str(output)]
    env = {"PATH": f"{d}:/usr/bin:/bin"}
    subprocess.run(args, env=env, check=True, timeout=5)
    assert output.read_text().endswith("test journal line\n")
    assert output.stat().st_mode & 0o777 == 0o600
    saved = output.read_bytes()
    assert subprocess.run(args, env=env, capture_output=True).returncode != 0
    assert output.read_bytes() == saved

installer = root / "scripts/install-power-fixes.sh"
for fail in (False, True):
    with tempfile.TemporaryDirectory() as directory:
        dest = Path(directory)
        originals = {
            "usr/local/bin/book4-pd-charge": b"old charger\n",
            "usr/lib/systemd/system-sleep/book4-battery": b"old battery hook\n",
        }
        for relative, data in originals.items():
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        bins = dest / "bin"
        bins.mkdir()
        (bins / "systemctl").write_text("#!/bin/sh\nexit 99\n")
        (bins / "systemctl").chmod(0o755)
        if fail:
            (bins / "install").write_text(
                '#!/bin/sh\n[ ! -e "$DESTDIR/installed-once" ] || exit 1\n'
                'touch "$DESTDIR/installed-once"\nexec /usr/bin/install "$@"\n')
            (bins / "install").chmod(0o755)
        env = {"PATH": f"{bins}:/usr/bin:/bin", "DESTDIR": directory}
        result = subprocess.run(["bash", str(installer)], env=env, text=True,
                                capture_output=True, timeout=10)
        backup = next((dest / "var/backups").glob("book4-power.*"))
        backlight = dest / "usr/lib/systemd/system-sleep/book4-backlight"
        if fail:
            assert result.returncode != 0, result.stdout
        else:
            assert result.returncode == 0, result.stderr
            assert (dest / "usr/local/bin/book4-pd-charge").read_bytes() == source.encode()
            assert backlight.read_bytes() == (root / "userspace/suspend/book4-backlight").read_bytes()
            assert not (dest / "usr/lib/systemd/system-sleep/book4-battery").exists()
            subprocess.run(["bash", str(installer), "--rollback", str(backup)],
                           env=env, check=True, capture_output=True, timeout=10)
        for relative, data in originals.items():
            assert (dest / relative).read_bytes() == data
        assert not backlight.exists()

print("suspend-fixes offline checks passed")
