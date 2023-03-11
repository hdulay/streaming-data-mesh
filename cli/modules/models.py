import json

class Config:
    def __init__(self, name, profile, url, profiles:dict = {}):
        self.name = name
        self.url = url
        self.profile = profile
        self.profiles = profiles

class ClusterLink:
    def __init__(self, config:dict):
        self.config = config

class Encoder(json.JSONEncoder):
    def default(self, o):
            return o.__dict__

class Field:
    def __init__(self, name:str, type:str) -> None:
        self.name = name
        self.type = type

class Describe:
    def __init__(self, fields:list[Field], table_type:str, sql:str, topic:str) -> None:
        self.fields:list[Field] = fields
        self.table_type = table_type
        self.sql = sql
        self.topic = topic
