from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

# Tabla de asociación para la relación muchos a muchos entre Article y Tag
article_tags = db.Table(
    'article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    # Campos de gamificación
    current_wpm = db.Column(db.Integer, default=200, nullable=False)
    max_wpm = db.Column(db.Integer, default=300, nullable=False)
    total_xp = db.Column(db.Integer, default=0, nullable=False)
    theme = db.Column(db.String(10), default='auto', server_default='auto', nullable=False)
    preferred_language = db.Column(db.String(5), nullable=True)

    # Relaciones
    articles = db.relationship('Article', back_populates='author', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy='dynamic')

    # FIX: Se ha cambiado el nombre de la relación inversa de 'articles' a 'authored_tags'
    # para evitar el conflicto con la relación User <-> Article.
    authored_tags = db.relationship('Tag', back_populates='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), unique=True, nullable=False)
    title = db.Column(db.String(255))
    image_url = db.Column(db.String(512), nullable=True)
    language = db.Column(db.String(10), nullable=True)  # p.ej. 'es', 'en'
    raw_content = db.Column(db.Text)  # Contenido original de newspaper
    clean_content = db.Column(db.Text)
    quiz_data = db.Column(db.Text)  # Almacenado como string JSON
    processing_status = db.Column(db.String(20), default='pending', nullable=False)
    timestamp = db.Column(
        db.DateTime, index=True, default=lambda: datetime.now(timezone.utc)
    )

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', back_populates='articles')

    tags = db.relationship(
        'Tag', secondary=article_tags, back_populates='articles', lazy='dynamic'
    )
    attempts = db.relationship(
        'QuizAttempt', backref='article', lazy='dynamic', cascade="all, delete-orphan"
    )


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # FIX: Se ha actualizado el back_populates para que coincida con el nuevo nombre en User.
    author = db.relationship('User', back_populates='authored_tags')
    articles = db.relationship(
        'Article', secondary=article_tags, back_populates='tags', lazy='dynamic'
    )


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    wpm_used = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(
        db.DateTime, index=True, default=lambda: datetime.now(timezone.utc)
    )