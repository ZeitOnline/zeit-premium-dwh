import json
import os
import pytest

from lxml import etree
from zeit_premium_dwh.consumer import XmlProducer


@pytest.fixture(scope='session')
def schema():
    xsd = os.path.join(os.path.dirname(__file__), 'sso-user.xsd')
    return etree.XMLSchema(etree.parse(xsd))


@pytest.mark.parametrize('order,expected', [
    (
        {
            'id': '523456',
            'campaign_id': '800144',
            'customer_id': '2234578',
            'subscription_id': None,
            'state': 'pending',
            'created': '2016-08-05 15:24:00',
            'last_modified': None,
            'agent_id': None,
            'comment': None,
            'addon': '1008009',
            'gift': 'false'
        },
        True
    ),
    (
        {
            'id': '523456',
            'campaign_id': '800144',
            'customer_id': '2234578',
            'subscription_id': None,
            'state': 'completed',
            'created': '2016-08-05 15:24:00',
            'last_modified': '2016-08-06 08:18:00',
            'agent_id': None,
            'comment': None,
            'addon': '1008009',
            'gift': 'false',
        },
        True
    ),
    (
        {
            'id': '523456',
            'campaign_id': '800144',
            'customer_id': '2234578',
            'subscription_id': '2871000000',
            'state': 'confirmed',
            'created': '2016-08-05 15:24:00',
            'last_modified': '2016-08-06 08:23:00',
            'agent_id': None,
            'comment': None,
            'addon': '1008009',
            'gift': 'false',
        },
        True
    ),
])
def test_build(schema, order, expected):
    producer = XmlProducer(order)
    assert schema.validate(producer.build(order)) == expected
