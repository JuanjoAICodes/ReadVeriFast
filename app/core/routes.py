# Standard library imports
import json
from flask import jsonify
from datetime import datetime, timedelta, timezone # Third-party imports (newspaper is moved to tasks.py)
# Third-party imports (newspaper is moved to tasks.py)
from flask import current_app, flash, redirect, render_template, request, url_for, session
from flask_babel import _
from flask_login import current_user, login_required 
from sqlalchemy import and_, not_, func, select
from sqlalchemy.orm import selectinload # Import json and celery

from flask_wtf.csrf import validate_csrf
# Local application imports
from app.core import bp
from app.extensions import db
from app.forms import ArticleSubmitForm, EmptyForm
from app.models import Article, QuizAttempt, Tag, article_tags
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
            flash(_('Esta URL ya ha sido enviada anteriormente.'))
            return redirect(url_for('core.submit_article'))

        # Crear y guardar el artículo con estado 'pending' para tener un ID.
        article = Article(
            url=submitted_url, author=current_user, processing_status='pending', is_user_submitted=True
        )
        db.session.add(article)

        # --- Añadir tag "community-pick" a artículos de usuarios ---
        COMMUNITY_TAG_NAME = 'community-pick'
        # Busca el tag ignorando mayúsculas/minúsculas
        community_tag = Tag.query.filter(func.lower(Tag.name) == func.lower(COMMUNITY_TAG_NAME)).first()
        if not community_tag:
            # Si no existe, lo crea
            community_tag = Tag(name=COMMUNITY_TAG_NAME)
            db.session.add(community_tag)
        # Añade el tag al nuevo artículo
        article.tags.append(community_tag)


        # Hacemos flush para obtener un ID para el artículo sin finalizar la transacción
        db.session.flush()

        # Encolar la tarea asíncrona para procesar el artículo
        process_article_task.delay(article.id)
        db.session.commit() # Commit final solo si la tarea se encoló con éxito

        flash(_('¡Gracias! Tu artículo ha sido enviado y se está procesando. Aparecerá en la lista principal en breve.'))
        return redirect(url_for('core.articles')) # Redirigir a la lista de artículos
    return render_template('core/submit_article.html', title=_('Enviar Artículo'), form=form) # type: ignore
@bp.route('/')
def landing_page():
    """
    Muestra la página de bienvenida principal de la aplicación.
    """
    return render_template('core/landing_page.html', title=_('Welcome to VeriFast'))


@bp.route('/articles')
def articles():
    """
    Muestra la pestaña "Últimos Artículos" con una lista paginada.
    """
    page = request.args.get('page', 1, type=int)
    # Se filtran los artículos para mostrar solo aquellos cuyo procesamiento ha sido completado.
    query = select(Article).filter(Article.processing_status == 'complete').order_by(Article.timestamp.desc())
    latest_articles_pagination = (
        db.paginate(query, page=page, per_page=10, error_out=False)
    )
    return render_template('core/articles.html', title=_('Latest Articles'), latest_articles_pagination=latest_articles_pagination)


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


