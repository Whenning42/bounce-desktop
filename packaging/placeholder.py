# This is an empty script that we pass as our poetry build script in pyproject.toml.
# This ensures Poetry tags our built wheels as platform ones, not pure-python ones.
# Our package is a platform wheel since it includes the `Desktop` extension module.
#
# i.e. our built wheels will get tagged as:
#   "bounce_desktop-x.y.z-cp311-cp311-manylinux..."
#
# instead of the incorrect:
#   "bounce_desktop-x.y.z-py3-none-any..."
