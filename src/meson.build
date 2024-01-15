moduledir = join_paths(pkgdatadir, 'speedtest')
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'ui/window.blp',
    'ui/gauge.blp',
    'ui/preferences.blp',
    'ui/views/start.blp',
    'ui/views/test.blp',
    'ui/views/offline.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('speedtest',
  'speedtest.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

configure_file(
  input: 'speedtest.in',
  output: 'speedtest',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

speedtest_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'gauge.py',
  'fetch_worker.py',
  'test_worker.py',
  'garbage.py',
  'util.py',
]

speedtest_sources += configure_file(
  input: 'conf.py.in',
  output: 'conf.py',
  configuration: conf
)

backends_sources = [
  'backends/librespeed.py',
]

install_data(speedtest_sources, install_dir: moduledir)
install_data(backends_sources, install_dir: join_paths(moduledir, 'backends'))
