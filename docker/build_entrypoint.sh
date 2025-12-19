#!/bin/bash

set -eux

BUILD_DIR=packaging/dist
VENV=build_venv

for py in python3.10 python3.11 python3.12 python3.13 python3.14; do
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
    # TODO: Figure out package tests. It'd be nice to test at build time
    # but my default container setup doesn't support weston's graphics
    # stack.
    # python src/bounce_desktop/bounce_desk_test.py

    deactivate

    cp ${BUILD_DIR}/* /dist_out
    chown -R ${MY_UID}:${MY_GID} /dist_out
done
