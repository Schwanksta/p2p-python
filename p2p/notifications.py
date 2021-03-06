"""
P2P Notification Listener
-------------------------
Connect to Tribune's RabbitMQ server to receive notifications when
content items or collections get added, updated or deleted.

You need to be on Tribune's network to connect to the message server.

Use the `start_listening` function to make stuff happen. You could use
the `Listener` class if you wanted, but you shouldn't need to.

Some backstory to this adventure
--------------------------------

So, kombu doesn't seem to be designed to share
any server resources with other platforms. Kombu attempts to create and
destroy any exchanges or queues that you define. That is appropiate for
queues, but not for exchanges. Unfortunately, kombu will not manage only
queues, you have to let kombu manage everything, or nothing.

Since we need to tap into an
existing exchange, we need to manage the setup and teardown of exchanges
and queues manually. This was not easy to figure out. It might be better
to use a low-level AMQP library like py-librabbitmq, but I'm afraid I
might have to re-implement boilerplate types of things that kombu provides:
connection pooling, thread management, etc..

Create/update/delete notifications are published via AMQP server.

The payload is a JSON hash. The 'action' key is "U" for create/update,
and "D" for deletes.
"""
from kombu import Exchange, Queue, Connection
from kombu.mixins import ConsumerMixin
from kombu.utils.debug import setup_logging
import json

import pprint
pp = pprint.PrettyPrinter(indent=4)


class Listener(ConsumerMixin):

    def __init__(self, connection, name, callback, product_code=None):
        """
        Setup connection, setup queues, and bind them to the exchange
        """
        self.connection = connection
        self.callback = callback
        self.product_affiliate_code = product_code
        self.exchange = Exchange('updated_content')

        if self.product_affiliate_code:
            ci_key = 'update.content_item.%s.#' % self.product_affiliate_code
            c_key = 'update.collection.%s.#' % self.product_affiliate_code
        else:
            ci_key = 'update.content_item.#'
            c_key = 'update.collection.#'

        self.queues = [
            Queue(name + '_content_items',
                  exchange=self.exchange,
                  routing_key=ci_key,
                  channel=self.connection,
                  auto_delete=True),
            Queue(name + '_collections',
                  exchange=self.exchange,
                  routing_key=c_key,
                  channel=self.connection,
                  auto_delete=True)
        ]

        for queue in self.queues:
            # We declare and bind the queues manually. If we let kombu
            # autodeclare things later, it tries to redeclare the exchange
            # which just utterly fails.
            queue.queue_declare()
            queue.queue_bind()

    def get_consumers(self, Consumer, channel):
        """
        Create the Consumer objects that kombu wants
        """
        return [Consumer(queues=self.queues,
                         callbacks=[self.process_task, ],
                         auto_declare=False), ]

    def process_task(self, body, message):
        """
        Here we actually do interesting things
        """
        data = json.loads(body)
        self.callback(data)

        message.ack()


def start_listening(name, callback, amqp_url=None, product_code=None):
    """
    Connect to the messaging server and listen for notifications. Takes
    the URL of the server to connect to and a function to call for every
    notification. The callback function should take one argument, a
    dictionary containing an action, either a content item id and slug or
    a collection id or slug.

    You must name every listener. Two listeners with the same name can't
    be listening at the same time. Or something, I think.

    This function will run indefinitely.
    """
    #setup_logging(loglevel='INFO')

    if amqp_url is None:
        import os

        # Try getting settings from environment variables
        if 'P2P_AMQP_URL' in os.environ:
            amqp_url = os.environ['P2P_AMQP_URL']
        else:
            # Try getting settings from Django
            try:
                from django.conf import settings
                amqp_url = settings.P2P_AMQP_URL
            except ImportError, e:
                raise P2PNotificationError(
                    "No connection settings available. Please put settings in"
                    " your environment variables or your Django config")

    with Connection(amqp_url) as conn:
        try:
            Listener(conn, name, callback, product_code).run()
        except KeyboardInterrupt:
            conn.release()
        except:
            conn.release()
            raise


class P2PNotificationError(Exception):
    pass
