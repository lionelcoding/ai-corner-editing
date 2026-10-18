#!/bin/bash
# Fabrique les médias du projet exemple avec ffmpeg (rien de binaire n'est versionné) :
#   out/demo-v1.mp4, out/demo-v2.mp4  rendus 9:16 de 9 s (mire + bip), un par tour de relecture
#   frames/*.png                      maquettes des panneaux du storyboard
set -e
cd "$(dirname "$0")"
mkdir -p out frames
render() {  # render <fichier> <motif de mire>
  ffmpeg -loglevel error -y \
    -f lavfi -i "$2=size=1080x1920:rate=30:duration=9" \
    -f lavfi -i "sine=frequency=440:beep_factor=4:duration=9" \
    -c:v libx264 -preset veryfast -crf 32 -pix_fmt yuv420p -c:a aac -b:a 96k -shortest "$1"
}
[ -f out/demo-v1.mp4 ] || render out/demo-v1.mp4 testsrc2
[ -f out/demo-v2.mp4 ] || render out/demo-v2.mp4 smptehdbars
for p in hook:1 demo:4.5 cta:7.5; do
  name=${p%%:*}; t=${p##*:}
  [ -f "frames/$name.png" ] || ffmpeg -loglevel error -y -ss "$t" -i out/demo-v1.mp4 -frames:v 1 -vf scale=540:-2 "frames/$name.png"
done
echo "médias prêts dans $(pwd)/out et $(pwd)/frames"
