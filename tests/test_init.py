import datetime as dt
import json
from dataclasses import dataclass
from enum import Enum
from unittest.mock import MagicMock, patch

from speid import CJSONEncoder, configure_environment


@patch('speid.Hosts.add')
@patch('speid.Hosts.write', return_value=None)
def test_edit_hosts(_, mock_hosts_add: MagicMock):
    with patch('speid.config.EDIT_HOSTS', 'true'):
        configure_environment()
        args = mock_hosts_add.call_args[0]
        host_entry = args[0][0]
        assert host_entry.entry_type == 'ipv4'
        assert host_entry.address == '1.0.0.1'
        assert host_entry.names == ['test.com']


def test_json_encoder():
    class EnumTest(Enum):
        s, p, e, i, d = range(5)

    @dataclass
    class TestClass:
        uno: str

        def to_dict(self):
            return dict(uno=self.uno, dos='dos')

    now = dt.datetime.utcnow()
    test_class = TestClass(uno='uno')

    to_encode = dict(enum=EnumTest.s, now=now, test_class=test_class)

    encoded = json.dumps(to_encode, cls=CJSONEncoder)
    decoded = json.loads(encoded)

    assert decoded['enum'] == 's'
    assert decoded['now'] == now.isoformat() + 'Z'
    assert decoded['test_class']['uno'] == 'uno'
    assert decoded['test_class']['dos'] == 'dos'
