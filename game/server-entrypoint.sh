#!/bin/sh

export DISPLAY=:1
Xvfb $DISPLAY &

fluxbox  &
x11vnc -forever -usepw -shared -rfbport 5900 -display $DISPLAY &

exec "$@"
