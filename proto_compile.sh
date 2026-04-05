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

# generate the classes and stubs using the schema
MYPY_FLAGS=()
if command -v protoc-gen-mypy &>/dev/null; then
    MYPY_FLAGS=(--mypy_out=./generated/ --mypy_grpc_out=./generated/)
fi

uv run python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=./generated/ \
    --grpc_python_out=./generated/ \
    "${MYPY_FLAGS[@]}" \
    proto/*.proto

sed -i 's/^import schema_pb2/from . import schema_pb2/' ./generated/schema_pb2_grpc.py
if [ -f ./generated/schema_pb2_grpc.pyi ]; then
    sed -i 's/^import schema_pb2/from . import schema_pb2/' ./generated/schema_pb2_grpc.pyi
fi

# Verify the generated scripts
uv run python -c "from generated import schema_pb2, schema_pb2_grpc"
