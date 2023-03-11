#!/usr/bin/env python
import typer
import logging
import cluster
import streaming
import domain
import dp
import json
import connect
import user
from pathlib import Path
from modules.rest_helper import *
from modules.models import *

app = typer.Typer()
app.add_typer(cluster.app, name="cluster", help="cluster tool")
app.add_typer(domain.app, name="domain", help="domain tool")
app.add_typer(streaming.app, name="streaming", help="streaming tool")
app.add_typer(dp.app, name="dp", help="data product tool")
app.add_typer(connect.app, name="connect", help="connector tool")
app.add_typer(user.app, name="user", help="user tool")

@app.command()
def init(email:str = typer.Argument(None, help="email"), url:str = typer.Argument(None, help="url to control plane")):
    """
    Do this first to initialize the CLI to speak to the data mesh services. This will write
    configuration information into .sdm/config.
    Contains keys, domain identification, user identification. etc.
    """
    config = Config(email, url)

    Path(".sdm").mkdir(parents=True, exist_ok=True)
    f = open(".sdm/config.json", "w")
    f.write(json.dumps(config, cls=Encoder))
    f.close()

@app.command()
def switch_domain(domain:str):
    Path(".sdm").mkdir(parents=True, exist_ok=True)
    f = open(".sdm/config.json","r")
    config = json.load(f)
    config['profile'] = domain
    typer.echo(json.dumps(config))
    w = open(".sdm/config.json", "w")
    w.write(json.dumps(config, indent=1, cls=Encoder))
    w.close()

@app.command()
def version(update: bool = False):
    """
    Displays the version of the CLI. Updates the CLI if --update is provided
    """
    typer.echo(f"list")


@app.command()
def login():
    """
    Reads from .smd/ to login
    """
    config = json.load(open(".sdm/config.json"))
    resp = post("{}/login".format(config['url']), config)
    print(dir(resp))
    print(resp.status_code)

@app.command()
def logout():
    """
    Log out
    """
    typer.echo(f"list")

if __name__ == "__main__":
    logging.basicConfig(filename='myapp.log', level=logging.DEBUG)
    app()
