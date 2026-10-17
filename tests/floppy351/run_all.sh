#!/bin/bash
# Run from anywhere; needs tools/.local/mame/mame_thomson/thomson (run tools/prepare-mame.sh first).
cd "$(dirname "$0")" || exit 1
python3 stage_roms.py || exit 1
python3 write_whole_disk.py && python3 read_kill_full.py &&
python3 ../../tools/fdtool.py get /tmp/pc128-full.fd F01.BIN /tmp/f01.bin --tracks 80 --side 0 &&
for t in backup_single_drive dski_dsko_track79 copy_verify_writeprot compare_640_351_copy_open compare_640_351_verify_seq compare_640_351_copy_16k disk_change; do
    echo "== $t"; python3 $t.py
done
