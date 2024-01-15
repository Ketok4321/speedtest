project('speedtest',
          version: run_command('git', 'describe', '--tags', check: false).stdout().strip(),
    meson_version: '>= 0.62.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')
python = import('python')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())

if get_option('development')
  app_id = 'xyz.ketok.Speedtest.Devel'
else
  app_id = 'xyz.ketok.Speedtest'
endif

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

conf.set('APP_ID', app_id)
conf.set('DEVEL', get_option('development'))

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
