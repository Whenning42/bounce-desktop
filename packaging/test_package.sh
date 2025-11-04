# Runs the bounce_desktop package tests for the built wheel saved under package/dist/*.
# Throws an error there are no wheels or more than one wheels under packaging/dist/*.

set -euo pipefail

PROJECT_ROOT=$(pwd)
TEST_DIST=packaging/dist

# Exit if the script wasn't run from the project's root directory.
FILE="packaging/test_package.sh"
if [[ ! -e "$FILE" ]]; then
  echo "test_package.sh should be run from bounce_desktop's project root directory."
  exit 1
fi

# Exit if ${TEST_DIST} contains zero or multiple wheels.
num_wheels=$(ls -1A "${TEST_DIST}" | grep ".whl" | wc -l || true)
if [ "${num_wheels}" -ne 1 ]; then
  echo "test_package.sh expects there to be exactly one wheel saved under"
  echo "packaging/dist/, but it found ${num_wheels} wheels."
  exit 1
fi

# Set up the test venv.
rm -rf packaging/test_venv
(cd packaging; python -m venv test_venv)
source packaging/test_venv/bin/activate

# Install the wheel into the test venv.
pip install packaging/dist/*.whl

# Run tests under /tmp to prevent importing local files.
(cd /tmp && python ${PROJECT_ROOT}/bounce_desktop/bounce_desk_test.py)

echo "Package tests passed!"


