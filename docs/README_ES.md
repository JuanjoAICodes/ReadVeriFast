# Documentación de VeriFast

Bienvenido a la documentación oficial de VeriFast, la plataforma de lectura rápida impulsada por IA.

## Primeros Pasos con VeriFast

¡Bienvenido a VeriFast! Esta guía te ayudará a empezar con el proyecto, ya seas un nuevo usuario o un desarrollador que busca contribuir.

### Para Nuevos Usuarios

VeriFast es una plataforma de lectura rápida impulsada por IA que te ayuda a leer más rápido y comprender más. Aquí te explicamos cómo empezar:

1.  **Crea una cuenta:** Regístrate para obtener una nueva cuenta y comenzar tu viaje de lectura personalizado.
2.  **Encuentra un artículo:** Explora nuestra biblioteca de artículos o envía los tuyos.
3.  **Comienza a leer:** Utiliza nuestro lector de velocidad para leer el artículo al ritmo que desees.
4.  **Haz un cuestionario:** Pon a prueba tu comprensión con nuestros cuestionarios impulsados por IA.
5.  **Gana XP:** Gana puntos de experiencia por tu rendimiento y desbloquea nuevas características.

### Para Desarrolladores

Esta guía te ayudará a configurar tu entorno de desarrollo y a empezar a contribuir en VeriFast.

#### Prerrequisitos

*   Python 3.10+
*   Node.js y npm (para dependencias de frontend)
*   PostgreSQL (para producción)

#### Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone <repository-url>
    cd verifast
    ```

2.  **Crea un entorno virtual:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    npm install
    ```

4.  **Configura la base de datos:**
    ```bash
    python3 manage.py migrate
    ```

5.  **Ejecuta el servidor de desarrollo:**
    ```bash
    python3 manage.py runserver
    ```

Visita `http://localhost:8000` para ver la aplicación en funcionamiento.

#### Claves de API

Necesitarás configurar las claves de API para los siguientes servicios:

*   **API de Google Gemini:** Para la generación de cuestionarios impulsados por IA.
*   **API de Wikipedia:** Para el etiquetado de contenido.

Añade tus claves de API a un archivo `.env` en la raíz del proyecto:

```
GEMINI_API_KEY=your-gemini-api-key
WIKIPEDIA_USER_AGENT=VeriFastApp/1.0
```

#### Despliegue

Para obtener instrucciones sobre cómo desplegar VeriFast en un entorno de producción, consulta nuestra [Guía de Despliegue](../development/README.md).

## Guía de Desarrollo de VeriFast

Esta guía proporciona convenciones y mejores prácticas para desarrollar en la plataforma VeriFast.

### Estilo de Código

El proyecto utiliza `ruff` para el linting y el formateo. Por favor, asegúrate de que tu código se adhiera a las directrices de estilo del proyecto.

*   **Linting y formateo:**
    ```bash
    ruff check .
    ```

### Pruebas

El proyecto utiliza `pytest` para las pruebas. Por favor, añade pruebas para cualquier nueva característica o corrección de errores.

*   **Ejecución de pruebas:**
    ```bash
    pytest
    ```

### Commits

Sigue los estándares de mensajes de commit convencionales.

### Ramas

Crea una nueva rama para cada característica o corrección de errores.

### Dependencias

Usa `pip` para gestionar las dependencias de Python y `npm` para las dependencias de frontend. Todas las dependencias deben añadirse al archivo `requirements.txt` o `package.json` apropiado.

### Arquitectura

VeriFast es una aplicación web basada en Django que utiliza una arquitectura híbrida HTMX para la funcionalidad de lectura rápida con elementos de gamificación, cuestionarios impulsados por IA y características sociales.

#### Principios Fundamentales de la Arquitectura

*   **Enfoque Híbrido HTMX:** Dominio del lado del servidor con un mínimo de JavaScript del lado del cliente.
*   **Pila Tecnológica:** Django, PostgreSQL, HTMX + Alpine.js, Celery con Redis.

Para una explicación más detallada de la arquitectura, consulta la [Guía de Arquitectura del Proyecto](docs/archived/documentation/PROJECT_ARCHITECTURE_GUIDE.md).

## Características de VeriFast

Esta guía proporciona una visión general de todas las características de VeriFast.

### Características Principales

#### Lectura Rápida

*   **Arquitectura Híbrida HTMX:** Un único modo inmersivo para la lectura rápida, con una franja de texto blanca a todo lo ancho.
*   **PPM Configurables:** Ajusta tu velocidad de lectura de 50 a 1000 PPM.

#### Cuestionarios Impulsados por IA

*   **Integración con Google Gemini:** Generación inteligente de cuestionarios.
*   **Dificultad Adaptativa:** Cuestionarios adaptados a la complejidad del contenido.

#### Sistema de Gamificación

*   **Economía de XP:** Gana puntos por tu rendimiento en la lectura y los cuestionarios.
*   **Características Premium:** Gasta XP en personalizaciones y mejoras.

#### Etiquetado Inteligente

*   **Validación de Wikipedia:** Las etiquetas se verifican con Wikipedia.
*   **Descubrimiento de Contenido:** Encuentra artículos por tema.

### Características Sociales

*   **Comentarios:** Comenta en los artículos e interactúa con otros usuarios.
*   **Interacciones con XP:** Gasta XP para comentar e interactuar con los comentarios de otros usuarios.

Para una explicación más detallada de todas las características, consulta el [Documento Maestro de Requisitos del Producto](docs/archived/documentation/MASTER_PRD.md).

## Guía de la API de VeriFast

Esta guía proporciona una visión general de la API de VeriFast.

### Configuración de la API

Para usar la API de VeriFast, necesitarás configurar las claves de API para los siguientes servicios:

*   **API de Google Gemini:** Para la generación de cuestionarios impulsados por IA.
*   **API de Wikipedia:** Para el etiquetado de contenido.

Añade tus claves de API a un archivo `.env` en la raíz del proyecto:

```
GEMINI_API_KEY=your-gemini-api-key
WIKIPEDIA_USER_AGENT=VeriFastApp/1.0
```

### Endpoints

La API de VeriFast proporciona endpoints para lo siguiente:

*   **Autenticación:** Inicio de sesión y registro de usuarios.
*   **Artículos:** Recupera artículos y envía nuevos.
*   **Cuestionarios:** Envía cuestionarios y obtén resultados.
*   **Usuarios:** Gestiona perfiles y configuraciones de usuario.

Para obtener información más detallada sobre la API, consulta la [Guía de Configuración de la API](docs/archived/docs/API_SETUP_GUIDE.md).
