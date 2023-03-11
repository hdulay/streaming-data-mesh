import typer

app = typer.Typer()

@app.command()
def list():
    """
    List all access controls including all the data products and their consuming domains
    """
    typer.echo(f"list")

@app.command()
def describe(access_control_id : str):
    """
    Describes an access control list including the data product and the consuming domain
    """
    typer.echo(f"describing domain: {access_control_id}")

@app.command()
def grant(data_product_id:str, consuming_domain:str, remove:bool=False):
    """
    Grants access to a data product to a consuming domain.
    """
    typer.echo(f"granting access to {data_product_id} for {consuming_domain}")


if __name__ == "__main__":
    app()
