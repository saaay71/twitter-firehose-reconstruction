import logging
from datetime import datetime
from snowflake.snowflake import decodeSnowflake, decodeTimestamp
from Downloadstatus import Downloadstatus
from Downloadsource import Downloadsource

from cassandra.query import UNSET_VALUE

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN, format=LOG_FORMAT)

class Tweet():
    """ A wrapper object for the json we get back from twitter. More tweets can be hidden here when they are embedded. """

    tweet_json = None
    crawling_timestamp = None
    downloadstatus = None
    downloadsource = None

    def __init__(self, tweet_json, crawling_timestamp, downloadstatus=Downloadstatus.DOWNLOADED, downloadsource=Downloadsource.LOOKUP) -> None:
        assert("id" in tweet_json)
        self.tweet_json = tweet_json
        self.crawling_timestamp = crawling_timestamp
        self.downloadstatus = downloadstatus
        self.downloadsource = downloadsource
    
    def __str__(self):
        return "Tweet: {} by {}:\t {}\n".format(self.id_(), self.username(), self.text())

    def id_(self) -> int:
        return self.tweet_json["id"]

    def username(self) -> str:
        if self.tweet_json.get("user"):
            return self.tweet_json.get("user").get("screen_name")
    
    def text(self) -> str:
        return self.tweet_json.get("full_text")

    def is_truncated(self) -> bool:
        return self.tweet_json.get("truncated")

    def has_all_important_fields(self) -> bool:
        """ Make sure the tweet has the minimal set of fields. Add more fields if needed. """
        return (not self.is_truncated()
                and self.tweet_json.get("id") != None
                and self.tweet_json.get("full_text") != None
                and self.tweet_json.get("user") != None
                )

    def get_related_tweets(self) -> "tuple[dict[int, Tweet], dict[int, Downloadstatus]]":
        """ Return all snowflakes that are discovered by this tweet without its own snowflake. """
        tweets: dict[int, Tweet] = {}
        downloadstatuses: dict[int, Downloadstatus] = {}

        # This tweet is a reply to another tweet
        if self.tweet_json["in_reply_to_status_id"] != None:
            tweets[self.tweet_json["in_reply_to_status_id"]] = None
            downloadstatuses[self.tweet_json["in_reply_to_status_id"]] = Downloadstatus.SEEN

        # This tweet quotes another tweet
        if self.tweet_json.get("quoted_status_id") != None:

            # The other tweet was not sent inline in this response, we just have the id
            if self.tweet_json["quoted_status"] == None:
                tweets[self.tweet_json["quoted_status_id"]] = None
                downloadstatuses[self.tweet_json["quoted_status_id"]] = Downloadstatus.SEEN
            
            # At least parts of this tweet have been sent inline already
            else:
                quoted_tweet = Tweet(self.tweet_json["quoted_status"], crawling_timestamp=self.crawling_timestamp)
                tweets[self.tweet_json["quoted_status_id"]] = quoted_tweet
                # 
                if quoted_tweet.has_all_important_fields():
                    downloadstatuses[self.tweet_json["quoted_status_id"]] = Downloadstatus.DOWNLOADED
                    quoted_tweet.downloadstatus = Downloadstatus.DOWNLOADED
                else:
                    downloadstatuses[self.tweet_json["quoted_status_id"]] = Downloadstatus.INCOMPLETE
                    quoted_tweet.downloadstatus = Downloadstatus.INCOMPLETE
                # quoted_tweets can be replies themselves
                related_tweets, related_downloadstatuses = quoted_tweet.get_related_tweets()
                tweets, downloadstatuses = Tweet.combine_tweets(tweets, downloadstatuses, related_tweets, related_downloadstatuses)

    
        return tweets, downloadstatuses

    def get_entity(self, name):
        entities = self.tweet_json.get("entities")
        if entities == None:
            return None
        content = entities.get(name)
        if content == None:
            return None
        return content
    
    def extract_urls(self):
        return set([url.get("expanded_url", url.get("url", "")) for url in self.get_entity("urls")])
    
    def extract_mentions(self):
        return set([mention.get("id_str", "") for mention in self.get_entity("user_mentions")])
    
    def extract_hashtags(self):
        return set([hashtag.get("text", "") for hashtag in self.get_entity("hashtags")])
    
    def extract_cashtags(self):
        return set([symbol.get("text", "") for symbol in self.get_entity("symbols")])

    def dict_for_db_statement(self) -> "dict":
        """ Return a dict suitable for direct use with insert statements from full tweet json. """
        # TODO: handle blocked, protected & other account related issues, possibly through retrying
        tweet_json = self.get_json()
        timestamp, datacenterid, serverid, sequenceid = decodeSnowflake(tweet_json["id"])
        days, hour, minute, ms = decodeTimestamp(timestamp)
        if tweet_json["truncated"]:
            LOGGER.error("text is truncated despite extended tweet_mode query parameter")
        tweet = {
            "day": days,
            "hour": hour,
            "minute": minute,
            "ms": ms,
            "datacenterid": datacenterid,
            "serverid": serverid,
            "sequenceid": sequenceid,
            "id": tweet_json["id"],
            "text": tweet_json["full_text"],
            "hearts": tweet_json["favorite_count"],
            "crawled_timestamp": self.crawling_timestamp,
            "reply_to_id": tweet_json["in_reply_to_status_id"],
            "reply_to_user": tweet_json["in_reply_to_screen_name"],
            "reply_to_user_id": tweet_json["in_reply_to_user_id"],
            "truncated": tweet_json["truncated"],
            "hashtags": self.extract_hashtags(),
            "cashtags": self.extract_cashtags(),
            "urls": self.extract_urls(),
            "user_mentions": self.extract_mentions(),

            "hearts_count": tweet_json["favorite_count"],
            "retweets_count": tweet_json["retweet_count"],
            "quoted_status_id": tweet_json.get("quoted_status_id"),
            "possibly_sensitive": tweet_json.get("possibly_sensitive"),
            "language": tweet_json["lang"],
            "has_media": True if self.get_entity("media") else False,
        }
        if tweet_json["user"] != None:
            tweet["user_name"] = tweet_json["user"]["screen_name"]
            tweet["user_displayname"] = tweet_json["user"]["name"]
            tweet["user_id"] = tweet_json["user"]["id"]
            tweet["user_verified"] = tweet_json["user"]["verified"]
            tweet["user_description"] = tweet_json["user"]["description"]
            tweet["user_created"] = int(datetime.strptime(tweet_json["user"]["created_at"], '%a %b %d %H:%M:%S %z %Y').timestamp()*1000)
            tweet["user_favourites_count"] = tweet_json["user"]["favourites_count"]
            tweet["user_friends_count"] = tweet_json["user"]["friends_count"]
            tweet["user_followers_count"] = tweet_json["user"]["followers_count"]
            tweet["user_statuses_count"] = tweet_json["user"]["statuses_count"]
            tweet["user_protected"] = tweet_json["user"]["protected"]

        tweet["download_status"] = int(self.downloadstatus)
        tweet["download_source"] = int(self.downloadsource)

        Tweet.set_missing_values_to_UNSET(tweet)
        return tweet

    @classmethod
    def set_missing_values_to_UNSET(cls, tweet_dict):
        for key in cls.get_all_expected_keys():
            # This evaluates to true for None, [], {}, set() and non-existing values
            # but leaves bools and 0's untouched
            if not tweet_dict.get(key) and type(tweet_dict.get(key)) != bool and type(tweet_dict.get(key)) != int:
                tweet_dict[key] = None
        # Use UNSET_VALUE instead of None if you use prepared statements
        # Otherwise you will get tombstones


    @classmethod
    def combine_tweets(cls,
                        tweetsA: "dict[int,Tweet]",
                        statusesA: "dict[int, Downloadstatus]",
                        tweetsB: "dict[int,Tweet]",
                        statusesB: "dict[int, Downloadstatus]"
                        ) -> "tuple[dict[int, Tweet], dict[int, Downloadstatus]]":
        """ Combine tweets by comparing their downloadstatuses to end up with duplicateless, most complete tweets. """
        for tweet_id in tweetsB:
            # both lists contain the tweet_id, tweetsA might only have it with status SEEN
            if tweetsA.get(tweet_id) != None:
                if statusesB[tweet_id].is_better_than(statusesA[tweet_id]):
                    tweetsA[tweet_id] = tweetsB[tweet_id]
                    statusesA[tweet_id] = statusesB[tweet_id]
            else:  # tweetsA does not contain this, so we'll att this tweet
                tweetsA[tweet_id] = tweetsB[tweet_id]
                statusesA[tweet_id] = statusesB[tweet_id]

        return tweetsA, statusesA

    def get_json(self) -> dict:
        return self.tweet_json

    @classmethod
    def get_all_expected_keys(cls) -> list:
        return [
            "day",
            "hour",
            "minute",
            "ms",
            "datacenterid",
            "serverid",
            "sequenceid",
            "id",
            "crawled_timestamp",
            "user_name",
            "user_displayname",
            "user_id",
            "user_verified",
            "user_description",
            "user_created",
            "user_favourites_count",
            "user_friends_count",
            "user_followers_count",
            "user_statuses_count",
            "user_protected",
            "reply_to_id",
            "reply_to_user",
            "reply_to_user_id",
            "truncated",
            "hashtags",
            "cashtags",
            "urls",
            "user_mentions",
            "text",

            "hearts_count",
            "retweets_count",
            "quoted_status_id",
            "possibly_sensitive",
            "language",
            "download_source",
            "download_status",
            "has_media",
        ]
