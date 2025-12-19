set -e

source .build_venv/bin/activate
trash build
make package
deactivate
source packaging/test_venv/bin/activate
pip install packaging/dist/bounce_desktop-0.2.2-cp311-cp311-manylinux_2_42_x86_64.whl --force-reinstall
python -i bounce_desktop/integration_test.py
