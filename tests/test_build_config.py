from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_meson_forces_the_visual_studio_environment_on_windows():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "--vsenv" in config["tool"]["meson-python"]["args"]["setup"]
