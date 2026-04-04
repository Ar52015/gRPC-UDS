#!/usr/bin/env bash

# Fail Loudly if any command fails in the script or in a pipe(defensivel included) in the script
# e - exit immediately if anything fails
# u - treat unset vars as errors instead of empty strings
# o - to supply pipefail
set -euo pipefail

# generate folder if they don't already exist
mkdir -p ./generated

# add __init__.py file to generated folder
touch ./generated/__init__.py

# generate the classes, stubs, and mypy type stubs using the schema
uv run python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=./generated/ \
    --grpc_python_out=./generated/ \
    --mypy_out=./generated/ \
    --mypy_grpc_out=./generated/ \
    proto/*.proto

sed -i 's/^import schema_pb2/from . import schema_pb2/' ./generated/schema_pb2_grpc.py
sed -i 's/^import schema_pb2/from . import schema_pb2/' ./generated/schema_pb2_grpc.pyi

# Verify the generated scripts
uv run python -c "from generated import schema_pb2, schema_pb2_grpc"
