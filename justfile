test_venv := ".test-wheel-venv"

test_wayland_desktop:
    PYTHONPATH=src python -m unittest src.bounce_desktop.wayland_desktop_test

wheel:
    rm -rf dist/*
    uv build --wheel

# Install the built wheel into a temp venv and run the tests.
test_wheel: wheel
    if [ -d {{test_venv}} ]; then trash {{test_venv}}; fi
    uv venv {{test_venv}}
    uv pip install --python {{test_venv}}/bin/python dist/*.whl
    {{test_venv}}/bin/python -m unittest src.bounce_desktop.wayland_desktop_test -v

# Upload package to PyPI
upload_package: test_wheel
    uv run --only-group dev twine upload python/dist/*.whl
