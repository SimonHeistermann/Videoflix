#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 \"commit message\""
  exit 1
fi

COMMIT_MSG="$1"

git pull
git add .
git commit -m "$COMMIT_MSG"
git push