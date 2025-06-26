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
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

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

    def to_dict(self):
        """Devuelve una representación del usuario en diccionario."""
        return {
            'id': self.id,
            'email': self.email,
            'total_xp': self.total_xp,
            'current_wpm': self.current_wpm,
            'max_wpm': self.max_wpm,
        }


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
    is_user_submitted = db.Column(
        db.Boolean, default=False, server_default='false', nullable=False
    )
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

    def to_dict(self):
        """Devuelve una representación del artículo en diccionario."""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'image_url': self.image_url,
            'language': self.language,
            # Llama a to_dict() en cada tag asociado
            'tags': [tag.to_dict() for tag in self.tags.all()]
        }


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # FIX: Se ha actualizado el back_populates para que coincida con el nuevo nombre en User.
    author = db.relationship('User', back_populates='authored_tags')
    articles = db.relationship(
        'Article', secondary=article_tags, back_populates='tags', lazy='dynamic'
    )

    def to_dict(self):
        """Devuelve una representación del tag en diccionario."""
        return {
            'id': self.id,
            'name': self.name
        }


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    wpm_used = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(
        db.DateTime, index=True, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        """Devuelve una representación del intento de quiz en diccionario."""
        return {
            'id': self.id,
            'score': self.score,
            'wpm_used': self.wpm_used,
            # Usamos el campo 'timestamp' y lo formateamos a ISO 8601
            'attempted_at': self.timestamp.isoformat() + 'Z'
        }