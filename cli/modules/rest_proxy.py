import json
from typing import Dict
from modules.helper import Helper
from modules.rest_helper import *

class RestProxy(Helper):
    
    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)
        self.url = f"http://{sdm_config['profiles'][profile]['prop']['kafka']['rest.proxy']}"
        # self.cluster = json.loads(get(f"{self.url}/clusters/").text)[0]

    def describe_topic(self, topic:str) -> Dict:
        return json.loads(get(f"{self.url}/{topic}").text)
