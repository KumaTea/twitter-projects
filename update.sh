#!/usr/bin/env bash

set -ex

git submodule sync
git submodule update --init --recursive --remote
