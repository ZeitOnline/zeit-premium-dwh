from configparser import ConfigParser
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
from zope.interface import implementer
import json
import pika


config_parser = ConfigParser()
config_parser.read_dict({
    'broker': {
        'host': 'premium-backend.zeit.de',
        'port': 5672,
        'virtual_host': '/'
    },
    'destination': {
        'url': 'https://crm-receiver.zeit.de/premium/bestellungen'
    }
})
config_parser.read(['/etc/zeit-premium-dwh/config.ini'])
agent = Agent(reactor)


@implementer(IBodyProducer)
class XmlProducer(object):

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
        nil = {'{http://www.w3.org/2001/XMLSchema-instance}nil': 'true'}
        interests = [
            E.interest(
                E.key('campaign_id'),
                E.value(str(order['campaign_id']))
            ),
            E.interest(
                E.key('state'),
                E.value(order['state'])
            ),
            E.interest(
                E.key('gift'),
                E.value(str(order['gift']))
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
                E.value(str(order['add_on']))
            ))
        if order.get('subscription_id'):
            interests.append(E.interest(
                E.key('dpv_order_id'),
                E.value(str(order['subscription_id']))
            ))
        if order.get('customer_id'):
            interests.append(E.interest(
                E.key('sso_id'),
                E.value(str(order['customer_id']))
            ))
        if order.get('icode'):
            interests.append(E.interest(
                E.key('icode'),
                E.value(str(order['icode']))
            ))
        if order.get('external_id'):
            interests.append(E.interest(
                E.key('external_id'),
                E.value(str(order['external_id']))
            ))

        users = E.users(
            E.user(
                E.id(str(order['id'])),
                E.email('premium-user'),
                E.firstname('default'),
                E.surname('default'),
                E.registration_date(**nil),
                E.modified_date(**nil),
                E.confirmed(**nil),
                E.deleted(**nil),
                E.accept_information(**nil),
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


class HttpError(Exception):

    def __init__(self, url, response):
        super(HttpError, self).__init__(
            'Received status {} from {}'.format(response.code, url))
        self.response = response


def sleep(secs):
    d = defer.Deferred()
    reactor.callLater(secs, d.callback, None)
    return d


@defer.inlineCallbacks
def run(connection):

    channel = yield connection.channel()
    exchange = yield channel.exchange_declare(
        exchange='premium', exchange_type='topic', durable=True)
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
        order = json.loads(body.decode('utf-8'))
        url = '{}/{}'.format(
            config_parser.get('destination', 'url'),
            order['id'])
        try:
            response = yield agent.request(
                b'PUT',
                url.encode('utf-8'),
                Headers({'content-type': ['text/xml']}),
                XmlProducer(order))
            if response.code >= 400:
                raise HttpError(url, response)
        except TypeError:
            log.err()
            yield ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except HttpError as e:
            log.err()
            requeue = True if e.response.code >= 500 else False
            yield ch.basic_nack(
                delivery_tag=method.delivery_tag, requeue=requeue)
        except:
            log.err()
            yield sleep(60)
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
        factory = PikaFactory(parameters)
        IReactorCore(reactor).connectTCP(
            parameters.host, parameters.port, factory)
