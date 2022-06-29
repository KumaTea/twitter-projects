#!/usr/bin/env bash

set -ex

git submodule sync
git submodule update --init --recursive --remote

cd twitter-user-data    && git checkout main && git pull && cd ..
cd tweet-likes-predict  && git checkout main && git pull && cd ..
cd twitter-progress-bar && git checkout main && git pull && cd ..
cd top-friends          && git checkout main && git pull && cd ..
cd friends-map          && git checkout main && git pull && cd ..
