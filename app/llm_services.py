# En llm_services.py
from __future__ import annotations

import google.generativeai as genai
import json
from flask import current_app
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Article

def generate_quiz_from_text(article: "Article") -> dict | None:
    """
    Genera un cuestionario de comprensión a partir de un texto usando la API de Gemini.
    """
    try:
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            current_app.logger.error("La clave GEMINI_API_KEY no está configurada.")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Lógica para determinar el idioma del prompt
        if article.language == 'es':
            idioma_instruccion = "en español"
        else:
            # Por defecto, para 'en' o cualquier otro idioma, generamos en inglés
            idioma_instruccion = "in English"

        prompt = f"""
        Basado en el siguiente texto, genera un cuestionario de comprensión y una lista de 3 a 5 etiquetas (tags) relevantes.
        El objetivo es evaluar si alguien ha entendido los puntos clave del artículo y categorizarlo.
        El formato de salida DEBE ser un objeto JSON válido, sin ningún texto o explicación adicional antes o después.
        La estructura del JSON debe ser la siguiente:
        {{
          "tags": ["tag1", "tag2", "tag3"],
          "questions": [
            {{
              "question": "Texto de la pregunta 1",
              "options": ["Opción A", "Opción B", "Opción C"],
              "answer": "La opción correcta exacta como aparece en la lista de opciones"
            }}
          ]
        }}
        IMPORTANTE: Todo el contenido generado (preguntas, opciones, respuestas y tags) debe estar estrictamente {idioma_instruccion}.
        Asegúrate de que el valor de "answer" en cada pregunta coincida exactamente con uno de los strings en su lista de "options".
        Texto del artículo:
        ---
        {article.raw_content}
        ---
        """

        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```")

        return json.loads(cleaned_text)

    except Exception as e:
        # Usamos el logger de la aplicación en lugar de print
        current_app.logger.error(f"Error al generar el cuestionario con Gemini: {e}")
        return None