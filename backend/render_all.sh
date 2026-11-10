#!/bin/bash
# Re-renders every reel + carousel, then re-mixes the licensed music. Silent masters go to static/reels/_silent/.
set -e
cd /app/backend
F=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
M=/app/backend/music
[ "$SKIP_MAIN" = 1 ] || python scripts_make_reel.py safe-sorry-launch-reel safe-sorry-coming-soon safe-sorry-award-reel safe-sorry-story-coming-soon safe-sorry-story-launch
python reel_insure.py
python reel_myth.py
python reel_myths2.py
python reel_variants.py
python carousel_myths.py
cd static/reels
mix() {  # name track start_fade_out total
  mv -f "$1.mp4" "_silent/$1.mp4"
  $F -y -loglevel error -i "_silent/$1.mp4" -i "$M/$2.mp3" -filter_complex \
    "[1:a]atrim=0:$4,asetpts=PTS-STARTPTS,volume=0.8,afade=t=in:d=0.6,afade=t=out:st=$3:d=2.5,apad,atrim=0:$4[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -ar 44100 -movflags +faststart -t "$4" "$1.mp4"
  echo "mixed $1"
}
mix safe-sorry-launch-reel launch 22.3 27
mix safe-sorry-coming-soon launch 22.3 27
mix safe-sorry-insure-reel insure 22.5 25
mix safe-sorry-myth-reel myth 24.5 27
mix safe-sorry-myth-young-reel myth 24.5 27
mix safe-sorry-myth-state-reel myth 24.5 27
mix safe-sorry-award-reel award 18.9 21.4
echo ALL DONE
