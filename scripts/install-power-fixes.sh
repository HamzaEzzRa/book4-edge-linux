#!/bin/bash
# Install the charger and sleep hooks with a rollback copy.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
D=${DESTDIR:-}
[[ -z "$D" || "$D" = /* ]] || { echo 'DESTDIR must be absolute' >&2; exit 1; }
if [ -n "$D" ]; then
    D=$(realpath -m "$D")
    [ "$D" != / ] || D=""
fi
[ -n "$D" ] || [ "$EUID" -eq 0 ] || { echo 'Run with sudo' >&2; exit 1; }
files=(/usr/local/bin/book4-pd-charge
       /usr/lib/systemd/system-sleep/book4-backlight
       /usr/lib/systemd/system-sleep/book4-battery)

restore(){
    local file
    for file in "${files[@]}"; do
        if [ -e "$backup$file" ] || [ -L "$backup$file" ]; then
            cp -a --remove-destination "$backup$file" "$D$file" || return 1
        else
            rm -f "$D$file" || return 1
        fi
    done
    if [ -z "$D" ] && [ -f "$backup/active" ]; then
        systemctl start book4-pd-charge || return 1
    fi
}

case "${1:-}" in
    --rollback)
        [ "$#" -eq 2 ] || exit 1
        backup=$2
        [[ "${backup%/*}" = "$D/var/backups" &&
           "${backup##*/}" =~ ^book4-power\.[a-zA-Z0-9]+$ ]] || exit 1
        [ -d "$backup" ] && [ ! -L "$backup" ] || exit 1
        [ "$(stat -c '%u %a' "$backup")" = "$EUID 700" ] || exit 1
        [ -f "$backup/complete" ] || exit 1
        [ -n "$D" ] || systemctl stop book4-pd-charge
        restore
        echo 'Previous power files restored'
        exit 0
        ;;
    '') [ "$#" -eq 0 ] || exit 1 ;;
    *) echo "Usage: $0 [--rollback BACKUP]" >&2; exit 1 ;;
esac

bash -n "$ROOT/userspace/charging/book4-pd-charge"
sh -n "$ROOT/userspace/suspend/book4-backlight"
mkdir -p "$D/var/backups"
backup=$(mktemp -d "$D/var/backups/book4-power.XXXXXX")
for file in "${files[@]}"; do
    if [ -e "$D$file" ] || [ -L "$D$file" ]; then
        mkdir -p "$(dirname "$backup$file")"
        cp -a "$D$file" "$backup$file"
    fi
done
if [ -z "$D" ] && systemctl is-active --quiet book4-pd-charge; then
    touch "$backup/active"
fi
touch "$backup/complete"
printf 'Backup: %s\n' "$backup"
trap 'trap - ERR; echo "Install failed. Restoring previous files" >&2; restore; exit 1' ERR
[ -n "$D" ] || systemctl stop book4-pd-charge
install -D -m755 "$ROOT/userspace/charging/book4-pd-charge" "$D${files[0]}"
install -D -m755 "$ROOT/userspace/suspend/book4-backlight" "$D${files[1]}"
rm -f "$D${files[2]}"
if [ -z "$D" ] && [ -f "$backup/active" ]; then
    systemctl start book4-pd-charge
    systemctl is-active --quiet book4-pd-charge
fi
trap - ERR
echo 'Power fixes installed'
printf 'Rollback: sudo bash %q --rollback %q\n' "$0" "$backup"
