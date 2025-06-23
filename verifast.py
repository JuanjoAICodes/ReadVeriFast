# verifast.py

import os
import click
from app import create_app, db
from app.models import User, Article, Tag, QuizAttempt # Importa todos tus modelos

# Crea la instancia de la aplicación
app = create_app()

# Este decorador hace que tus modelos estén disponibles automáticamente
# en el 'flask shell' sin necesidad de importarlos.
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Article=Article, Tag=Tag, QuizAttempt=QuizAttempt)

# Este decorador permite crear comandos de prueba personalizados.
# Por ejemplo, podrías ejecutar 'flask test' si defines una función aquí.
@app.cli.command()
@click.argument('test_names', nargs=-1)
def test(test_names):
    """Run the unit tests."""
    # ... (lógica de pruebas futuras)
    pass

# ¡LA PARTE MÁS IMPORTANTE!
# El CLI de Flask-Babel espera encontrar la instancia de la app
# registrada de esta manera para poder añadir sus comandos.
# No es necesario añadir nada más, al tener la app configurada,
# Flask-Babel se enganchará automáticamente.