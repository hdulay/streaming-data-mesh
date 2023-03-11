import typer

app = typer.Typer()


@app.command()
def list():
    """
    Lists all roles in a domain.
    """
    typer.echo(f"list")

@app.command()
def describe(role_id: str):
    """
    Describes a role
    """
    typer.echo(f"describing domain: {id}")

@app.command()
def add(role_id: str):
    """
    Adds a role to the domain.
    """
    typer.echo(f"describing domain: {id}")

@app.command()
def delete(role_id: str):
    """
    Deletes a role from a domain
    """
    typer.echo(f"describing domain: {id}")


if __name__ == "__main__":
    app()
