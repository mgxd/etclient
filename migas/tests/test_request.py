import pytest

from migas.request import _request

GET_URL = 'https://httpbin.org/get'
GET_COMPRESSED_URL = 'https://httpbingo.org/get'
POST_URL = 'https://httpbin.org/post'

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.mark.parametrize(
    'method,url,query', [
        ('POST', POST_URL, 'mydata'),
        ('GET', GET_URL, None),
        ('GET',GET_COMPRESSED_URL, None)
    ]
)
def test_request_get(method, url, query):
    status, res = _request(url, query=query, method=method)
    assert status == 200
    assert res


def test_timeout(monkeypatch):
    status, res = _request(GET_URL, timeout=0.00001, method="GET")
    assert status == 408
    assert res['errors']

    monkeypatch.setenv('MIGAS_TIMEOUT', '0.000001')
    status, res = _request(GET_URL, method="GET")
    assert status == 408
    assert res['errors']

    monkeypatch.delenv('MIGAS_TIMEOUT')
    status, res = _request(GET_URL, method="GET")
    assert status == 200
    assert res
