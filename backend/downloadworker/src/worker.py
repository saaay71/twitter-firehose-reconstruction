from DBHelper import DBHelper
from Tweet import Tweet
from Tweet import Downloadstatus
from Downloadsource import Downloadsource
from error_handling import RETRY_ON_AMQP_ERROR
import functools
import json
import time
import logging
import os
import pika
import threading
import requests
import random
from requests_oauthlib import OAuth1
from datetime import datetime
from requests.exceptions import Timeout


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

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
TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_KEY_SECRET = os.environ.get("TWITTER_CONSUMER_KEY_SECRET")

CONTAINER_ID = os.environ.get("HOSTNAME")

json_credentials = None
rate_limit_reached = False

def process_job_dict(job_dict):
    """ Extract information from message. Necessary since all items in dict become kwargs. """
    tweet_ids = job_dict['urls']
    return {"tweet_ids": tweet_ids}


def get_valid_credentials():
    """ Get credentials from credentialsmanager. """
    global json_credentials
    global rate_limit_reached
    if json_credentials == None or rate_limit_reached:
        if not rate_limit_reached:
            response = requests.get("http://" + CREDENTIALSMANAGER_HOST + ":" + CREDENTIALSMANAGER_PORT + "/first_token/" + CONTAINER_ID)
        else:
            response = requests.get("http://" + CREDENTIALSMANAGER_HOST + ":" + CREDENTIALSMANAGER_PORT + "/new_token/" + CONTAINER_ID)
        if response.status_code == 503:
            LOGGER.info("Received 503 from credentialsmanager. Will sleep now and then retry.")
            time.sleep(int(response.headers.get("Retry-After", 60)))
            return None
        elif response.status_code != 200:
            LOGGER.error("Credentialsmanager returned unexpected response: " + str(response.status_code) + response.text)
            return None
        else:
            assert response.status_code == 200
            rate_limit_reached = False
            json_credentials = json.loads(response.text)

    access_token = json_credentials['access_token']
    access_token_secret = json_credentials['access_token_secret']

    return {'consumer_key': TWITTER_CONSUMER_KEY,
            'consumer_secret': TWITTER_CONSUMER_KEY_SECRET,
            'access_token': access_token,
            'token_secret':     access_token_secret
            }

def refresh_credentials() -> "dict[str,str]":
    credentials = None
    while credentials == None:
        credentials = get_valid_credentials()
    return credentials


def get_oauth_object():
    credentials = None
    while credentials == None:
        credentials = get_valid_credentials()
    return OAuth1(
        credentials['consumer_key'],
        credentials['consumer_secret'],
        credentials['access_token'],
        credentials['token_secret'],
        signature_type="query")


def download_work_item(tweet_ids) -> "dict[int, Tweet]":
    """ Check for valid credentials, download a bunch of tweets and send to db. """
    if type(tweet_ids) == str:
        tweet_ids = [tweet_ids]

    if len(tweet_ids) > 100:
        LOGGER.error(
            msg="Too many ids for a single request! Just using the first 100.")
        tweet_ids = tweet_ids[0:100]

    id_string = ",".join(tweet_ids)
    url = 'https://api.twitter.com/1.1/statuses/lookup.json?tweet_mode=extended&id=' + id_string

    oauth = get_oauth_object()
    try:
        resp = requests.get(url,
                            auth=oauth,
                            timeout=1.0)

        if resp.status_code == 200:
            datetime.utcfromtimestamp(1642336464).isoformat()
            timestamp = int(datetime.now().timestamp()*1000)
            tweet_list = json.loads(resp.text)
            requested_tweets_count = len(tweet_ids)
            downloaded_tweets_count = len(tweet_list)
            remaining = resp.headers.get("x-rate-limit-remaining")
            reset = resp.headers.get("x-rate-limit-reset")
            reset_window = ""
            if reset != None:
                reset_window = datetime.utcfromtimestamp(int(reset)).isoformat()
            LOGGER.warning(str(downloaded_tweets_count/requested_tweets_count*100)[:5] + "%: We downloaded " + str(downloaded_tweets_count) + " tweets from " + str(requested_tweets_count) + " possible ones. " + remaining + "#" + reset_window)
            if os.environ.get("WORKER_TYPE") == "STREAM":
                return {x["id"]:Tweet(x, crawling_timestamp=timestamp, downloadsource=Downloadsource.FILTEREDSTREAM) for x in tweet_list}
            else:
                return {x["id"]:Tweet(x, crawling_timestamp=timestamp) for x in tweet_list}
        elif resp.status_code == 429:
            global rate_limit_reached
            rate_limit_reached = True
            LOGGER.info("Rate limit reached, will switch token.")
            return None # if we return None, we will try to reexecute this
        else:
            LOGGER.warning("Unexpected http response: " + str(resp.status_code) + resp.text)
            return {}
    except Timeout as err:
        LOGGER.warning("Request timed out:")
        LOGGER.warning(err)
    except BaseException as err:
        print('##############################################', flush=True)
        print('#     Error while downloading the tweets     #', flush=True)
        print('##############################################', flush=True)
        LOGGER.error("Unknown error while downloading tweets")
        LOGGER.error(err)




