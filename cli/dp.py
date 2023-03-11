import typer

import access

app = typer.Typer()
app.add_typer(access.app, name="access", help="access controls for data products")


@app.command()
def list():
    """
    Lists all the data products.
    """
    typer.echo(f"list")

@app.command()
def describe(data_product_id: str):
    """
    Describes a data product. Including schemas.
    """
    typer.echo(f"describing data product: {data_product_id} in {domain}")



if __name__ == "__main__":
    app()
