from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_meson_forces_the_visual_studio_environment_on_windows():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "--vsenv" in config["tool"]["meson-python"]["args"]["setup"]


def test_standalone_nmath_uses_msvc_safe_special_values():
    header = (ROOT / "vendor" / "nmath" / "src" / "nmath.h").read_text()
    expected = """#if defined(_MSC_VER)
# define ML_POSINF INFINITY
# define ML_NEGINF (-INFINITY)
# define ML_NAN NAN
#else"""
    assert expected in header


def test_free_threaded_wheels_use_the_focused_thread_safety_suite():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    overrides = config["tool"]["cibuildwheel"]["overrides"]
    free_threaded = next(item for item in overrides if item["select"] == "cp3??t-*")

    assert free_threaded["test-requires"] == ["pytest"]
    assert "test_free_threading.py" in free_threaded["test-command"]
    assert "test_thread_safety.py" in free_threaded["test-command"]


def test_generated_flag_ufuncs_use_a_platform_stable_integer_type():
    source = (ROOT / "accudist" / "_ufuncs.c").read_text()

    assert "npy_int64 lower_tail" in source
    assert "npy_int64 log_arg" in source
    assert "NPY_INT64, NPY_INT64" in source
    assert "long lower_tail" not in source
    assert "long log_arg" not in source


def test_package_metadata_exposes_documentation_and_discovery_links():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    project = config["project"]

    assert project["authors"]
    assert {"probability", "statistics", "numpy", "rmath"} <= set(
        project["keywords"]
    )
    assert "Topic :: Scientific/Engineering :: Mathematics" in project["classifiers"]
    assert project["urls"] == {
        "Documentation": "https://hyunminkang.github.io/accudist/",
        "Repository": "https://github.com/hyunminkang/accudist",
        "Issues": "https://github.com/hyunminkang/accudist/issues",
        "Changelog": "https://github.com/hyunminkang/accudist/blob/HEAD/CHANGELOG.md",
    }
    assert any(
        dependency.startswith("mkdocs-material")
        for dependency in project["optional-dependencies"]["docs"]
    )


def test_readme_links_work_when_rendered_on_pypi():
    readme = (ROOT / "README.md").read_text()

    assert "](benchmarks/" not in readme
    assert "https://hyunminkang.github.io/accudist/" in readme
