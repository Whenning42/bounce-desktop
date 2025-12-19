# Install Python package files to bounce_desktop/ under the install prefix
install_data('__init__.py', install_dir: 'bounce_desktop')
install_data('bounce_desk_test.py', install_dir: 'bounce_desktop')

# Use 'python' (not 'python3') so Meson finds the venv's Python when
# running inside 'poetry run'. Make it required to avoid silently
# falling back to a system interpreter.
python3 = import('python').find_installation('python', required: true)
nanobind_dep = dependency('nanobind')

py_sources = [
  '../bindings/desktop_ext.cpp',
  '../desktop/desktop.cpp',
  '../../third_party/status/exceptions.h',
]

python3.extension_module('_core',
  py_sources,
  include_directories: ['../../', '..'],
  dependencies: [nanobind_dep, gvnc_dep],
  link_with: bouncedesk_lib,
  cpp_args: [],
  override_options: [
    'cpp_rtti=true',
    'cpp_eh=default',
    'warning_level=2',
  ],
  install_rpath: '$ORIGIN',
  install: true,
  install_dir: 'bounce_desktop',
)

test('bounce_desk_test',
  python3,
  args: [meson.project_source_root() / 'src/bounce_desktop/bounce_desk_test.py'],
  env: {'PYTHONPATH': meson.project_build_root()},
  workdir : meson.project_source_root()
)
