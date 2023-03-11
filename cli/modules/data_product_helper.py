from typing import Dict
from confluent_kafka.admin import AdminClient

from modules.helper import Helper
from modules.rest_proxy import RestProxy

class DataProductHelper(Helper):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)

    def publish(self, topic:str) -> Dict:
        # call airflow dag
        pass

