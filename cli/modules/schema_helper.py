from time import sleep
from confluent_kafka.schema_registry.schema_registry_client import *
from ksql import KSQLAPI
import json
from modules.models import Field
from modules import *

class SchemaHelper:

    def __init__(self, profile:str, config:dict):
        url = config['profiles'][profile]['prop']['schema.registry']['rest']
        self.sr = SchemaRegistryClient({
            "url":f"http://{url}"
        })
        ksql_rest = config['profiles'][profile]['prop']['ksql']['rest']
        self.ksql_client = KSQLAPI(f"http://{ksql_rest}")

    def get_topic_fields(self, topic:str):

        attempts = 0
        while True:
            try:
                id = self.sr.get_versions(f"{topic}-value")[-1]
                fields = json.loads(self.sr.get_schema(id).schema_str)['fields']
                return [ Field(name=field['name'],type=field['type'] if field['type'] is str else 'struct').__dict__ for field in fields]
            except Exception as e: 
                print(e)
                attempts+=1
                if attempts < 5:
                    sleep(2)
                    continue
    
    def get_stream_fields(self, table:str):
        ksql_describe = self.ksql_client.ksql(f'describe {table} extended;')[0]
        ksql_fields = ksql_describe['sourceDescription']['fields']
        return [{ "name":field['name'], "type":field['schema']['type']} for field in ksql_fields]