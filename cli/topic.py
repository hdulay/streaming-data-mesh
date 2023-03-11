
import os
import sys

from modules.helpers import Helpers
from modules.helper import *
import typer, json
from confluent_kafka.admin import AdminClient

app = typer.Typer()

# Available Commands:
#   list            List all available Kafka cluster in your domain.
#   create          Creates a topic
#   delete          Delete a topic
#   publish         Published the topic as a data product.
#                   This will generate an AsyncAPI and send it
#                   to the streaming data catalog.         
#   consume         Consume the data in the topic
#   produce         Produce some data to the topic
#   describe        Describes a topic

@app.command()
def list():
    """
    Lists the topics
    """
    profile, config = Helpers.get_config()
    bootstrap = config['profiles'][profile]['prop']['kafka']['bootstrap.servers']
    admin = AdminClient({
        "bootstrap.servers":bootstrap
    })
    topics = [topic for topic in admin.list_topics().topics.keys()]

    typer.echo(json.dumps(topics))


@app.command()
def create(cluster_id: str, name: str, partitions:int=6):
    """
    Create a topic
    """
    typer.echo(f"list")

@app.command()
def delete(cluster_id: str, topic: str):
    """
    Deletes a topic
    """
    typer.echo(f"list")

@app.command()
def produce(cluster_id: str, topic: str, msg:str):
    """
    Produces to a topic given a cluster id
    """
    typer.echo(f"list")

@app.command()
def publish(cluster_id: str, topic: str, name:str, description:str):
    """
    Publishes a topic as a streaming data product
    """
    typer.echo(f"list")

@app.command()
def consume(cluster_id: str, topic: str, beginning:bool = False):
    """
    Consumes from a topic
    """
    typer.echo(f"list")

@app.command()
def describe(cluster_id: str, topic: str):
    """
    Describes a topic
    """
    typer.echo(f"describing topic: {topic} in cluster {cluster_id}")



if __name__ == "__main__":
    app()
