import click
from flask.cli import with_appcontext

from .extensions import db


def register_commands(app):
    """Register CLI commands."""

    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command():
        """Creates all the database tables."""
        db.create_all()
        click.echo("Initialized the database.")