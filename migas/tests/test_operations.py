from datetime import datetime as dt
from datetime import timedelta
from datetime import timezone as tz

from looseversion import LooseVersion
import pytest

import migas
from migas.operations import (
    add_breadcrumb,
    check_project,
    get_usage,
)

from .utils import run_server_tests

# skip all tests in module if server is not available
pytestmark = pytest.mark.skipif(not run_server_tests, reason="Local server not found")

test_project = 'nipreps/migas-py'
today = dt.now(tz.utc)
future = (today + timedelta(days=2)).strftime('%Y-%m-%d')
today = today.strftime('%Y-%m-%d')


TEST_ROOT = "http://localhost:8080/"
TEST_ENDPOINT = f"{TEST_ROOT}graphql"



@pytest.fixture(autouse=True, scope='module')
def setup_migas():
    """Ensure migas is configured to communicate with the staging app."""
    migas.setup(endpoint=TEST_ENDPOINT)

    assert migas.config.Config._is_setup
    return migas.config.Config._is_setup



def test_migas_add_get():
    res = add_breadcrumb(test_project, migas.__version__)
    # ensure kwargs can be submitted
    res = add_breadcrumb(test_project, migas.__version__, wait=True, language='cpython', platform='win32')
    assert res['success'] is True
    # this breadcrumb is not valid, so won't be tracked
    res = add_breadcrumb(test_project, migas.__version__, wait=True, status='wtf')
    assert res['success'] is False

    # 2 crumbs should be present on the server, both from the same user
    res = get_usage(test_project, start=today)
    assert res['success'] is True
    all_usage = res['hits']
    assert all_usage == 2

    res = get_usage(test_project, start=today, unique=True)
    assert res['success'] is True
    assert all_usage > res['hits'] > 0

    res = get_usage(test_project, start=future)
    assert res['success'] is True
    assert res['hits'] == 0

    # checking a project that is not tracked will lead to a failure
    res = get_usage('my/madeup-project', start=today)
    assert res['success'] is False
    assert res['hits'] == 0


def test_check_project():
    res = check_project(test_project, migas.__version__)
    assert res['success'] is True
    assert res['latest']
    v = LooseVersion(migas.__version__)
    latest = LooseVersion(res['latest'])
    assert v >= latest
    assert res['flagged'] is False
    assert res['message'] == ''
