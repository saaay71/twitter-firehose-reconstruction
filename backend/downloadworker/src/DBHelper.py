from cassandra.cluster import Cluster, ProtocolVersion
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy, ConstantSpeculativeExecutionPolicy
from cassandra.connection import OperationTimedOut
from cassandra.cluster import NoHostAvailable
from cassandra.query import SimpleStatement
from cassandra import WriteTimeout
import logging
import random
import time
import os
from Tweet import Tweet

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN, format=LOG_FORMAT)


class DBHelper:
    # Structure taken from https://stackoverflow.com/a/865272

    def __init__(self):
        self.__connect_to_cluster()

    def insert_tweet(self, tweet: Tweet) -> bool:
        query_string = """
                    INSERT INTO tweets (day, hour, minute, ms, datacenterid, serverid, sequenceid, id, crawled_timestamp, user_name, user_displayname, user_id, user_verified, user_description, user_created, user_favourites_count, user_friends_count, user_followers_count, user_statuses_count, user_protected, reply_to_id, reply_to_user, reply_to_user_id, truncated, hashtags, cashtags, urls, user_mentions, text, hearts_count, retweets_count, quoted_status_id, possibly_sensitive, language, download_source, download_status, has_media)
                    VALUES (%(day)s, %(hour)s, %(minute)s, %(ms)s, %(datacenterid)s, %(serverid)s, %(sequenceid)s, %(id)s, %(crawled_timestamp)s, %(user_name)s, %(user_displayname)s, %(user_id)s, %(user_verified)s, %(user_description)s, %(user_created)s, %(user_favourites_count)s, %(user_friends_count)s, %(user_followers_count)s, %(user_statuses_count)s, %(user_protected)s, %(reply_to_id)s, %(reply_to_user)s, %(reply_to_user_id)s, %(truncated)s, %(hashtags)s, %(cashtags)s, %(urls)s, %(user_mentions)s, %(text)s, %(hearts_count)s, %(retweets_count)s, %(quoted_status_id)s, %(possibly_sensitive)s, %(language)s, %(download_source)s, %(download_status)s, %(has_media)s)
                    """

        statement = SimpleStatement(query_string=query_string)#, retry_policy=retry_policy)
        try:
            self.session.execute(statement, parameters=tweet.dict_for_db_statement())
            return True
        except WriteTimeout as wto:
            secs = random.randint(1,10)
            LOGGER.warn("WriteTimeout of cassandra. We will retry in " + str(secs) + " seconds.")
            time.sleep(secs)
            return False

    def __connect_to_cluster(self):
        username = os.environ.get("CASSANDRA_USERNAME")
        password = os.environ.get("CASSANDRA_PASSWORD")
        hostname = os.environ.get("CASSANDRA_HOST")
        auth_provider = PlainTextAuthProvider(username=username, password=password)
        lb_policy = DCAwareRoundRobinPolicy("datacenter1")
        session = None
        while session == None:
            try:
                cluster = Cluster([hostname], auth_provider=auth_provider, load_balancing_policy=lb_policy, protocol_version=ProtocolVersion.V5)
                session = cluster.connect("twitter")
            except OperationTimedOut as oto:
                LOGGER.warn("Operation timed out, will retry...")
                LOGGER.warn(oto.errors)
                secs = random.randint(1,10)
                LOGGER.warn("Will sleep for " + str(secs) + " seconds.")
                time.sleep(secs)
            except NoHostAvailable as nha:
                LOGGER.warn("No Host available, will retry...")
                LOGGER.warn(nha.errors)
                secs = random.randint(1,10)
                LOGGER.warn("Will sleep for " + str(secs) + " seconds.")
                time.sleep(secs)

        self.session = session

    def close(self):
        self.session.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
