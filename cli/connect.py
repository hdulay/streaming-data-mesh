import typer
import sys

from modules.helpers import Helpers
import connector
from modules.rest_helper import *
from modules.helper import *
from modules.connect_helper import *
import docker

app = typer.Typer()
app.add_typer(connector.app, name="connector", help="Tool to manage connectors")

@app.command()
def plugins():
    """
    Lists all the connect clusters
    """
    
    profile, config = Helpers.get_config()
    # connect_help = ConnectHelper(profile, config)
    # connect_help.add_plugin()
    url = config['profiles'][profile]['prop']['connect']['rest']
    response = get(f"http://{url}/connector-plugins/")
    typer.echo(response.text)

@app.command()
def add(plugin:str):
    """
    Installs a connector into a connect cluster
    """

    profile, config = Helpers.get_config()
    helper = ConnectFactory.get_connect_helper(profile, config)
    typer.echo(helper.add_plugin(plugin))


@app.command()
def describe(connect_id: str):
    """
    Describes a connect cluster
    """
    list()



if __name__ == "__main__":
    app()
