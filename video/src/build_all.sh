#!/bin/bash
# Usage: build_all.sh <piper_dir> <build_dir> <geo_dir> <out.mp4> [jobs]
set -e
SRC=$(cd "$(dirname "$0")" && pwd)
PIPER=$1; export BUILD_DIR=$2; export GEO_DIR=$3; OUT=$4; JOBS=${5:-4}
[ -f "$BUILD_DIR/timeline.json" ] || python3 "$SRC/build_voice.py" "$PIPER" "$BUILD_DIR"
python3 "$SRC/audio.py"
ffmpeg -y -v error -i "$BUILD_DIR/mix_raw.wav" -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -ac 2 -c:a aac -b:a 192k "$BUILD_DIR/mix.m4a"
TOTAL=$(python3 -c "import json;print(int(json.load(open('$BUILD_DIR/timeline.json'))['duration']*25))")
STEP=$(( (TOTAL + JOBS - 1) / JOBS ))
rm -f "$BUILD_DIR"/seg_*.mp4 "$BUILD_DIR/segs.txt"
for i in $(seq 0 $((JOBS-1))); do
  S=$((i*STEP)); E=$(( (i+1)*STEP < TOTAL ? (i+1)*STEP : TOTAL ))
  (cd "$SRC" && python3 render.py $S $E "$BUILD_DIR/seg_$i.mp4" > "$BUILD_DIR/seg_$i.log" 2>&1) &
  echo "file '$BUILD_DIR/seg_$i.mp4'" >> "$BUILD_DIR/segs.txt"
done
wait
ffmpeg -y -v error -f concat -safe 0 -i "$BUILD_DIR/segs.txt" -i "$BUILD_DIR/mix.m4a" -map 0:v -map 1:a -c:v copy -c:a copy -shortest -movflags +faststart "$OUT"
echo "done: $OUT"
