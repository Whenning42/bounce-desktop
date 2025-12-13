0.2.2 - 2025-12-13

- Add an optional 'visible' argument to `Desktop.create()`.

0.2.1 - 2025-10-27

FIXED:
- Fixed runtime error in Desktop.get_desktop_env() from missing nanobind type
  cast include.

0.2.0 - 2025-10-27

Update the API so that callers, not bounce_desktop, are responsible for subprocess
launch and cleanup.

0.1.6 - 2025-10-07

- Document multi-instance limitations and add asserts preventing
  accidental multi-instance use.

0.1.5 - 2025-10-03

- Fix incorrect string nesting in build_extension.py

0.1.4 - 2025-10-03

- Add missing MIT license

0.1.3 - 2025-10-03

- Add python 3.10 support

0.1.2 - 2025-10-03

- Reorganized source code layout
- Added more information to the readme

0.1.0 - 2025-10-03

Initial release of bounce_desktop
