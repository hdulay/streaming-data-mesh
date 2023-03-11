import typer

import role
app = typer.Typer()
app.add_typer(role.app, name="role", help="role tool")


@app.command()
def list():
    """
    Lists all users in a domain.
    """
    typer.echo(f"list")

@app.command()
def describe(user_id: str):
    """
    Describes a user
    """
    typer.echo(f"describing domain: {id}")

@app.command()
def add(user_id: str):
    """
    Adds a user to the domain.
    """
    typer.echo(f"describing domain: {id}")

@app.command()
def delete(user_id: str):
    """
    Deletes a user from a domain
    """
    typer.echo(f"describing domain: {id}")

@app.command()
def add_role(user_id: str, role:str):
    """
    Adds a role to the user
    """
    typer.echo(f"describing domain: {id}")

@app.command()
def delete_role(user_id: str, role:str):
    """
    Deletes a role from the user
    """
    typer.echo(f"describing domain: {id}")


if __name__ == "__main__":
    app()
