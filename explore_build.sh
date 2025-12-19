#!/bin/bash

# Prototype simple and incremental python package builds.

set -eux
shopt -s failglob

BUILD_DIR=packaging/dist
PACKAGE_OUT=dist
VENV=packaging/test_venv


# for py in python3.11 python3.12 python3.13; do
for py in python3.12; do
    # Activate python environment
    rm -rf -- ${VENV} && $py -m venv ${VENV}
    source ${VENV}/bin/activate
    pip install build
    pip install poetry-core meson ninja

    # Build the extension module
    make build

    # Build the package
    rm -rf -- ${BUILD_DIR} && mkdir -p -- ${BUILD_DIR}
    echo "Files under build: $(ls build)"
    $py -m build -v --wheel --no-isolation --outdir ${BUILD_DIR}

    # Test the package
    pip install ${BUILD_DIR}/*.whl
    python src/bounce_desktop/bounce_desk_test.py

    deactivate
done



