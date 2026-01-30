import httpx
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--green-agent-url",
        default="http://localhost:9009",
        help="Green Agent URL (default: http://localhost:9009)",
    )
    parser.addoption(
        "--purple-agent-url",
        default="http://localhost:9019",
        help="Purple Agent URL (default: http://localhost:9019)",
    )


@pytest.fixture(scope="session")
def green_agent(request):
    """Green Agent URL fixture. Agent must be running before tests start."""
    url = request.config.getoption("--green-agent-url")

    try:
        response = httpx.get(f"{url}/.well-known/agent-card.json", timeout=2)
        if response.status_code != 200:
            pytest.exit(f"Green Agent at {url} returned status {response.status_code}", returncode=1)
    except Exception as e:
        pytest.exit(f"Could not connect to Green Agent at {url}: {e}", returncode=1)

    return url


@pytest.fixture(scope="session")
def purple_agent(request):
    """Purple Agent URL fixture. Agent must be running before tests start."""
    url = request.config.getoption("--purple-agent-url")

    try:
        response = httpx.get(f"{url}/.well-known/agent-card.json", timeout=2)
        if response.status_code != 200:
            pytest.exit(f"Purple Agent at {url} returned status {response.status_code}", returncode=1)
    except Exception as e:
        pytest.exit(f"Could not connect to Purple Agent at {url}: {e}", returncode=1)

    return url