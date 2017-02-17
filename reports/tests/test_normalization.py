import pytest
import warnings
import mock
from reports.helpers import value_currency_normalize
from reports.tests.utils import MockCurrencyResponce

def test_value_normalization():
    with pytest.raises(ValueError):
        warnings.warn(
        'ValueError',
        value_currency_normalize(
        '1',
        u'EUR',
        '2015-10-11')            
        )
    with mock.patch('reports.helpers.requests.get', new=lambda *args, **kwargs: MockCurrencyResponce()):
        value_valid = 10
        currencies = [u'USD', u'RUR', u'EUR']
        for curr in currencies:
            value, rate = value_currency_normalize(
                value_valid, curr, '2015-10-11'
            )
            assert 20 == value
