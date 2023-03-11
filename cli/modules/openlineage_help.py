from dataclasses import field
import profile
from typing import Tuple
from unicodedata import name
import attr
import logging
import uuid, datetime
from modules.helpers import *
from modules.helper import Helper
from modules.rest_helper import *
from openlineage.client.serde import Serde
from openlineage.client import *
from openlineage.client.run import *
from openlineage.client.transport import *
from urllib.parse import urlparse
from modules.schema_helper import SchemaHelper
from modules.topic_helper import TopicHelper

log = logging.getLogger(__name__)

@attr.s
class MarquezHttpConfig(Config):
    url: str = attr.ib()
    type: str = attr.ib()

    @classmethod
    def from_dict(cls, params: dict) -> 'MarquezHttpConfig':
        if 'url' not in params:
            raise RuntimeError("`url` key not passed to HttpConfig")
        return cls(**params)

class MarquezHttpTransport(Transport):
    kind = "http"
    config = MarquezHttpConfig

    def __init__(self, config: MarquezHttpConfig):
        self.config = config
        self.url = config.url.strip()

    def emit(self, event: RunEvent):
        j = Serde.to_json(event)
        if log.isEnabledFor(logging.DEBUG):
            log.debug(f"Sending openlineage event {j}")

        headers = {"Content-Type": "application/json; charset=utf-8"}
        return post(self.url, data=j, headers=headers)

class InvalidStateError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class TopicDataset(Dataset):
    def __init__(self, topic:str, namespace: str, name: str, facets: Dict = dict) -> None:
        self.topic = topic
        return super().__init__(namespace=namespace, name=name, facets=facets)

    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()
        

class DatabaseDataset(Dataset):
    def __init__(self, namespace: str, name: str, facets: Dict = dict) -> None:
        return super().__init__(namespace=namespace, name=name, facets=facets)

    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()

class StreamDataset(Dataset):
    def __init__(self, namespace: str, name: str, facets: Dict = dict) -> None:
        return super().__init__(namespace=namespace, name=name, facets=facets)

    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()

class AppendStreamDataset(StreamDataset):
    def __init__(self, namespace: str, name: str, facets: Dict = dict) -> None:
        return super().__init__(namespace=namespace, name=name, facets=facets)

    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()

class ChangeDataset(StreamDataset):
    def __init__(self, namespace: str, name: str, facets: Dict = dict) -> None:
        return super().__init__(namespace=namespace, name=name, facets=facets)

    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()


class OpenLineage(Helper):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)
        self.factory = DefaultTransportFactory()
        self.factory.register_transport("http", MarquezHttpTransport)

    def create_conn_job(self, conn_instance_name:str, conn_config:dict={}) -> Job:
        """
        The topic is not part of the name so that marquez can create multiple edges from this
        connector to multiple topics. Specifically for debezium connectors.
        """
        connector_class = conn_config['connector.class']
        return Job(namespace=self.profile, name=f"{conn_instance_name}.{connector_class}", facets=conn_config)
    
    def get_job(self, namespace:str, name:str, facets:dict) -> Job:
        return Job(namespace=namespace, name=name, facets=facets)

    def get_run(self, facet:dict={})->Run:
        """
        The same Run instance should be the same for the START and COMPLETE RunStates when emitting.
        """
        return Run(runId=str(uuid.uuid4()), facets=facet)

    def emit_run(self, inputs:List[Dataset], outputs:List[Dataset], job:Job, run:Run, producer:str="https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client"):
        """
        Emits both the start and end of a run. You must have both the input and output datasets.
        """
        eventTime = datetime.datetime.now().isoformat()
        start: RunEvent = RunEvent(inputs=inputs, eventTime=eventTime, eventType=RunState.START, job=job, producer=producer, run=run)
        complete: RunEvent = RunEvent(outputs=outputs, eventTime=eventTime, eventType=RunState.COMPLETE, job=job, producer=producer, run=run)

        transport = self.factory.create()
        start_status = transport.emit(start)
        complete_status = transport.emit(complete)
        
        return {
            "start":start_status,
            "complete": complete_status
        }


