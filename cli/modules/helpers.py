from typing import Tuple, Dict
import json

class Helpers:
    @staticmethod
    def get_config() -> Tuple[str, Dict]:
        config = json.load(open(".sdm/config.json"))
        profile = config['profile']
        return (profile, config)