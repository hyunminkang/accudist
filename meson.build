project(
  'accudist',
  'c',
  version : '0.1.0',
  default_options : ['c_std=c11', 'optimization=2', 'b_lto=false'],
)

py = import('python').find_installation(pure : false)
py_dep = py.dependency()
cc = meson.get_compiler('c')
np_inc = run_command(
  py,
  '-c',
  'import numpy; print(numpy.get_include())',
  check : true,
).stdout().strip()
# NumPy may be installed in an in-tree virtual environment. Meson deliberately
# rejects absolute source-tree paths passed to include_directories(), so pass the
# compiler's native include argument through the dependency instead.
np_include_flag = cc.get_argument_syntax() == 'msvc' ? '/I' : '-I'
np_dep = declare_dependency(compile_args : [np_include_flag + np_inc])
m_dep = cc.find_library('m', required : false)

source_output = run_command(
  py,
  files('tools/list_nmath_sources.py'),
  check : true,
).stdout().strip()
nmath_sources = []
foreach source_name : source_output.split('\n')
  nmath_sources += files(source_name)
endforeach

subdir('accudist')

install_data('LICENSE', install_dir : get_option('datadir') / 'licenses' / 'accudist')
install_data('NOTICE', install_dir : get_option('datadir') / 'licenses' / 'accudist')
install_data('vendor/nmath/COPYING', install_dir : get_option('datadir') / 'licenses' / 'accudist')
