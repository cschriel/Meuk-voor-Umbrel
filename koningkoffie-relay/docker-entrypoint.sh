#!/bin/sh
set -eu

if [ -d /app/default-data/drivers ]; then
  mkdir -p /app/data/drivers
  for driver in /app/default-data/drivers/*.json; do
    [ -e "$driver" ] || continue
    cp "$driver" "/app/data/drivers/$(basename "$driver")"
  done
fi

exec "$@"
