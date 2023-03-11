
from difflib import restore
from typing import Tuple
from ksql import KSQLAPI
from sqlglot import *
import re
from modules.helpers import Helpers
from modules.openlineage_help import *
from modules.models import *

class SQL_Helper(Helper):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)

    def describe(self, table:str) -> Describe:
        pass

    def deploy_sql(self, sql_file:str):
        pass

    def create_dataset_from_table_desc(self, table:str) -> StreamDataset:
        pass

    def parse_tables(self, sql:str) -> tuple[list[str], str]:
        tables = [
            t.sql() for t in parse_one(sql).find_all(exp.Table)
        ]
        output_table = tables[0]
        input_tables = tables[1:]
        return input_tables, output_table


class KSQL_Helper(SQL_Helper):

    def __init__(self, profile: str, sdm_config: dict) -> None:
        super().__init__(profile, sdm_config)
        ksql_rest = sdm_config['profiles'][profile]['prop']['ksql']['rest']
        self.url = f"http://{ksql_rest}"
        self.client = KSQLAPI(self.url)

    def describe(self, table:str) -> Describe:
        describe = self.client.ksql(f'describe {table} extended;')[0]
        fields =  [{ "name":f['name'], "type":f['schema']['type']}  for f in describe['sourceDescription']['fields']]
        table_type = describe['sourceDescription']['type'].lower()
        statement = describe['sourceDescription']['statement']
        topic = describe['sourceDescription']['topic']
        return Describe(fields=fields, table_type=table_type, sql=statement, topic=topic)

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

    def create_dataset_from_table_desc(self, table:str) -> StreamDataset:
        describe:Describe = self.describe(table=table)
        return self.create_stream_dataset(
            namespace=self.profile, 
            table_type=describe.table_type,
            table_name=table,
            facet=DatasetHelper.get_facet(fields=describe.fields, code=describe.sql)
        )

    def deploy_sql(self, sql_file:str):
        f = open(sql_file, "r")
        sql = f.read()
        profile, config = Helpers.get_config()
        ksql_rest = config['profiles'][profile]['prop']['ksql']['rest']
        
        client = KSQLAPI(f"http://{ksql_rest}")

        results = client.ksql(sql)[0]

        _sql = re.sub('(?<=\s)(?i)emit\s*changes(?=\s|;)', '', sql).replace('->', '.') # remove emit changes from ksql
        _sql = re.sub('(?<=\s)(?i)stream(?=\s|;)', 'table', _sql)
        # (?<!create|source|replace)stream(?=\s+) - replace "stream" with maybe "table"
        input_tables, output_table = self.parse_tables(_sql)

        inputs = [ 
            self.create_dataset_from_table_desc(table=table)
            for table in input_tables 
        ]
        describe = self.describe(output_table)
        output = self.create_stream_dataset(
            namespace=self.profile, 
            table_type=describe.table_type,
            table_name=output_table,
            facet=DatasetHelper.get_facet(fields=describe.fields, code=describe.sql)
        )
        # topic = describe['sourceDescription']['topic']
        topic = "CLICK_USERS"
        output_topic = TopicDataset(
            topic=topic, 
            namespace=profile, 
            name=topic, 
            facets=DatasetHelper.get_facet(
                fields=describe.fields, 
                code=describe.sql
            )
        )
        outputs = [ output, output_topic ]
        print(f"{outputs}")

        out = self.emit_run(inputs=inputs, outputs=outputs, ksql_results=results)
        return results

    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()

        print(f"{output}")

        out = self.emit_run(inputs=inputs, output=output, ksql_results=results)

        return results

    def emit_run(self, inputs:List[Dataset], outputs:List[Dataset], ksql_results:dict) -> Dataset:
        command_id = ksql_results['commandId'].replace('`', '').replace('/', '.')
        statement = ksql_results['statementText']

        ol = OpenLineage(profile=self.profile, sdm_config=self.sdm_config)

        ksql_run = ol.get_run(facet={
            "status": ksql_results
        })
        ksql_job = Job(namespace=self.profile, name=command_id, facets={
            "sql": {
                "_producer": "https://CRYqvLkHm.mhyC3CALxhqMM1",
                "_schemaURL": "https://eOfzKjpqJhOqKYtaKcKtZykNvsnHp.pebuZH,RFS87YQlccD5an5e",
                "query": statement
            }
        })
        
        ol.emit_run(
            producer=command_id, 
            inputs=inputs, 
            outputs=outputs, 
            job=ksql_job, 
            run=ksql_run
        )

        return output


class SQLHelperFactory():
    @staticmethod
    def get_helper(profile:str, config:dict) -> SQL_Helper:
        return KSQL_Helper(profile, config)