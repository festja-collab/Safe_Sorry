#!/bin/bash
# Re-renders every reel + carousel, then re-mixes the licensed music. Silent masters go to static/reels/_silent/.
set -e
cd /app/backend
F=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
M=/app/backend/music
python scripts_make_reel.py safe-sorry-launch-reel safe-sorry-coming-soon safe-sorry-award-reel safe-sorry-story-coming-soon safe-sorry-story-launch
python reel_insure.py
python reel_myth.py
python reel_myths2.py
python reel_variants.py
python carousel_myths.py
cd static/reels
F2=$F
dur() { $F2 -i "$1" 2>&1 | grep -o "Duration: [0-9:.]*" | awk -F'[: ]' '{print $3*3600+$4*60+$5}'; }
# The launch track is ~25s, so join two copies with a 2s crossfade to cover the longer reels
[ -f $M/launch-long.mp3 ] || $F -y -loglevel error -i $M/launch.mp3 -i $M/launch.mp3 -filter_complex "[0:a][1:a]acrossfade=d=2[a]" -map "[a]" $M/launch-long.mp3
mix() {  # name track
  mv -f "$1.mp4" "_silent/$1.mp4"
  D=$(dur "_silent/$1.mp4"); FO=$(python -c "print(round($D-3,2))")
  $F -y -loglevel error -i "_silent/$1.mp4" -i "$M/$2.mp3" -filter_complex \
    "[1:a]atrim=0:$D,asetpts=PTS-STARTPTS,volume=0.8,afade=t=in:d=0.6,afade=t=out:st=$FO:d=3,apad,atrim=0:$D[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -ar 44100 -movflags +faststart -t "$D" "$1.mp4"
  echo "mixed $1 ($D s)"
}
mix safe-sorry-launch-reel launch-long
mix safe-sorry-coming-soon launch-long
mix safe-sorry-insure-reel insure
mix safe-sorry-myth-reel myth
mix safe-sorry-myth-young-reel myth
mix safe-sorry-myth-state-reel myth
mix safe-sorry-award-reel award
echo ALL DONE
