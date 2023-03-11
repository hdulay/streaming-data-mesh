import typer

app = typer.Typer()

# Available Commands:
#   deployed        List all UDFs.
#   list            List all available UDFS in artifactory.
#   add             Adds a UDF from artifactory.
#   drop            Delete a connection.
#   update          Update a UDF from artifactory.

@app.command()
def list(deployed:bool = False):
    """
    Available UDFs from the repository to add
    """
    typer.echo(f"list")

@app.command()
def add(udf_id: str):
    """
    Add an available UDF
    """
    typer.echo(f"list")

@app.command()
def drop(id: str):
    """
    Drops a UDF
    """
    typer.echo(f"list")
    
@app.command()
def update(id:str, sqlfile: str):
    """
    Updates a UDF to a newer version
    """
    typer.echo(f"list")

@app.command()
def describe(id: str):
    """
    Describes a UDF, parameters, data types, return value
    """
    typer.echo(f"sql")



if __name__ == "__main__":
    app()
