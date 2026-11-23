#!/usr/bin/env bash
# Copy the minimum needed to run mutation testing in an isolated dir so the real repo is never mutated.
set -e
W=${MUT_WORK:-/c/mut_work}; rm -rf "$W"; mkdir -p "$W/data" "$W/tests"
cp -r src "$W/src"; rm -rf "$W/src/ephios/static" "$W/src/ephios/locale"
cp tests/*.py "$W/tests/"; cp -r tests/team "$W/tests/team"; cp pyproject.toml .env "$W/"
cp -r data/private "$W/data/private" 2>/dev/null || true
cp mutation/cosmic-ray.toml "$W/"
echo "mutation workdir ready: $W"
