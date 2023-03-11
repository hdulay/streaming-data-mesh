from typing import Dict
from confluent_kafka.admin import AdminClient

from modules.helper import Helper
from modules.rest_proxy import RestProxy

class TopicHelper(Helper):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)
        self.rest_proxy = RestProxy(profile=profile, sdm_config=sdm_config)

    def describe_topic(self, topic:str) -> Dict:
        return self.rest_proxy.describe_topic(topic)
