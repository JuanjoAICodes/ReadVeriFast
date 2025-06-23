# Standard library imports
import json
from flask import jsonify
# Third-party imports (newspaper is moved to tasks.py)
from flask import current_app, flash, redirect, render_template, request, url_for, session
from flask_login import current_user, login_required
from sqlalchemy import and_, not_, func
from sqlalchemy.orm import selectinload

# Local application imports
from app.core import bp
from app.extensions import db
from app.forms import ArticleSubmitForm, EmptyForm
from app.models import Article, QuizAttempt, Tag
from app.tasks import process_article_task

# Eliminamos la primera definición de index que no se usa para mostrar artículos
# @bp.route('/')
# @bp.route('/index')
# def index():
#     return render_template('index.html')

@bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_article():
    """
    Maneja el envío de nuevas URLs de artículos por parte de los usuarios.
    Si el formulario es válido y se envía (POST), muestra un mensaje
    y redirige al índice.
    Si es una solicitud GET o el formulario no es válido, muestra el formulario de envío.
    """
    form = ArticleSubmitForm()
    if form.validate_on_submit():
        submitted_url = form.url.data
        existing_article = Article.query.filter_by(url=submitted_url).first()

        if existing_article:
            flash('Esta URL ya ha sido enviada anteriormente.')
            return redirect(url_for('core.submit_article'))

        # Crear y guardar el artículo con estado 'pending' para tener un ID.
        article = Article(url=submitted_url, author=current_user, processing_status='pending')
        db.session.add(article)
        db.session.commit()
        
        # Encolar la tarea asíncrona para procesar el artículo
        process_article_task.delay(article.id)

        flash('¡Gracias! Tu artículo ha sido enviado y se está procesando. Aparecerá en la lista principal en breve.')
        return redirect(url_for('core.index')) # Redirigir inmediatamente
    return render_template('core/submit_article.html', title='Enviar Artículo', form=form)
@bp.route('/')
@bp.route('/index')
# @login_required # Descomentar si la página de inicio solo es para usuarios logueados
def index():
    # Consulta todos los artículos, ordenados por los más recientes primero, para mostrar su estado
    articles = Article.query.order_by(Article.timestamp.desc()).all()
    # Se renderiza 'auth/index.html' que contiene la lógica para mostrar los artículos.
    return render_template('auth/index.html', title='Inicio', articles=articles)


@bp.route('/article/<int:article_id>')
# @login_required # Se comenta para permitir el acceso a invitados
def article_detail(article_id):
    # Realiza una consulta para obtener el artículo o devuelve un error 404 si no se encuentra.
    article = Article.query.get_or_404(article_id)
    # Proporciona un título alternativo si el artículo no tiene uno.
    page_title = article.title or "Detalle de Artículo"
    
    # Inicializar la variable para las preguntas del cuestionario.
    quiz_questions = []
    
    # Cargar los datos del cuestionario de forma segura desde el campo JSON.
    if article.quiz_data:
        try:
            # Suponiendo que quiz_data es un string JSON, lo convertimos a un objeto Python.
            quiz_questions = json.loads(article.quiz_data)
        except (json.JSONDecodeError, TypeError):
            # Si el JSON está mal formado o no es un string (p.ej. ya es un dict),
            # no hacemos nada y quiz_questions seguirá siendo una lista vacía.
            pass

    # Creamos una instancia de EmptyForm para la protección CSRF del cuestionario
    # Esto es necesario porque el formulario del cuestionario no es un FlaskForm tradicional
    form = EmptyForm()

    # Determinar WPM para el usuario (registrado o invitado)
    if current_user.is_authenticated:
        current_wpm = current_user.current_wpm
        max_wpm = current_user.max_wpm
    else:
        current_wpm = session.get('guest_current_wpm', 250)
        max_wpm = session.get('guest_max_wpm', 250)

    # Renderiza la plantilla de detalle, pasándole el objeto del artículo.
    return render_template(
        'core/article_detail.html',
        title=page_title,
        article=article,
        quiz_questions=quiz_questions,
        form=form,
        current_wpm=current_wpm,
        max_wpm=max_wpm
    )

