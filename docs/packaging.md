# Packaging and release

This page is for maintainers. The repository builds extension-module wheels with
meson-python and cibuildwheel, publishes documentation with GitHub Pages, and uses
PyPI Trusted Publishing rather than a long-lived API token.

## Verify a checkout

Create a virtual environment and install all development dependencies:

```console
python -m pip install --upgrade pip
python -m pip install '.[test,docs]' build twine
python tools/check_inventory.py
python tools/regen.py --check
python -m mkdocs build --strict
python tools/check_docs.py site
```

Because the unbuilt source package can shadow the installed extension module, run
the package checks with a working directory outside the checkout and pass the test
directory by absolute path:

```console
python -m pytest -q /absolute/path/to/accudist/tests
python -m pytest -q -m scipy_gap /absolute/path/to/accudist/tests
python -c "import accudist; print(accudist.__version__)"
```

Build and inspect both distribution formats:

```console
python -m build
python -m twine check dist/*
```

Test a built wheel in a clean environment before release. A wheel should import
without access to the repository checkout.

## Documentation publishing

The `docs` GitHub Actions workflow validates pull requests and deploys pushes to
the `main` branch. In the repository's GitHub **Settings → Pages**, select
**GitHub Actions** as the publishing source. The deployed site is
`https://hyunminkang.github.io/accudist/`.

If the default branch changes, update the branch filter in
`.github/workflows/docs.yml`, the edit links in `mkdocs.yml`, and branch-specific
repository URLs together.

## Prepare PyPI

On PyPI, create the `accudist` project or add a pending Trusted Publisher with:

- owner: `hyunminkang`;
- repository: `accudist`;
- workflow: `wheels.yml`;
- environment: `pypi`.

In GitHub **Settings → Environments**, create the matching `pypi` environment.
Environment reviewers and tag-protection rules are recommended for a production
release.

## Make a release

1. Choose an unused version and update every version source in the repository.
2. Update `CHANGELOG.md`, regenerate checked-in generated files, and run the full
   verification commands above.
3. Commit and push the release changes.
4. Create and push a `v*` tag for the release commit.
5. Watch the `wheels` workflow. It builds the source distribution and platform
   wheels, validates every artifact with Twine, then publishes from the protected
   `pypi` environment.
6. Open the PyPI project page and confirm the README, Python requirement, licence,
   and Documentation, Repository, Issues, and Changelog links.

PyPI does not allow replacing a file for an existing release. Correct a bad release
with a new version rather than attempting to reuse its version number.
