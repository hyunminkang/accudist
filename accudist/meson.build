gen = custom_target(
  'accudist-codegen',
  input : '../docs/functions.toml',
  output : ['_ufuncs.c', '_api.py', '_generated.pyi', 'rmath.py', 'test_manifest.py'],
  command : [py, files('../tools/regen.py'), '@INPUT@', '@OUTDIR@'],
  build_by_default : true,
)

shim_inc = include_directories('../src')
nmath_inc = include_directories('../vendor/nmath/include', '../vendor/nmath/src')

c_args = ['-DMATHLIB_STANDALONE']
if cc.get_id() == 'msvc'
  c_args += ['/fp:precise']
else
  c_args += ['-O2', '-ffp-contract=off']
endif

py.extension_module(
  '_ufuncs',
  [gen[0], '../src/accudist_shim.c'] + nmath_sources,
  include_directories : [nmath_inc, shim_inc],
  dependencies : [py_dep, np_dep, m_dep],
  c_args : c_args,
  install : true,
  subdir : 'accudist',
)

py.install_sources(
  [
    '__init__.py', '_errstate.py', '_dispatch.py', '_rng.py', '_bespoke.py',
    '_api.py', '_generated.pyi', 'rmath.py', 'py.typed',
  ],
  subdir : 'accudist',
)
