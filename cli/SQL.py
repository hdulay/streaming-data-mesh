import typer
import json
import re
from sqlglot import *
from modules.helper import *
from modules.rest_helper import *
from modules.openlineage_help import *
from modules.schema_helper import *
from modules.models import *

app = typer.Typer()

types = {
    "long":"bigint"
}
def type_mapping(dt:str):
    ksql_type = types.get(dt)
    return dt if ksql_type is None else ksql_type

@app.command()
def ps():
    """
    List all running sql with id.
    """
    typer.echo(f"list")

@app.command()
def add(sql_file:str, description:str=None):
    """
    Add a sql to the stream processing platform
    """
    profile, config = Helpers.get_config()
    sql = open(sql_file, "r").read()
    ksql_rest = config['profiles'][profile]['prop']['ksql']['rest']
    client = KSQLAPI(f"http://{ksql_rest}")
    results = client.ksql(sql)[0]

    input_tables, output_table = parse_tables(sql)

    inputs = [ 
        table_dataset(profile, table, client)
        for table in input_tables 
    ]

    desc = describe(output_table, client)
    output_ds = table_dataset(profile, output_table, client)
    topic = desc.topic
    output_topic = TopicDataset(
        topic=topic, 
        namespace=profile, 
        name=f"topic.{topic}", 
        facets=DatasetHelper.get_facet(
            fields=desc.fields, 
            code=desc.sql
        )
    )
    outputs = [ output_ds, output_topic ]

    emit_run(profile=profile, inputs=inputs, outputs=outputs, ksql_results=results, config=config)
    typer.echo(f"{json.dumps(results)}")

def parse_tables(sql:str) -> tuple[list[str], str]:
    _sql = re.sub('(?<=\s)(?i)emit\s*changes(?=\s|;)', '', sql).replace('->', '.') # remove emit changes from ksql
    _sql = re.sub('(?<=\s)(?i)stream(?=\s|;)', 'table', _sql)
    # (?<!create|source|replace)stream(?=\s+) - replace "stream" with maybe "table"
    tables = [
        t.sql() for t in parse_one(_sql).find_all(exp.Table)
    ]
    output_table = tables[0]
    input_tables = tables[1:]
    return input_tables, output_table

def create_stream_dataset(namespace:str, table_type:str, table_name:str, facet:dict={}) -> Dataset:
    if table_type == 'stream':
        return AppendStreamDataset(
            namespace=namespace, 
            name=f"append.{table_name.lower()}", 
            facets=facet
        )
    else:
        return ChangeDataset(
            namespace=namespace, 
            name=f"change.{table_name.lower()}", 
            facets=facet
        )

def describe(table:str, client:KSQLAPI) -> Describe:
    describe = client.ksql(f'describe {table} extended;')[0]
    fields =  [{"name":f['name'], "type":f['schema']['type']}  for f in describe['sourceDescription']['fields']]
    table_type = describe['sourceDescription']['type'].lower()
    statement = describe['sourceDescription']['statement']
    topic = describe['sourceDescription']['topic']
    return Describe(fields=fields, table_type=table_type, sql=statement, topic=topic)

def table_dataset(profile:str, table:str, client:KSQLAPI) -> StreamDataset:
    desc:Describe = describe(table=table, client=client)
    return create_stream_dataset(
        namespace=profile, 
        table_type=desc.table_type,
        table_name=table,
        facet=DatasetHelper.get_facet(fields=desc.fields, code=desc.sql)
    )

def emit_run(profile:str, inputs:List[Dataset], outputs:List[Dataset], ksql_results:dict, config:dict) -> Dataset:
    command_id = ksql_results['commandId'].replace('`', '').replace('/', '.')
    statement = ksql_results['statementText']

    ol = OpenLineage(profile=profile, sdm_config=config)

    ksql_run = ol.get_run(facet={
        "status": ksql_results
    })
    ksql_job = Job(namespace=profile, name=command_id, facets={
        "sql": {
            "_producer": "https://CRYqvLkHm.mhyC3CALxhqMM1",
            "_schemaURL": "https://eOfzKjpqJhOqKYtaKcKtZykNvsnHp.pebuZH,RFS87YQlccD5an5e",
            "query": statement
        }
    })

    print(f"{outputs} --- {inputs}")
    
    ol.emit_run(
        producer=command_id, 
        inputs=inputs, 
        outputs=outputs, 
        job=ksql_job, 
        run=ksql_run
    )

    return outputs

@app.command()
def drop(id: str):
    """
    Deletes a sql
    """
    typer.echo(f"list")

@app.command()
def update(id:str, sqlfile: str):
    """
    Updates/replaces a deployed sql
    """
    typer.echo(f"list")

@app.command()
def explain(id: str):
    """
    Explains a sql
    """
    typer.echo(f"sql")

@app.command()
def start(id: str):
    """
    Starts a sql
    """
    typer.echo(f"sql")


@app.command()
def stop(id: str):
    """
    Stops a sql
    """
    typer.echo(f"sql")

@app.command()
def restart(id: str):
    """
    Restarts a sql
    """
    stop(id)
    start(id)
    typer.echo(f"sql")


if __name__ == "__main__":
    app()
