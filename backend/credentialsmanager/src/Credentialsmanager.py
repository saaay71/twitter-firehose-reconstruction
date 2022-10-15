from datetime import datetime
from re import L
import struct
from datetime import datetime
from urllib import response
import requests
import json
import time
import logging
from requests_oauthlib import OAuth1
import redis
import os

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -20s %(funcName) '
              '-15s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_KEY_SECRET = os.environ.get("TWITTER_CONSUMER_KEY_SECRET")
TWITTER_USER_CREDENTIALS_URL = os.environ.get("TWITTER_USER_CREDENTIALS_URL")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_TOKEN_PREFIX = "blockedToken."

class Token():
    first_request = 0 # unix timestamp in seconds
    used_up = False
    keys = {}

    def __init__(self, keys) -> None:
        self.keys = keys

    def refresh(self, now):
        # if less than 15min, respect used_up status, otherwise toggle
        self.used_up = (now < (self.first_request + (15*60))) and self.used_up

    def is_valid(self):
        return not self.used_up


class Credentialsmanager():

    tokens: "list[Token]" = []
    last_tokens: "dict[str,Token]" = {}
    r = None

    def __init__(self) -> None:
        self.r = redis.Redis(host=REDIS_HOST)
        tokens = None
        while tokens == None:
            LOGGER.info("Trying to pull tokens from webapp now.")
            tokens = self._pull_tokens()
            time.sleep(1)
        self.tokens = tokens

    def get_number_of_usable_tokens(self):
        return len(self.tokens)

    def _pull_tokens(self):
        resp = requests.get(TWITTER_USER_CREDENTIALS_URL)
        if resp.status_code != 200:
            return None
        cred_rows = resp.text.strip().split("\n")
        
        untested_tokens: dict[str,dict] = {json.loads(row)["access_token"]:json.loads(row) for row in cred_rows}
        revoked_tokens = [token_dict for (access_token,token_dict) in untested_tokens.items() if self._revoked(token_dict)]
        tokens = [token_dict for (access_token,token_dict) in untested_tokens.items() if token_dict not in revoked_tokens]
        LOGGER.info("In " + str(len(cred_rows)) + " entries, we had " + str(len(untested_tokens)) + " unique tokens of which we could use " + str(len(tokens)))
        if len(revoked_tokens) > 0:
            LOGGER.info("Revoked tokens:")
            for token in revoked_tokens:
                LOGGER.info(token)
        return [Token({'access_token': token['access_token'], 'access_token_secret': token['access_token_secret']}) for token in tokens]

    def _revoked(self, token_dict):
        EXAMPLE_TWEET_ID = "1477395490220220419"
        EXAMPLE_TWEET_CONTENT = "let's just see how this one goes"
        if self.r.get(REDIS_TOKEN_PREFIX + token_dict["access_token"]):
            return True
        oauth = OAuth1(
            TWITTER_CONSUMER_KEY,
            TWITTER_CONSUMER_KEY_SECRET,
            token_dict['access_token'],
            token_dict['access_token_secret'],
            signature_type="query")
        resp = requests.get(url='https://api.twitter.com/1.1/statuses/lookup.json?tweet_mode=extended&id=' + EXAMPLE_TWEET_ID,
                            auth=oauth,
                            timeout=1.0)
        if resp.status_code == 401 or '"code": 89' in resp.text or "invalid" in resp.text.lower():
            self._save_blocked_status_for(token_dict)
            return True
        if resp.status_code == 200:
            assert len(json.loads(resp.text)) == 1
            assert EXAMPLE_TWEET_CONTENT in resp.text
            return False
        if resp.status_code == 429:
            # Should only be blocked, but work in principle
            return False

        # Better be on the safe side and not use tokens where we don't understand the answer
        return True

    def _save_blocked_status_for(self, token_dict):
        self.r.set(REDIS_TOKEN_PREFIX + token_dict["access_token"], True)

    def refresh_tokens(self, now):
        for token in self.tokens:
            token.refresh(now)

    def get_valid_token_for(self, id, now) -> "tuple[Token,int]":
        self.refresh_tokens(now)
        try:
            token = next(filter(lambda x: not x.used_up, self.tokens))
        except StopIteration:
            # Return estimated timestamp for token being available again and add 10 sec
            self.tokens.sort(key=lambda x: x.first_request)
            return None, 15*60 - (now - self.tokens[0].first_request) +10
        self.last_tokens[id] = token
        if self.more_than_15min_passed(token.first_request, now):
            token.first_request = now
        return token, 0

    def get_credentials(self, id: str, mark_as_blocked: bool):
        timestamp_now = int(datetime.now().timestamp())
        last_token = self.last_tokens.get(id)
        if last_token == None:
            return self.get_valid_token_for(id, timestamp_now)
        else:
            # If >15min passed, then it's probably a reconnect
            if self.more_than_15min_passed(last_token.first_request, timestamp_now):
                #if not last_token.used_up:
                last_token.first_request = timestamp_now
                return last_token
            # Client restarted, it's probably still good:
            if not mark_as_blocked:
                return last_token, 0
            # If <15min passed, the token is most likely used up.
            # It does not really matter whether someone else already marked it
            # We will mark it and continue with another one
            last_token.used_up = True
            return self.get_valid_token_for(id, timestamp_now)

    @classmethod
    def more_than_15min_passed(cls, timestamp, now) -> bool:
        return (timestamp + 15 * 60) < now
