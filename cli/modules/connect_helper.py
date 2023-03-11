
import json, docker
from modules.helper import Helper
from modules.openlineage_help import ConnectorOpenLineage, KsqlOpenLineage
from modules.rest_helper import *
from ksql import KSQLAPI

from modules.sql_helper import SQLHelperFactory

class ConnectHelper(Helper):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)

    def add_plugin(self, plugin:str) -> dict:
        pass

    def deploy_connect(self, connect_name:str, connect_config:str) -> dict:
        pass

    def ps(self) -> dict:
        pass

    def describe(self, connector_name:str) -> dict:
        pass

    def start(self, connector_name:str) -> dict:
        pass

    def stop(self, connector_name:str, force:bool=False) -> dict:
        pass

    def delete(self, connector_name:str) -> dict:
        pass

class KafkaConnect(ConnectHelper):
    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)

    def ps(self) -> dict:
        connect = self.sdm_config['profiles'][self.profile]['prop']['connect']
        # PUT /connectors/(string:name)/config
        resp = json.loads(get(f'http://{connect["rest"]}/connectors').text)
        return resp

    def describe(self, connector_name: str) -> dict:
        connect = self.sdm_config['profiles'][self.profile]['prop']['connect']

        status = json.loads(get(f'http://{connect["rest"]}/connectors/{connector_name}/status').text)
        config = json.loads(get(f'http://{connect["rest"]}/connectors/{connector_name}/config').text)
        return {
            "status": status,
            "config": config
        }

    def deploy_connect(self, connect_name:str, connect_config:str) -> dict:
        """
        Deploys a connector
        """
        connect = self.sdm_config['profiles'][self.profile]['prop']['connect']
        
        f = open(connect_config, "r")
        json_str = f.read()
        conn_config = json.loads(json_str)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        result = put(f'http://{connect["rest"]}/connectors/{connect_name}/config', json_str, headers=headers)
        conn_resp = json.loads(result.text)
        col = ConnectorOpenLineage(
            profile=self.profile, 
            sdm_config=self.sdm_config, 
            conn_name=connect_name, 
            conn_config=conn_config
        )
        sources, sinks = col.emit_run(conn_resp=conn_resp)

        # automatically add a ksql stream
        ksql_rest = self.config['profiles'][self.profile]['prop']['ksql']['rest'] # TODO
        client = KSQLAPI(f"http://{ksql_rest}")

        for sink in sinks:
            sql = f"create or replace stream {sink.topic} with ( kafka_topic='{sink.topic}', value_format='avro') ;"
            ksql_results = client.ksql(sql)
            kol = KsqlOpenLineage(profile=self.profile, sdm_config=self.config)
            helper = SQLHelperFactory.get_helper(self.profile, self.sdm_config)
            output_ds = helper.create_dataset_from_table_desc(sink.topic)
            output = kol.emit_run(inputs=[sink], output=output_ds, ksql_results=ksql_results[0])

        resp = {
            "connector": conn_config,
            "ksql": ksql_results
        }
        return json.dumps(resp)


class DockerKafkaConnect(KafkaConnect):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)
        self.config = sdm_config

    def add_plugin(self, plugin:str) -> dict:
        url = self.config['profiles'][self.profile]['prop']['connect']['rest']
        response = get(f"http://{url}/connector-plugins/")
        self.__restart__(plugin)
        return {}

    def __restart__(self, plugin:str):
         # restarting the container starts the connector
        client = docker.from_env()
        container = client.containers.get('connect')
        install = container.exec_run(f'confluent-hub install --no-prompt {plugin}')
        container.restart()
        return json.dumps(
            {
                "install.status": {
                    "exit_code":install.exit_code,
                    "output":install.output.decode('utf8')
                }
            }
        )

    # def deploy_connect(self, connect_name:str, connect_config:str):
    #     """
    #     Deploys a connector
    #     """
    #     return self.__deploy_to_kafka_connect__(
    #         connect_name=connect_name, 
    #         connect_config=connect_config
    #     )

    # def __deploy_to_kafka_connect__(self, connect_name:str, connect_config:str):
    #     connect = self.config['profiles'][self.profile]['prop']['connect']
        
    #     f = open(connect_config, "r")
    #     json_str = f.read()
    #     conn_config = json.loads(json_str)
    #     result = put(
    #         f'http://{connect["rest"]}/connectors/{connect_name}/config', 
    #         json_str, 
    #         headers={"Content-Type": "application/json; charset=utf-8"}
    #     )
    #     conn_resp = json.loads(result.text)
    #     col = ConnectorOpenLineage(
    #         profile=self.profile, 
    #         sdm_config=self.config, 
    #         conn_name=connect_name, 
    #         conn_config=conn_config
    #     )
    #     sources, sinks = col.emit_run(conn_resp=conn_resp)

    #     # automatically add a ksql stream
    #     ksql_rest = self.config['profiles'][self.profile]['prop']['ksql']['rest'] # TODO
    #     client = KSQLAPI(f"http://{ksql_rest}")

    #     for sink in sinks:
    #         sql = f"create or replace stream {sink.topic} with ( kafka_topic='{sink.topic}', value_format='avro') ;"
    #         ksql_results = client.ksql(sql)
    #         kol = KsqlOpenLineage(profile=self.profile, sdm_config=self.config)
    #         output_ds = kol.create_dataset_from_table_desc(sink.topic)
    #         output = kol.emit_run(inputs=[sink], output=output_ds, ksql_results=ksql_results[0])

    #     return {
    #         "connector": conn_config,
    #         "ksql": ksql_results
    #     }


class ConnectFactory():
    def get_connect_helper(profile:str, config=dict) -> ConnectHelper:
        return DockerKafkaConnect(profile, config)