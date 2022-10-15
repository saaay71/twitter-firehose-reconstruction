from FilteredStreamFollower import FilteredStreamFollower
import os
import pika
import logging
from QueuePublisher import QueuePublisher
from error_handling import RETRY_ON_AMQP_ERROR

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN, format=LOG_FORMAT)

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.environ.get("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD")
RABBITMQ_TTL = int(os.environ.get("RABBITMQ_TTL"))

RABBITMQ_URL = "amqp://" + RABBITMQ_USERNAME + ":" + RABBITMQ_PASSWORD + "@" + RABBITMQ_HOST + ":" + RABBITMQ_PORT
QUEUE_NAME = os.environ.get("RABBITMQ_QUEUE_NAME")
EXCHANGE_NAME = os.environ.get("RABBITMQ_EXCHANGE_NAME")

@RETRY_ON_AMQP_ERROR
def setup_rabbitmq():
    """ Setup a connection to the queue and make sure our channel is declared. """
    parameters = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    
    channel.exchange_declare(exchange='dlx', exchange_type='direct')
    channel.queue_declare(queue='dl'+QUEUE_NAME)
    channel.queue_bind(exchange='dlx', queue='dl'+QUEUE_NAME)

    channel.queue_declare(queue=QUEUE_NAME, arguments={
                          'x-message-ttl' : RABBITMQ_TTL,
                          'x-dead-letter-exchange' : 'dlx',
                          'x-dead-letter-routing-key' : 'dl'+QUEUE_NAME
                      })

    channel.queue_bind(
        queue=QUEUE_NAME, exchange=EXCHANGE_NAME, routing_key=QUEUE_NAME)
    return connection, channel


def main():
    timeout = 0
    abort = False
    while not abort:
        connection = None
        channel = None

        try:
            connection, channel = setup_rabbitmq()
        except KeyboardInterrupt:
            channel.close()
            connection.close()
            abort = True
            break
        # except: pika.exceptions.ConnectionClosedByBroker:
        except pika.exceptions.ConnectionClosed:
            LOGGER.warn('Connection closed. Recovering')
            continue

        tweetid_publisher = QueuePublisher(channel, EXCHANGE_NAME, QUEUE_NAME)

        try:
            follower = FilteredStreamFollower(tweetid_publisher)
            follower.connect_to_endpoint(follower.CREATE_URL)
        except Exception as err:
            print("Error, will retry: ", err)
        timeout += 1

if __name__ == "__main__":
    main()
