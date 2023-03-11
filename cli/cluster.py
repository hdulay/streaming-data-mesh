import typer
import topic
import json
from modules.models import *
from modules.rest_helper import *

app = typer.Typer()
app.add_typer(topic.app, name="topic", help="topic tool")

@app.command()
def list():
    """
    Lists all the streaming platform clusters
    """
    config = json.load(open(".sdm/config.json"))
    profile = config['profile']
    typer.echo(json.dumps(config['profiles'][profile]))

@app.command()
def describe(cluster_id: str):
    """
    Describes a streaming platform. Includes capacity, number of topics and partitions.
    """
    typer.echo(f"describing cluster: {cluster_id}")



if __name__ == "__main__":
    app()
