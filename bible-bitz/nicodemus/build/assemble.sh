#!/bin/bash
# Join rendered scenes, add the soundtrack, encode for vertical social video.
set -e
cd "$(dirname "$0")/.."
ls render/scenes/*.mp4 | sort | sed "s|^|file '$PWD/|; s|$|'|" > render/list.txt
ffmpeg -v error -y -f concat -safe 0 -i render/list.txt -i audio/soundtrack.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 8M -maxrate 10M -bufsize 16M -pix_fmt yuv420p \
  -r 16 -c:a aac -b:a 192k -movflags +faststart -shortest render/bible_bitz_nicodemus_9x16.mp4
ffprobe -v error -show_entries format=duration,size -of default=nw=1 render/bible_bitz_nicodemus_9x16.mp4
