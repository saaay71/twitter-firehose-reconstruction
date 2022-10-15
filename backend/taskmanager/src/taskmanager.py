import json
import math
import os
import pika
import time
import logging
import requests
import json
import redis
from datetime import datetime

from snowflake.snowflake import getSnowflake
from error_handling import RETRY_ON_AMQP_ERROR

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -20s %(funcName) '
              '-15s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


REDIS_HOST = os.environ.get("REDIS_HOST")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.environ.get("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD")
RABBITMQ_TTL = int(os.environ.get("RABBITMQ_TTL"))


RABBITMQ_URL = "amqp://" + RABBITMQ_USERNAME + ":" + RABBITMQ_PASSWORD + "@" + RABBITMQ_HOST + ":" + RABBITMQ_PORT
QUEUE_NAME = os.environ.get("RABBITMQ_QUEUE_NAME")
EXCHANGE_NAME = os.environ.get("RABBITMQ_EXCHANGE_NAME")

CREDENTIALSMANAGER_HOST = os.environ.get("CREDENTIALSMANAGER_HOST")
CREDENTIALSMANAGER_PORT = os.environ.get("CREDENTIALSMANAGER_PORT")

WORK_TYPE = os.environ.get("WORK_TYPE")
CHUNK_SIZE = 10 * 60  # min * s
r = redis.Redis(host=REDIS_HOST)


def get_twitter_timestamp():
    """ Return milliseconds since twitter epoch start """
    return int(datetime.now().timestamp()*1000)-1288834974657


def get_current_chunk_id():
    return unix_to_chunk_id(time.time())


def chunk_id_to_unix(chunk_id):
    # returns a unix ts in s
    return int(chunk_id * CHUNK_SIZE)


def unix_to_chunk_id(unix_ts):
    # returns a chunk_id
    return unix_ts // CHUNK_SIZE


# This works great for the first 200ish Server (~2000 Token)
# After that we usually get < 10 Tweets per Datacenter-Server-Sequence combination and a statistical approach would be better suited
def get_active_server_ids_in(chunk_id):
    """ Return all servers (datacenterId, serverId, sequenceId, count) that were active in this time range. """
    result = None
    i = 0
    while result == None:
        result = r.get(chunk_id_to_unix(chunk_id - i))
        i += 1
        if i > 100:
            return[]
    servers = sorted(json.loads(result)['server'], key=lambda s: -s[3])
    return servers

def publish_all_work_items(time_range, percentage, channel):
    """ Publish work items for the given percentage in the given time range. """
    raise NotImplementedError

def get_num_tokens():
    resp = requests.get("http://" + CREDENTIALSMANAGER_HOST + ":" + CREDENTIALSMANAGER_PORT + "/num_tokens")
    if resp.status_code != 200:
        return None
    response_dict = json.loads(resp.text)
    return response_dict.get("num_tokens", None)


def determine_possible_rate():
    """ Return the maximum requests per second we can cover given our credentials. """
    credential_count = None
    while credential_count == None:
        credential_count = get_num_tokens()
    # Remove 1 for sampled stream and one so we have a chance to catch
    # up to the queue should we face any downtimes
    credential_count -= 2

    ######        TODO:             ######
    ###### ATTENTION DEBUG CODE     ######
    credential_count = 2
    ###### REMOVE AGAIN AFTER DEBUG ######
    ######     its for de säfty     ######

    safety_margin = 0.05
    LOGGER.info("Got " + str(credential_count) + " tokens, will set rate of " +
                str(credential_count * (1-safety_margin)))
    # 900 Requests per 15 Min = 1 Request per second. Every user can make one request per second
    return credential_count * (1-safety_margin)


def stream_work_items(rate, channel):
    """ Add live work items to queue while respecting our max rate. """
    window_length = 5
    while True:
        timestamp = (get_twitter_timestamp()//5000)*5000
        # lookup the most active datacenter, server, sequence combination in the previous 10 Minutes
        servers = get_active_server_ids_in(get_current_chunk_id()-1)
        for _ in range(0, window_length):  # for every second
            i = 0
            for _ in range(0, math.floor(rate)):  # for every token we have
                server = servers[i//10]
                ts = timestamp - window_length * 1000  # always ask for 5 seconds in the past
                send_100_Tweets(ts + ((i % 10) * 100), server, channel)
                i += 1
        # sleep as long as the starttimestamp + 5 seconds is larger then the current time
        while timestamp + window_length*1000 >= get_twitter_timestamp():
            time.sleep(0.1)


def send_100_Tweets(timestamp, server, channel):
    id_array = []
    ts = timestamp
    for _ in range(0, 100):  # add 100 Tweets to id_array
        id_array.append(
            str(getSnowflake(ts, server[0], server[1], server[2])))
        ts += 1
    publish_to_rabbitmq(id_array, channel)  # send id_array to rabbit


def publish_to_rabbitmq(tweet_urls, channel):
    """ Publish a single work item to the queue. """
    job_dict = {}
    job_dict['urls'] = tweet_urls
    channel.basic_publish(exchange=EXCHANGE_NAME,
                          routing_key=QUEUE_NAME, body=json.dumps(job_dict))
    LOGGER.info("Published message to queue.")


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
                          'x-message-ttl': RABBITMQ_TTL,
                          'x-dead-letter-exchange': 'dlx',
                          'x-dead-letter-routing-key': 'dl'+QUEUE_NAME
                          })

    channel.queue_bind(
        queue=QUEUE_NAME, exchange=EXCHANGE_NAME, routing_key=QUEUE_NAME)
    return connection, channel


def main():
    # time.sleep(45)
    connection, channel = setup_rabbitmq()
    LOGGER.info("Rabbit successfully set up.")

    if WORK_TYPE == "ARCHIVE":
        print("Entering ARCHIVE mode", flush=True)
        #publish_all_work_items(time_range, percentage, channel)
    elif WORK_TYPE == "LIVE":
        print("Entering LIVE mode", flush=True)
        rate = determine_possible_rate()
        stream_work_items(rate, channel)
    else:
        print("ERROR: unrecognised work type")

    time.sleep(1)
    connection.close()


if __name__ == "__main__":
    main()
