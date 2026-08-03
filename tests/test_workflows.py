from pathlib import Path

import yaml


def test_github_workflows_are_valid_yaml():
    root = Path(__file__).resolve().parents[1]
    workflows = tuple((root / ".github/workflows").glob("*.yml"))
    assert workflows
    for workflow in workflows:
        yaml.safe_load(workflow.read_text())