def get_connected_tweets(tweets: "list[Tweet]") -> "list[Tweet]":
    _tweets = tweets.copy()
    downloadstatuses = {
        tweet_id: Downloadstatus.DOWNLOADED for tweet_id in tweets}
    for tweet in tweets.values():
        related_tweets, related_downloadstatuses = tweet.get_related_tweets()

        _tweets, downloadstatuses = Tweet.combine_tweets(
            _tweets, downloadstatuses, related_tweets, related_downloadstatuses)

    return _tweets, downloadstatuses


def save_tweets_to_db(tweets: "list[Tweet]"):
    """ Save tweets to database. """
    # TODO: use batch statement
    # TODO: check for already downloaded ids
    with DBHelper() as helper:
        for tweet in tweets:
            while helper.insert_tweet(tweets[tweet]) == False:
                pass

def ensure_env_variables_exist():
    for variable in ["CASSANDRA_USERNAME",
                    "CASSANDRA_PASSWORD",
                    "CASSANDRA_HOST",
                    "CREDENTIALSMANAGER_HOST",
                    "CREDENTIALSMANAGER_PORT",
                    "TWITTER_CONSUMER_KEY",
                    "TWITTER_CONSUMER_KEY_SECRET",
                    "HOSTNAME",
                    "RABBITMQ_HOST",
                    "RABBITMQ_PORT",
                    "RABBITMQ_USERNAME",
                    "RABBITMQ_PASSWORD",
                    "RABBITMQ_QUEUE_NAME",
                    "RABBITMQ_EXCHANGE_NAME",
                    ]:
        temp = os.environ.get(variable)
        if temp == None or temp == "":
            LOGGER.error(variable + " is not set in worker! Will exit now.")
            exit(1)


# ------------ THREADING --------------- #

def ack_message(ch, delivery_tag):
    if ch.is_open:
        ch.basic_ack(delivery_tag)
    else:  # Channel is already closed, so we can't ACK this message;
        pass


i = 0


def do_work(conn, ch, delivery_tag, body):
    global i
    #print('message No.: ' + str(i))
    i += 1
    thread_id = threading.get_ident()
    LOGGER.info('Thread id: %s Delivery tag: %s Message body: %s', thread_id,
                delivery_tag, body)
    #print(" [x] Received message", flush=True)

    message = body.decode('utf-8')
    job_dict = json.loads(message)

    if len(message) > 0:
        message_parameters = process_job_dict(job_dict)
        tweets = None
        while tweets == None:
            tweets = download_work_item(**message_parameters)
            if tweets == None:
                secs = random.randint(0,10)
                print("Have to retry the tweets, will sleep for " + str(secs) + " seconds.", flush=True)
                time.sleep(secs)
        #all_tweets, all_downloadstatuses = get_connected_tweets(tweets)
        save_tweets_to_db(tweets)
        # TODO: add batch import to cassandra instead of 100 inserts

    cb = functools.partial(ack_message, ch, delivery_tag)
    conn.add_callback_threadsafe(cb)


def on_message(ch, method_frame, _header_frame, body, args):
    (conn, threads) = args
    delivery_tag = method_frame.delivery_tag
    t = threading.Thread(target=do_work, args=(conn, ch, delivery_tag, body))
    t.start()
    threads.append(t)


@ RETRY_ON_AMQP_ERROR
def setup_rabbitmq():
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


# time.sleep(45)

ensure_env_variables_exist()

abort = False
while not abort:

    connection, channel = setup_rabbitmq()

    # Only one task/message at a time
    channel.basic_qos(prefetch_count=1)

    threads = []
    on_message_callback = functools.partial(
        on_message, args=(connection, threads))
    channel.basic_consume(QUEUE_NAME, on_message_callback)

    print(' [*] Waiting for messages. To exit press CTRL+C', flush=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        abort = True
        break
    except pika.exceptions.ConnectionClosedByBroker:
        LOGGER.warn("connection closed by broker.")
        continue
    except pika.exceptions.ConnectionClosed:
        LOGGER.warn('Connection closed. Recovering')
        continue
    abort = True
    break

# Wait for all to complete
#       when running long, "threads" could become *very* long.
#       Restart periodically or implement better solution
for thread in threads:
    thread.join()

connection.close()
