from ensurepip import bootstrap
from tkinter.font import names
import typer
import sys
import json
app = typer.Typer()
from modules.helpers import *
from modules.rest_helper import *
from modules.openlineage_help import *
from modules.schema_helper import *
from modules.sql_helper import *
from modules.connect_helper import *
from ksql import KSQLAPI


# Available Commands:
#   deployed        List all connectors.
#   list            List all available connectors in artifactory.
#   add             Adds a connector from artifactory.
#   drop            Delete a connection.
#   update          Update a connector from artifactory.

@app.command()
def ps():
    """
    Lists all the deployed connectors
    """
    profile, config = Helpers.get_config()
    helper = ConnectFactory.get_connect_helper(profile=profile, config=config)

    resp = helper.ps()
    typer.echo(resp)

@app.command()
def add(conn_name:str, connector_config: str = typer.Argument(None, help="connector configuration file")):
    """
    Deploys a connector
    """
    resp = deploy_connect(conn_name, connector_config)
    typer.echo(json.dumps(resp))

def add_plugin(plugin:str) -> dict:
    profile, config = Helpers.get_config()
    url = config['profiles'][profile]['prop']['connect']['rest']
    response = get(f"http://{url}/connector-plugins/")
    __restart__(plugin)
    return response

def __restart__(plugin:str):
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

def deploy_connect(connect_name:str, connect_config:str) -> dict:
    """
    Deploys a connector
    """
    profile, sdm_config = Helpers.get_config()
    connect = sdm_config['profiles'][profile]['prop']['connect']
    
    f = open(connect_config, "r")
    json_str = f.read()
    conn_config = json.loads(json_str)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    result = put(f'http://{connect["rest"]}/connectors/{connect_name}/config', json_str, headers=headers)
    conn_resp = json.loads(result.text)
    col = ConnectorOpenLineage(
        profile=profile, 
        sdm_config=sdm_config, 
        conn_name=connect_name, 
        conn_config=conn_config
    )
    sources, sinks = col.emit_run(conn_resp=conn_resp)

    # automatically add a ksql stream
    ksql_rest = sdm_config['profiles'][profile]['prop']['ksql']['rest']
    client = KSQLAPI(f"http://{ksql_rest}")

    for sink in sinks:
        sql = f"create or replace stream {sink.topic} with ( kafka_topic='{sink.topic}', value_format='avro') ;"
        ksql_results = client.ksql(sql)
        kol = KsqlOpenLineage(profile=profile, sdm_config=sdm_config)
        helper = SQLHelperFactory.get_helper(profile, sdm_config)
        output_ds = helper.create_dataset_from_table_desc(sink.topic)
        output = kol.emit_run(inputs=[sink], output=output_ds, ksql_results=ksql_results[0])

    resp = {
        "connector": conn_config,
        "ksql": ksql_results
    }
    return json.dumps(resp)
    

@app.command()
def drop(connect_cluster_id:str, id: str):
    """
    Drops a connector
    """
    typer.echo(f"list")
    
@app.command()
def update(connect_cluster_id:str, id:str, sqlfile: str):
    """
    Updates a connector to a newer version
    """
    typer.echo(f"list")

@app.command()
def describe(name: str):
    """
    Describes a connector, parameters
    """
    profile, config = Helpers.get_config()
    helper = ConnectFactory.get_connect_helper(profile, config)
    typer.echo(helper.describe(connector_name=name))

@app.command()
def start(connect_cluster_id:str, id: str):
    """
    Starts a connector
    """
    typer.echo(f"sql")


@app.command()
def stop(connect_cluster_id:str, id: str):
    """
    Stops a connector
    """
    typer.echo(f"sql")

@app.command()
def restart(connect_cluster_id:str, id: str):
    """
    Restarts a connector
    """
    stop(id)
    start(id)
    typer.echo(f"sql")


if __name__ == "__main__":
    app()