@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Muestra el dashboard de administración. Solo accesible para el usuario con ID 1.
    """
    # Control de acceso de administrador basado en el rol del usuario
    if not current_user.is_admin:
        flash(_('Acceso denegado. Solo los administradores pueden acceder a esta página.'), 'danger')
        return redirect(url_for('core.articles')) # Redirige a la lista de artículos si no es admin

    # Creamos una instancia de EmptyForm para la protección CSRF en el formulario de "fetch-now"
    form = EmptyForm()

    # 1. Obtener un término de búsqueda opcional desde los argumentos de la URL
    query = request.args.get('q', '')
    # 2. Obtener el número de página actual, también de la URL
    page = request.args.get('page', 1, type=int)

    # 3. Construir una consulta base de SQLAlchemy
    stmt = select(Article).order_by(Article.timestamp.desc()) # type: ignore

    # 4. Si hay un término de búsqueda, añadir un filtro
    if query:
        # .ilike es el equivalente en SQLAlchemy para una búsqueda 'icontains' (insensible a mayúsculas)
        stmt = stmt.where(Article.title.ilike(f'%{query}%'))

    # 5. Aplicar la paginación a la consulta final
    articles_pagination = db.paginate(stmt, page=page, per_page=20, error_out=False)

    # 1. Leer los datos de tendencias desde Redis
    trending_tags = []
    try:
        # Asegúrate de que 'celery' esté importado desde 'app.extensions'
        from app.extensions import celery
        redis_client = celery.backend.client
        tags_json = redis_client.get('trending_tags')
        if tags_json:
            trending_tags = json.loads(tags_json)
    except Exception as e:
        current_app.logger.error(f"Error al leer trending_tags de Redis: {e}")

    # 6. Pasar el objeto de paginación, el término de búsqueda y los trending_tags a la plantilla
    return render_template('core/dashboard.html',
                           title=_('Dashboard de Administración'),
                           articles_pagination=articles_pagination,
                           query=query, # type: ignore
                           trending_tags=trending_tags, # type: ignore
                           form=form) # Pasamos la instancia del formulario a la plantilla

@bp.route('/dashboard/fetch-now', methods=['POST'])
@login_required
def fetch_articles_now():
    """
    Fuerza la ejecución de la tarea de búsqueda de nuevos artículos.
    Solo accesible para administradores.
    """
    # Creamos una instancia de EmptyForm para la protección CSRF
    form = EmptyForm()

    if not current_user.is_admin:
        flash(_('Acción no permitida.'), 'danger')
        return redirect(url_for('core.dashboard'))

    # Encolar la tarea de búsqueda de artículos
    from app.tasks import fetch_new_articles_task
    fetch_new_articles_task.delay()

    flash(_('La tarea de búsqueda de artículos ha sido encolada. Los nuevos artículos aparecerán en breve.'), 'info')
    return redirect(url_for('core.dashboard'))

@bp.route('/article/<int:id>/delete', methods=['POST'])
@login_required
def delete_article(id):
    """
    Elimina un artículo de la base de datos.
    Solo accesible para administradores.
    """
    if not current_user.is_admin:
        flash(_('Acción no permitida.'), 'danger')
        return redirect(url_for('core.dashboard'))

    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    flash(_('El artículo ha sido eliminado con éxito.'), 'success')
    return redirect(url_for('core.dashboard'))


@bp.route('/articles/trending')
def trending_articles():
    """
    Muestra la pestaña "Artículos del Momento".
    """
    three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
    
    # Paso 1: Subconsulta para obtener los IDs y el conteo de los artículos en tendencia.
    popular_article_ids_subquery = (
        db.session.query(
            Article.id.label('id'),
            func.count(QuizAttempt.id).label('read_count')
        )
        .join(Article.attempts)  # Se une usando la relación 'attempts' del modelo Article
        .filter(Article.processing_status == 'complete')
        .filter(QuizAttempt.timestamp >= three_days_ago)
        .group_by(Article.id)
        .order_by(func.count(QuizAttempt.id).desc())
        .limit(5)  # Se limita a 5 como se solicitó para la depuración
        .subquery()
    )
    # Paso 2: Consulta principal que usa los IDs de la subconsulta para obtener los objetos Article completos.
    trending_articles = (
        db.session.query(Article)
        .join(popular_article_ids_subquery, Article.id == popular_article_ids_subquery.c.id)
        .order_by(popular_article_ids_subquery.c.read_count.desc())
        .all()
    )
    return render_template('core/trending_articles.html', title=_('Trending Articles'), trending_articles=trending_articles)


@bp.route('/articles/tags')
def explore_tags():
    """
    Muestra la pestaña "Explorar Tags" con una lista de todos los tags.
    """
    # Consulta simplificada para obtener todos los tags, ordenados alfabéticamente.
    # Esto es más robusto para depuración.
    tags = db.session.scalars(select(Tag).order_by(Tag.name.asc())).all()
    # Línea de depuración para ver en la consola si se están obteniendo los tags.
    current_app.logger.info(f"Tags encontrados para la página de exploración: {tags}")
    return render_template('core/explore_tags.html', title=_('Explore Tags'), tags=tags)

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
            # Guardar la velocidad de este intento exitoso como la nueva velocidad actual
            user.current_wpm = wpm_used
            if wpm_used >= user.max_wpm:
                user.max_wpm += 25

            # Lógica de recomendación robusta
            related_article = None
            
            # Subconsulta para obtener todos los IDs de artículos que el usuario ya ha intentado
            attempted_article_ids_subquery = db.session.query(QuizAttempt.article_id).filter(QuizAttempt.user_id == user.id).subquery()

            # 1. Intenta buscar por tags compartidos
            current_tag_ids = [tag.id for tag in article.tags] # type: ignore
            if current_tag_ids: # type: ignore
                related_article = db.session.query(Article).join(Article.tags).filter(
                    Article.processing_status == 'complete', # Solo recomendar artículos listos
                    Tag.id.in_(current_tag_ids), # que comparta al menos un tag
                    Article.id != article.id, # que no sea el artículo actual
                    Article.id.notin_(attempted_article_ids_subquery) # que el usuario no haya intentado
                ).order_by(func.random()).first()

            # 2. Si no se encontró nada, busca cualquier artículo no leído (fallback)
            if not related_article:
                current_app.logger.info(f"Fallback de recomendación para usuario {user.id}: buscando cualquier artículo no leído.")
                related_article = db.session.query(Article).filter(
                    Article.processing_status == 'complete', # Solo recomendar artículos listos
                    Article.id != article.id, # que no sea el artículo actual
                    Article.id.notin_(attempted_article_ids_subquery) # que el usuario no haya intentado
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
    user = current_user
    # La relación 'quiz_attempts' es dinámica, por lo que actúa como un objeto de consulta.
    # Añadimos 'selectinload' para cargar eficientemente los artículos relacionados
    # y evitar múltiples consultas a la base de datos en la plantilla (problema N+1).
    # También se corrige el nombre de la columna de ordenación a 'timestamp'.
    attempts = (
        user.quiz_attempts.options(selectinload(QuizAttempt.article))
        .order_by(QuizAttempt.timestamp.desc())
        .all()
    )

    return render_template(
        'core/profile.html', user=user, attempts=attempts, title="Mi Perfil"
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

    # Validación manual del token CSRF para endpoints JSON
    try:
        validate_csrf(data.get('csrf_token')) # Flask-WTF 1.0+ busca en el JSON por defecto
    except Exception as e:
        # Si la validación falla, se lanza una excepción que podemos capturar.
        return jsonify({'error': 'CSRF token missing or invalid'}), 400

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
    current_app.logger.info(f'Intentando cambiar idioma a: {lang}')

    # 1. Verificar si el idioma es soportado por la aplicación
    if lang in current_app.config.get('LANGUAGES', []):
        # 2. Guardar en la sesión para todos (invitados y registrados)
        session['language'] = lang

        # 3. Guardar en el perfil para usuarios autenticados
        if current_user.is_authenticated:
            current_user.preferred_language = lang
            db.session.commit()

    current_app.logger.info(f"Idioma guardado en sesión: {session.get('language')}")

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