class DatasetHelper(Helper):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)
        self.schema_helper = SchemaHelper(*Helpers.get_config())
        self.topic_helper = TopicHelper(*Helpers.get_config())

    @staticmethod
    def get_facet(fields:Dict, code:str="") -> Dict:
        return {
            "sourceCode": code,
            "schema": {
                "_producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
                "_schemaURL":"https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/spec/OpenLineage.json#/definitions/SchemaDatasetFacet",
                "fields":fields
            }
        }

    def create_db_dataset(self, type:str, hostname:str, table:str) -> Dataset:
        """
        They only way to get the schema of the database table is to lookup the its corresponding
        topic metadata
        """
        fields = self.schema_helper.get_topic_fields(table)
        return DatabaseDataset(
            namespace=self.profile, 
            name=f"{type}.{hostname}.{table}", 
            facets=self.get_facet(fields=fields)
        )

    def create_topic_dataset(self, topic:str) -> Dataset:
        facet = self.get_facet(self.schema_helper.get_topic_fields(topic))
        return TopicDataset(namespace=self.profile, topic=topic, name=f"topic.{topic}", facets=facet)

    def create_datasets_from_connect(self, connect_config:dict) -> Tuple[List[Dataset], List[Dataset]] :
        connector_class:str = connect_config['connector.class']
        connect:str = connector_class.split('.')[-1].lower()

        if "datagen" in connect:
            topic = connect_config['kafka.topic']
            return (
                [
                    self.create_db_dataset(type=connect, hostname="localhost", table=topic)
                ],
                [
                    self.create_topic_dataset(topic=topic)
                ]
            )
        elif "debezium" in connector_class:
            whitelist = connect_config.get('table.whitelist').split(',') if 'table.whitelist' in connect_config else []
            include = connect_config.get('table.include.list').split(',') if 'table.include.list' in connect_config else []
            tables = whitelist + include
            # table.exclude.list is not supported
            return (
                [
                    self.create_db_dataset(
                        type=connect,
                        hostname=urlparse(connect_config['database.hostname']).hostname,
                        table=table[table.find('.')+1:len(table)].rstrip()
                    ) for table in tables
                ],
                [
                    self.create_topic_dataset(
                        topic=table[table.find('.')+1:len(table)].rstrip()
                    ) for table in tables
                ]
            )

        else:

            is_source = True if 'source' in connect else False

            host_keys = list(filter(
                lambda key: {
                    map(lambda s: s in key.lower, ['host', 'server', 'endpoint', 'url', 'uri'])
                }, 
                connect_config.keys()
            ))
            host = connect_config.get(host_keys[0]) if len(host_keys) > 0 else "localhost"

            table_keys = list(filter(
                lambda key: {
                    map(lambda s: s in key.lower, 
                        [
                            'table', 'collection', 'directory', 'path', 'uri', 'dir', 'folder', 'view',
                            'object', 'topic', 'bucket', 'bin', 'index', 'set'
                        ]
                    )
                }, 
                connect_config.keys()
            ))
            table = connect_config.get(table_keys[0]) if len(table_keys) > 0 else "default"

            if is_source:
                source = self.create_db_dataset(type=connect, hostname=host,table=table)
                sink = self.create_topic_dataset(table)
            else:
                source = self.create_topic_dataset(table)
                sink = self.create_db_dataset(type=connect, hostname=host,table=table)


            return [source, sink]

class ConnectorOpenLineage(Helper):

    def __init__(self, profile:str, sdm_config:Dict, conn_name:str, conn_config:Dict) -> None:
        super().__init__(profile, sdm_config)
        self.conn_config = conn_config
        self.profile = profile
        self.conn_name = conn_name
        self.ds_helper = DatasetHelper(*Helpers.get_config())
        self.open_lineage = OpenLineage(*Helpers.get_config())

    def emit_run(self, conn_resp:Dict) -> Tuple[List[Dataset], List[Dataset]]:
        source, sink = self.ds_helper.create_datasets_from_connect(connect_config=self.conn_config)
        connect_run = self.open_lineage.get_run(facet=conn_resp)
        connect_job = self.open_lineage.create_conn_job(self.conn_name, self.conn_config)

        status = self.open_lineage.emit_run(producer=self.conn_name, inputs=source, outputs=sink, job=connect_job, run=connect_run)

        return (source, sink)

class KsqlOpenLineage(Helper):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)
        self.schema_helper = SchemaHelper(profile=profile, config=sdm_config)
        self.open_lineage = OpenLineage(profile=profile, sdm_config=sdm_config)
        self.ds_helper = DatasetHelper(profile=profile, sdm_config=sdm_config)

    def create_stream_dataset(self, namespace:str, table_type:str, table_name:str, facet:dict={}) -> Dataset:
        if table_type == 'stream':
            return AppendStreamDataset(
                namespace=namespace, 
                name=f"append.{table_name.lower()}", 
                facets=facet
            )
        else:
            return ChangeDataset(
                namespace=self.profile, 
                name=f"change.{table_name.lower()}", 
                facets=facet
            )


    def emit_run(self, inputs:List[Dataset], output:Dataset, ksql_results:dict) -> Dataset:
        command_id = ksql_results['commandId'].replace('`', '').replace('/', '.')
        statement = ksql_results['statementText']

        ksql_run = self.open_lineage.get_run(facet={
            "status": ksql_results
        })
        ksql_job = Job(namespace=self.profile, name=command_id, facets={
            "sql": {
                "_producer": "https://CRYqvLkHm.mhyC3CALxhqMM1",
                "_schemaURL": "https://eOfzKjpqJhOqKYtaKcKtZykNvsnHp.pebuZH,RFS87YQlccD5an5e",
                "query": statement
            }
        })
        
        self.open_lineage.emit_run(
            producer=command_id, 
            inputs=inputs, 
            outputs=[output], 
            job=ksql_job, 
            run=ksql_run
        )

        return output
