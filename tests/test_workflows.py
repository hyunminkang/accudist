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
