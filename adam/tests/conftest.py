import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--skip-notebooks", action="store_true", default=False, help="skip notebook tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "notebook: mark test as invoking a Jupyter notebook")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--skip-notebooks"):
        # --skip-notebooks given in cli: do not skip notebook tests
        return
    skip_notebooks = pytest.mark.skip(reason="--skip-notebooks option given")
    for item in items:
        if "notebook" in item.keywords:
            item.add_marker(skip_notebooks)