@bp.route('/article/<int:article_id>/quiz', methods=['POST'])
# @login_required # Se elimina para permitir envíos de invitados
def submit_quiz(article_id):
    """
    Procesa las respuestas del cuestionario, calcula la puntuación,
    aplica la lógica de gamificación y muestra una página de resultados.
    """
    # 1. VALIDACIÓN Y CARGA DE DATOS
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Envío de formulario inválido. Inténtalo de nuevo.')
        return redirect(url_for('core.article_detail', article_id=article_id))

    article = Article.query.get_or_404(article_id)

    # Determinar el WPM por defecto según si el usuario está logueado o es invitado
    if current_user.is_authenticated:
        default_wpm = current_user.current_wpm
    else:
        default_wpm = session.get('guest_current_wpm', 200)

    # Leer el WPM usado del formulario, con un fallback robusto
    try:
        wpm_used = int(request.form.get('wpm_used', default_wpm))
    except (ValueError, TypeError):
        wpm_used = default_wpm

    quiz_data = {}
    if article.quiz_data:
        try:
            quiz_data = json.loads(article.quiz_data)
        except (json.JSONDecodeError, TypeError):
            flash('Error al procesar los datos del cuestionario.')
            return redirect(url_for('core.article_detail', article_id=article_id))
    questions = quiz_data.get('questions', [])
    if not questions:
        flash('No se encontraron preguntas para este artículo.')
        return redirect(url_for('core.article_detail', article_id=article_id))

    # 2. EVALUACIÓN DE RESPUESTAS
    score = 0
    evaluation_details = []
    for i, question_data in enumerate(questions):
        user_answer = request.form.get(f'question_{i + 1}')
        correct_answer = question_data.get('answer')
        is_correct = user_answer == correct_answer
        if is_correct:
            score += 1
        evaluation_details.append({
            'question_text': question_data.get('question'),
            'user_answer': user_answer or "No respondida",
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })
    score_percentage = (score / len(questions)) * 100 if questions else 0

    # 3. LÓGICA DE GAMIFICACIÓN Y PERSISTENCIA
    if current_user.is_authenticated:
        # --- LÓGICA PARA USUARIOS AUTENTICADOS ---
        attempt = QuizAttempt(user_id=current_user.id, article_id=article.id, score=score_percentage, wpm_used=wpm_used)
        db.session.add(attempt)
        
        user = current_user
        if score_percentage < 50:
            # FRACASO: Ajustar WPM
            last_successful_attempt = QuizAttempt.query.filter_by(user_id=user.id).filter(QuizAttempt.score >= 50).order_by(QuizAttempt.timestamp.desc()).first()
            new_wpm = last_successful_attempt.wpm_used if last_successful_attempt else 200
            user.current_wpm = max(100, new_wpm)
            db.session.commit()
            return render_template('core/quiz_results_fail.html', article=article, new_wpm=user.current_wpm)
        else:
            # ÉXITO: Calcular XP, actualizar WPM y buscar artículo relacionado
            xp_earned = int(score_percentage * (1 + (wpm_used / 100)))
            user.total_xp += xp_earned
            if wpm_used >= user.max_wpm:
                user.max_wpm += 25

            # Lógica de recomendación
            related_article = None
            current_tag_ids = [tag.id for tag in article.tags]
            if current_tag_ids:
                attempted_article_ids = db.session.query(QuizAttempt.article_id).filter(QuizAttempt.user_id == user.id).subquery()
                related_article = db.session.query(Article).join(Article.tags).filter(
                    Tag.id.in_(current_tag_ids),
                    Article.id != article.id,
                    Article.id.notin_(attempted_article_ids)
                ).order_by(func.random()).first()

            db.session.commit()
            return render_template(
                'core/quiz_results_success.html',
                evaluation_details=evaluation_details,
                xp_earned=xp_earned,
                total_xp=user.total_xp,
                related_article=related_article,
                article=article
            )
    else:
        # --- LÓGICA PARA USUARIOS ANÓNIMOS (INVITADOS) ---
        guest_xp = session.get('guest_xp', 0)
        guest_current_wpm = session.get('guest_current_wpm', 200)
        guest_max_wpm = session.get('guest_max_wpm', 300)
        xp_earned = 0
        new_wpm = None

        if score_percentage < 50:
            # FRACASO: Reducir WPM en la sesión
            new_wpm = max(100, guest_current_wpm - 25)
            session['guest_current_wpm'] = new_wpm
        else:
            # ÉXITO: Calcular XP y actualizar WPM en la sesión
            xp_earned = int(score_percentage * (1 + (wpm_used / 100)))
            guest_xp += xp_earned
            session['guest_xp'] = guest_xp
            if wpm_used >= guest_max_wpm:
                session['guest_max_wpm'] = guest_max_wpm + 25
        
        approved = score_percentage >= 50
        # Renderizar la plantilla para invitados
        return render_template(
            'core/quiz_results_anonymous.html',
            article=article,
            score=score_percentage,
            evaluation_details=evaluation_details,
            xp_earned=xp_earned,
            guest_xp=session.get('guest_xp', 0),
            new_wpm=new_wpm,  # Será None en caso de éxito
            approved=approved
        )

