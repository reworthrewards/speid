from speid.models.helpers import base62_encode


def test_base_62_encode():
    assert base62_encode(0) == '0'
