#!/usr/bin/env bash

# Fail Loudly if any command fails in the script or in a pipe(defensivel included) in the script
# e - exit immediately if anything fails
# u - treat unset vars as errors instead of empty strings
# o - to supply pipefail
set -euo pipefail

# generate folders if they don't already exist
mkdir -p ./generated
mkdir -p ./generated/classes
mkdir -p ./generated/stubs

# add __init__.py files to generated folder
touch ./generated/__init__.py
touch ./generated/classes/__init__.py
touch ./generated/stubs/__init__.py

# generate the classes and stubs using the schema
uv run python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=./generated/classes \
    --grpc_python_out=./generated/stubs \
    proto/*.proto
