import csv
import json
import requests
import time
from collections import defaultdict
import redis
from datetime import datetime
import os


class FilteredStreamFollower():

    r = None
    current_chunk_id = None
    id_set = None
    BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
    CHUNK_SIZE = 10 * 60  # min * s
    CREATE_URL = "https://api.twitter.com/2/tweets/sample/stream"

    def __init__(self, tweetid_publisher=None) -> None:
        self.r = redis.Redis(host="redis")
        self.id_set = FilteredStreamFollower.empty_id_set()
        self.current_chunk_id = FilteredStreamFollower.get_current_chunk_id()
        self.tweetid_publisher = tweetid_publisher

    @classmethod
    def get_current_chunk_id(cls):
        return cls.unix_to_chunk_id(time.time())

    @classmethod
    def chunk_id_to_unix(cls, chunk_id):
        # returns a unix ts in s
        return int(chunk_id * cls.CHUNK_SIZE)

    @classmethod
    def unix_to_chunk_id(cls, unix_ts):
        # returns a chunk_id
        return unix_ts // cls.CHUNK_SIZE

    @classmethod
    def empty_id_set(cls):
        return defaultdict(lambda: 0, {})

    @classmethod
    def set_bearer_oauth_on(cls, request):
        """
        Method required by bearer token authentication.
        """

        request.headers["Authorization"] = f"Bearer {FilteredStreamFollower.BEARER_TOKEN}"
        request.headers["User-Agent"] = "v2SampledStreamPython"
        return request

    def sendToDatabase(self, id_set):
        start_timestamp = self.chunk_id_to_unix(self.current_chunk_id)
        end_timestamp = self.chunk_id_to_unix(self.current_chunk_id+1)
        _json = json.dumps({'start_timestamp': start_timestamp,
                            'end_timestamp': end_timestamp,
                            'server': [(x[0][0], x[0][1], x[0][2], x[1]) for x in id_set.items()]})
        self.r.set(start_timestamp, _json)  # use start_timestamp as key
        print(_json, flush=True)

    @classmethod
    def decodeSnowflake(cls, snowflake):
        snowflake = int(snowflake)
        timestamp_s = (int(bin(snowflake)[2:-22], 2) + 1288834974657) // 1000
        timestamp_ms = (int(bin(snowflake)[2:-22], 2) + 1288834974657) % 1000
        datacenter_id = int(bin(snowflake)[-22:-17], 2)
        server_id = int(bin(snowflake)[-17:-12], 2)
        sequence_number = int(bin(snowflake)[-12:], 2)
        return timestamp_s, timestamp_ms, datacenter_id, server_id, sequence_number

    def writeToIdSet(self, snowflake_d):
        if self.get_current_chunk_id() > self.current_chunk_id:
            self.sendToDatabase(self.id_set)
            self.current_chunk_id = self.get_current_chunk_id()
            self.id_set = self.empty_id_set()
        self.id_set[(snowflake_d[2], snowflake_d[3], snowflake_d[4])] += 1

    def connect_to_endpoint(self, url):
        print("connect to endpoint")
        response = requests.request(
            "GET", url, auth=FilteredStreamFollower.set_bearer_oauth_on, stream=True)
        print(response.status_code)

        with open('ids.csv', 'a', newline='') as csvfile:
            id_writer = csv.writer(csvfile, delimiter=',',
                                   quotechar='|', quoting=csv.QUOTE_MINIMAL)

            snowflake_batch = []
            for index, response_line in enumerate(response.iter_lines()):
                if index % 100 == 0:
                    print(index, flush=True)
                if response.status_code != 200:
                    print("Request returned an error: {} {}".format(
                        response.status_code, response.text))
                if response.status_code == 429:
                    remaining_secs = int(
                        response.headers["x-rate-limit-reset"]) - int(datetime.now().timestamp())
                    print("Seconds until reopen:" + str(remaining_secs) +
                          ". Will sleep until then.", flush=True)
                    time.sleep(remaining_secs + 1)
                elif response_line:
                    json_response = json.loads(response_line)
                    snowflake_id = json_response['data']['id']
                    snowflake_decoded = FilteredStreamFollower.decodeSnowflake(
                        snowflake_id)

                    self.writeToIdSet(snowflake_decoded)
                    snowflake_batch.append(snowflake_id)

                    id_writer.writerow(snowflake_decoded)
                    if self.tweetid_publisher != None:
                        self.tweetid_publisher.add(snowflake_id)
