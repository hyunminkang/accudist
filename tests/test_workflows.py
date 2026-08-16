from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_github_workflows_are_valid_yaml():
    workflows = tuple((ROOT / ".github/workflows").glob("*.yml"))
    assert workflows
    for workflow in workflows:
        yaml.safe_load(workflow.read_text())


def test_installed_package_tests_run_outside_the_checkout():
    workflow = yaml.safe_load((ROOT / ".github/workflows/test.yml").read_text())
    steps = workflow["jobs"]["test"]["steps"]
    pytest_step = next(step for step in steps if "pytest" in step.get("run", ""))

    assert pytest_step["working-directory"] == "${{ runner.temp }}"
    assert "${{ github.workspace }}/tests" in pytest_step["run"]


def test_free_threaded_ci_runs_the_focused_thread_safety_suite():
    workflow = yaml.safe_load((ROOT / ".github/workflows/test.yml").read_text())

    standard_versions = workflow["jobs"]["test"]["strategy"]["matrix"]["python"]
    assert all(not version.endswith("t") for version in standard_versions)

    job = workflow["jobs"]["free-threaded"]
    assert job["strategy"]["matrix"]["python"] == ["3.13t", "3.14t"]
    install_step = next(step for step in job["steps"] if "pip install" in step.get("run", ""))
    assert install_step["run"] == "python -m pip install . pytest"
    pytest_step = next(
        step for step in job["steps"] if "python -m pytest" in step.get("run", "")
    )
    assert "test_free_threading.py" in pytest_step["run"]
    assert "test_thread_safety.py" in pytest_step["run"]


def test_reference_build_imports_accudist_before_rtools_changes_path():
    workflow = yaml.safe_load((ROOT / ".github/workflows/reference.yml").read_text())
    steps = workflow["jobs"]["generate"]["steps"]

    install_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("run") == "python -m pip install ."
    )
    import_index = next(
        index
        for index, step in enumerate(steps)
        if 'import accudist' in step.get("run", "")
    )
    setup_r_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("uses", "").startswith("r-lib/actions/setup-r@")
    )
    rng_step = next(
        step for step in steps if "gen_rng_reference.py" in step.get("run", "")
    )

    assert install_index < import_index < setup_r_index
    assert steps[import_index]["working-directory"] == "${{ runner.temp }}"
    assert "${{ github.workspace }}/tools/gen_rng_reference.py" in rng_step["run"]
    assert rng_step["working-directory"] == "${{ runner.temp }}"
