from ConfigParser import SafeConfigParser
from lxml import etree
from lxml.builder import E
from pika.adapters import twisted_connection
from twisted.application import service
from twisted.internet import defer, protocol, reactor, task
from twisted.internet.interfaces import IReactorCore
from twisted.python import log
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implements
import json
import pika


defaults = {
    'host': 'premium-backend01.zeit.de',
    'port': 5672,
    'virtual_host': '/',
    'url': 'https://crm-receiver.zeit.de/premium/kunden'
}
config_parser = SafeConfigParser(defaults)
config_parser.read(['/etc/zeit-premium-dwh/config.ini'])
agent = Agent(reactor)


class XmlProducer(object):
    implements(IBodyProducer)

    def __init__(self, order):
        self.body = etree.tostring(self.build(order))
        self.length = len(self.body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

    def build(self, order):
        interests = [
            E.interest(
                E.key('campaign_id'),
                E.value(order['campaign_id'])
            ),
            E.interest(
                E.key('state'),
                E.value(order['state'])
            ),
            E.interest(
                E.key('gift'),
                E.value(order['gift'])
            )
        ]
        if order.get('created'):
            interests.append(E.interest(
                E.key('created'),
                E.value(order['created'])
            ))
        if order.get('last_modified'):
            interests.append(E.interest(
                E.key('last_modified'),
                E.value(order['last_modified'])
            ))
        if order.get('agent_id'):
            interests.append(E.interest(
                E.key('agent_id'),
                E.value(order['agent_id'])
            ))
        if order.get('add_on'):
            interests.append(E.interest(
                E.key('add_on'),
                E.value(order['add_on'])
            ))
        if order.get('subscription_id'):
            interests.append(E.interest(
                E.key('subscription_id'),
                E.value(order['subscription_id'])
            ))

        users = E.users(
            E.user(
                E.id(order['customer_id']),
                E.email('premium-user'),
                E.firstname('default'),
                E.surname('default'),
                E.registration_date('default'),
                E.modified_date('default'),
                E.confirmed(**{'{http://www.w3.org/2001/XMLSchema-instance}nil': 'true'}),
                E.deleted(**{'{http://www.w3.org/2001/XMLSchema-instance}nil': 'true'}),
                E.accept_information(**{'{http://www.w3.org/2001/XMLSchema-instance}nil': 'true'}),
                E.additional(
                    E.street(),
                    E.street_number(),
                    E.zip_code(),
                    E.city(),
                    E.phone(),
                    E.country(),
                    E.birthday(),
                    E.gender(),
                    E.interests(
                        *interests
                    )
                )
            )
        )
        return users


def sleep(secs):
    d = defer.Deferred()
    reactor.callLater(secs, d.callback, None)
    return d


@defer.inlineCallbacks
def run(connection):

    channel = yield connection.channel()
    exchange = yield channel.exchange_declare(
        exchange='premium', type='topic', durable=True)
    queue = yield channel.queue_declare(
        queue='orders', auto_delete=False, exclusive=False, durable=True)

    yield channel.queue_bind(
        exchange='premium', queue='orders', routing_key='order.*')
    yield channel.basic_qos(prefetch_count=1)
    queue_object, consumer_tag = yield channel.basic_consume(
        queue='orders', no_ack=False)

    l = task.LoopingCall(read, queue_object)
    l.start(0.01)


@defer.inlineCallbacks
def read(queue_object):

    ch, method, properties, body = yield queue_object.get()

    if body:
        order = json.loads(body)
        url = '{}/{}'.format(
            config_parser.get('destination', 'url'),
            order['customer_id'])
        try:
            yield agent.request(
                'PUT',
                url,
                Headers({'content-type': ['text/xml']}),
                XmlProducer(order))
        except:
            log.err()
            yield sleep(3)
            yield ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            yield ch.basic_ack(delivery_tag=method.delivery_tag)


class PikaFactory(protocol.ClientFactory):

    def __init__(self, parameters):
        self.parameters = parameters

    def buildProtocol(self, addr):
        self.connection = twisted_connection.TwistedProtocolConnection(
            self.parameters)
        self.connection.ready.addCallback(run)
        return self.connection


class PikaService(service.Service):

    def startService(self):
        parameters = pika.ConnectionParameters(
            host=config_parser.get('broker', 'host'),
            port=config_parser.getint('broker', 'port'),
            virtual_host=config_parser.get('broker', 'virtual_host'))
        self.factory = PikaFactory(parameters)
        IReactorCore(reactor).connectTCP(
            parameters.host, parameters.port, self.factory)

    def stopService(self):
        return self.factory.connection.close()
