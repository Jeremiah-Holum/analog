#!/usr/bin/env bash
# Turn a rendered frame sequence into a worn VHS tape: usage ./vhs.sh <frames_dir> <out.mp4>
set -e
IN=$1; OUT=$2; FONT=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf
ffmpeg -loglevel error -y -framerate 24 -i "$IN/f_%04d.png" \
  -f lavfi -i "anoisesrc=color=pink:amplitude=0.04:d=5" \
  -f lavfi -i "sine=frequency=60:d=5" \
  -filter_complex "
  [0:v]scale=640:480:flags=bilinear,
  eq=brightness=-0.18:contrast=1.35:saturation=0.45:gamma=0.85,
  colorbalance=gm=0.08:bm=-0.05,
  gblur=sigma=1.1,
  rgbashift=rh=4:bh=-4,
  noise=alls=22:allf=t,
  vignette=PI/3.5,
  rgbashift=rh=18:gv=6:bh=-18:enable='between(n,66,73)',
  drawbox=y=ih*0.68:w=iw:h=10:color=white@0.5:t=fill:enable='between(n,66,73)',
  drawtext=fontfile=$FONT:text='PLAY ▶':x=40:y=36:fontsize=26:fontcolor=white:shadowx=2:shadowy=2,
  drawtext=fontfile=$FONT:text='SP':x=w-90:y=36:fontsize=26:fontcolor=white:shadowx=2:shadowy=2,
  drawtext=fontfile=$FONT:text='OCT. 14 1994':x=40:y=h-70:fontsize=24:fontcolor=white:shadowx=2:shadowy=2,
  drawtext=fontfile=$FONT:text='3\:17\:%{eif\:n/24\:d\:2} AM':x=w-230:y=h-70:fontsize=24:fontcolor=white:shadowx=2:shadowy=2[v];
  [1:a][2:a]amix=inputs=2,volume=2[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -crf 20 -c:a aac -shortest "$OUT"
