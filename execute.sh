#!/bin/bash
mkdir -p "$HOME/docker-app/$2"
xhost local:root
docker run \
  --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -v $XDG_RUNTIME_DIR/pulse:/run/pulse:ro \
  -v "$HOME/docker-app/$2":/home/docker \
  --device /dev/dri \
  -v /etc/localtime:/etc/localtime:ro \
  $1 \
  $(id -u)
