
from distutils.sysconfig import get_config_h_filename
import json
from typing import Dict, Tuple

class Helper:
    def __init__(self, profile:str, sdm_config:dict) -> None:
        self.profile = profile
        self.sdm_config = sdm_config

    @classmethod
    def from_dict(cls, params: dict):
        return cls()