@bp.route('/profile')
@login_required
def profile():
    """
    Muestra la página de perfil del usuario, incluyendo su historial de intentos.
    """
    # Consulta para obtener los intentos del usuario, cargando eficientemente
    # la información del artículo relacionado para evitar consultas N+1.
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id)\
        .options(selectinload(QuizAttempt.article))\
        .order_by(QuizAttempt.timestamp.desc())\
        .all()

    return render_template(
        'core/profile.html',
        title='Mi Perfil',
        user=current_user,
        attempts=attempts
    )

@bp.route('/set-theme', methods=['POST'])
@login_required
def set_theme():
    """
    Ruta API para que el usuario guarde su preferencia de tema (claro/oscuro).
    Espera un payload JSON con la clave 'theme' y valor 'light' o 'dark'.
    """
    data = request.get_json()
    if not data or 'theme' not in data:
        return jsonify({'error': 'Payload JSON inválido o falta la clave "theme"'}), 400

    theme_preference = data['theme']

    if theme_preference not in ['light', 'dark', 'auto']: # Añadimos 'auto' como opción válida
        return jsonify({'error': 'Valor de tema inválido. Debe ser "light", "dark" o "auto"'}), 400

    current_user.theme = theme_preference
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'Tema actualizado a {theme_preference}'})


@bp.route('/set-language/<lang>')
def set_language(lang):
    """
    Establece el idioma de la interfaz para el usuario.
    Guarda la preferencia en la sesión y, si el usuario está autenticado,
    también en su perfil de la base de datos.
    """
    # 1. Verificar si el idioma es soportado por la aplicación
    if lang in current_app.config.get('LANGUAGES', []):
        # 2. Guardar en la sesión para todos (invitados y registrados)
        session['language'] = lang

        # 3. Guardar en el perfil para usuarios autenticados
        if current_user.is_authenticated:
            current_user.preferred_language = lang
            db.session.commit()

    # 4. Redirigir a la página anterior o al inicio como fallback
    return redirect(request.referrer or url_for('core.index'))


@bp.route('/tag/<tag_name>')
def articles_by_tag(tag_name):
    """
    Muestra todos los artículos asociados a un tag específico.
    """
    # 1. Buscar el tag por nombre. first_or_404 abortará si no lo encuentra.
    # Usamos func.lower para que la búsqueda no distinga mayúsculas/minúsculas.
    tag = Tag.query.filter(func.lower(Tag.name) == func.lower(tag_name)).first_or_404()

    # 2. Obtener solo los artículos completos asociados a este tag, ordenados por fecha.
    articles = tag.articles.filter_by(processing_status='complete').order_by(Article.timestamp.desc()).all()

    # 3. Renderizar la plantilla, pasando el tag y la lista de artículos.
    return render_template(
        'core/articles_by_tag.html',
        title=f"Artículos sobre '{tag.name}'",
        tag=tag,
        articles=articles
    )