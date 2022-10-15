import json

class QueuePublisher():

    snowflake_buffer = []

    def __init__(self, rabbit_channel, exchange_name, queue_name) -> None:
        self.rabbit_channel = rabbit_channel
        self.exchange_name = exchange_name
        self.queue_name = queue_name

    def add(self, snowflake_id):
        self.snowflake_buffer.append(snowflake_id)
        if len(self.snowflake_buffer) >= 100:
            self._publish_to_rabbitmq(self.snowflake_buffer)
            self.snowflake_buffer = []

    def _publish_to_rabbitmq(self, tweet_ids):
        """ Publish a single work item to the queue. """
        job_dict = {}
        job_dict['urls'] = tweet_ids
        self.rabbit_channel.basic_publish(exchange=self.exchange_name,
                            routing_key=self.queue_name,
                            body=json.dumps(job_dict))
