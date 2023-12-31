pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
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

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

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

backends_sources = [
  'backends/librespeed.py',
]

install_data(speedtest_sources, install_dir: moduledir)
install_data(backends_sources, install_dir: join_paths(moduledir, 'backends'))
