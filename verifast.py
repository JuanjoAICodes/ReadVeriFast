import os
import click
from app import create_app, db
from app.models import User, Article, QuizAttempt, Tag
from config import Config
from flask_migrate import Migrate

# Create the Flask app instance using the app factory.
# The FLASK_CONFIG environment variable can be used to select a configuration.
app = create_app(os.getenv('FLASK_CONFIG') or Config)
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """
    Makes additional variables available in the Flask shell context
    for easier testing and debugging.
    """
    return {'db': db, 'User': User, 'Article': Article, 'QuizAttempt': QuizAttempt, 'Tag': Tag}

# Defines a new 'translate' command group for the Flask CLI.
@app.cli.group()
def translate():
    """Translation and localization commands."""
    pass

@translate.command()
def update():
    """Update all languages."""
    # 1. Extract all marked strings from the app into a .pot file.
    #    We scan the 'app' directory and use '_' as the extraction keyword.
    if os.system('pybabel extract -F babel.cfg -k _ -o messages.pot app'):
        raise RuntimeError('extract command failed')
    # 2. Update the language-specific .po files with the new strings.
    if os.system('pybabel update -i messages.pot -d app/translations'):
        raise RuntimeError('update command failed')
    # 3. Clean up the temporary .pot file.
    os.remove('messages.pot')
    click.echo('Translation files updated.')

@translate.command()
def compile():
    """Compile all languages."""
    # Compiles the .po files into .mo files, which are used by the application.
    if os.system('pybabel compile -d app/translations'):
        raise RuntimeError('compile command failed')
    click.echo('Translations compiled.')

@translate.command()
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    # We scan the 'app' directory and use '_' as the extraction keyword.
    if os.system('pybabel extract -F babel.cfg -k _ -o messages.pot app'):
        raise RuntimeError('extract command failed')
    if os.system(f'pybabel init -i messages.pot -d app/translations -l {lang}'):
        raise RuntimeError('init command failed')
    os.remove('messages.pot')
    click.echo(f"Language '{lang}' initialized in app/translations.")