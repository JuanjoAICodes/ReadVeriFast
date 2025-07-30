"""
Management command to create sample multilingual articles for testing language filtering
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from verifast_app.models import Article, Tag
import json


class Command(BaseCommand):
    help = 'Create sample multilingual articles for testing language filtering functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of articles to create per language (default: 10)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Sample English articles
        english_articles = [
            {
                'title': 'The Future of Artificial Intelligence in Education',
                'content': '''Artificial intelligence is revolutionizing the educational landscape in unprecedented ways. From personalized learning experiences to automated grading systems, AI technologies are transforming how students learn and teachers teach. Machine learning algorithms can now analyze student performance patterns to identify areas where individual learners need additional support. This personalized approach ensures that no student is left behind while allowing advanced learners to progress at their own pace. Virtual tutoring systems powered by AI can provide 24/7 assistance to students, answering questions and providing explanations in real-time. Natural language processing enables these systems to understand student queries in plain English and respond with appropriate educational content. Furthermore, AI-driven analytics help educators make data-informed decisions about curriculum design and teaching methodologies. The integration of AI in education also extends to administrative tasks, streamlining processes like enrollment, scheduling, and resource allocation. As we look toward the future, the potential for AI to create more inclusive, accessible, and effective educational experiences continues to grow.''',
                'tags': ['Technology', 'Education', 'Artificial Intelligence'],
                'language': 'en'
            },
            {
                'title': 'Climate Change and Renewable Energy Solutions',
                'content': '''Climate change represents one of the most pressing challenges of our time, requiring immediate and sustained action across all sectors of society. The transition to renewable energy sources has emerged as a critical component in the global effort to reduce greenhouse gas emissions and mitigate the effects of global warming. Solar power technology has advanced significantly in recent years, with photovoltaic cells becoming more efficient and cost-effective. Wind energy has also seen remarkable growth, with offshore wind farms generating substantial amounts of clean electricity. Hydroelectric power continues to play a vital role in many countries' energy portfolios, while emerging technologies like geothermal and tidal energy offer additional sustainable alternatives. The development of energy storage systems, particularly advanced battery technologies, is crucial for managing the intermittent nature of renewable energy sources. Smart grid technologies enable better integration of renewable energy into existing power infrastructure, optimizing distribution and reducing waste. Government policies and incentives play a crucial role in accelerating the adoption of renewable energy technologies. International cooperation and knowledge sharing are essential for developing countries to leapfrog traditional fossil fuel-based energy systems and adopt clean energy solutions from the outset.''',
                'tags': ['Environment', 'Climate Change', 'Renewable Energy'],
                'language': 'en'
            },
            {
                'title': 'The Psychology of Effective Learning Strategies',
                'content': '''Understanding how the human brain processes and retains information is fundamental to developing effective learning strategies. Cognitive psychology research has revealed numerous insights into the mechanisms of memory formation, attention, and knowledge acquisition. The spacing effect demonstrates that distributed practice over time leads to better long-term retention compared to massed practice or cramming. Active recall, the practice of retrieving information from memory without looking at source materials, has been shown to strengthen neural pathways and improve retention. Elaborative interrogation, which involves asking "why" and "how" questions about the material being studied, helps create meaningful connections between new information and existing knowledge. The testing effect reveals that taking practice tests not only assesses learning but actually enhances it through the retrieval process. Interleaving, or mixing different types of problems or topics during study sessions, improves the ability to discriminate between concepts and apply knowledge flexibly. Dual coding theory suggests that information processed through both verbal and visual channels is more likely to be remembered. Metacognition, or thinking about thinking, enables learners to monitor their understanding and adjust their strategies accordingly. These evidence-based learning strategies can be applied across various educational contexts to improve academic performance and lifelong learning outcomes.''',
                'tags': ['Psychology', 'Education', 'Learning'],
                'language': 'en'
            },
            {
                'title': 'Advances in Medical Technology and Healthcare',
                'content': '''The healthcare industry is experiencing a technological revolution that is transforming patient care, medical research, and healthcare delivery systems worldwide. Telemedicine has emerged as a game-changing innovation, enabling remote consultations and monitoring that improve access to healthcare services, particularly in underserved areas. Wearable devices and Internet of Things (IoT) sensors continuously collect vital health data, allowing for proactive health management and early detection of potential medical issues. Artificial intelligence and machine learning algorithms are being deployed to analyze medical imaging, assist in diagnosis, and predict patient outcomes with remarkable accuracy. Robotic surgery systems provide surgeons with enhanced precision and control, leading to minimally invasive procedures with faster recovery times. Gene therapy and CRISPR technology offer unprecedented opportunities to treat genetic disorders at their source. Personalized medicine, based on individual genetic profiles and biomarkers, enables tailored treatment plans that are more effective and have fewer side effects. 3D printing technology is revolutionizing the production of prosthetics, implants, and even bioprinted tissues and organs. Electronic health records and blockchain technology are improving data security and interoperability across healthcare systems. These technological advances are not only improving patient outcomes but also reducing healthcare costs and making quality medical care more accessible to populations around the globe.''',
                'tags': ['Healthcare', 'Technology', 'Medicine'],
                'language': 'en'
            },
            {
                'title': 'The Impact of Social Media on Modern Communication',
                'content': '''Social media platforms have fundamentally altered the way humans communicate, share information, and maintain relationships in the digital age. These platforms have democratized information sharing, allowing individuals to broadcast their thoughts, experiences, and expertise to global audiences instantly. The real-time nature of social media has accelerated the pace of communication and news dissemination, enabling rapid response to events and facilitating social movements and activism. However, this speed of communication has also contributed to the spread of misinformation and the creation of echo chambers where users are primarily exposed to information that confirms their existing beliefs. The psychological effects of social media usage have become a subject of intense research, with studies examining the relationship between social media engagement and mental health outcomes. The concept of social comparison has been amplified by curated online personas, potentially leading to decreased self-esteem and increased anxiety among users. Privacy concerns have emerged as a significant issue, with users often unaware of how their personal data is collected, stored, and utilized by platform operators and third parties. The influence of social media on political discourse and democratic processes has become increasingly apparent, raising questions about the role of these platforms in shaping public opinion and electoral outcomes. Despite these challenges, social media continues to provide valuable opportunities for education, business networking, creative expression, and maintaining connections across geographical boundaries.''',
                'tags': ['Social Media', 'Communication', 'Technology'],
                'language': 'en'
            }
        ]

        # Sample Spanish articles
        spanish_articles = [
            {
                'title': 'La Revolución de la Inteligencia Artificial en la Medicina',
                'content': '''La inteligencia artificial está transformando radicalmente el campo de la medicina, ofreciendo nuevas posibilidades para el diagnóstico, tratamiento y prevención de enfermedades. Los algoritmos de aprendizaje automático pueden analizar grandes cantidades de datos médicos para identificar patrones que podrían pasar desapercibidos para los profesionales de la salud humanos. En el área de diagnóstico por imágenes, la IA ha demostrado una precisión excepcional en la detección de cáncer, enfermedades cardíacas y trastornos neurológicos. Los sistemas de IA pueden procesar radiografías, tomografías computarizadas y resonancias magnéticas en segundos, proporcionando análisis detallados que ayudan a los médicos a tomar decisiones más informadas. La medicina personalizada se beneficia enormemente de la IA, ya que puede analizar el perfil genético de un paciente junto con su historial médico para recomendar tratamientos específicos. Los chatbots médicos y asistentes virtuales están mejorando el acceso a la atención médica, especialmente en áreas rurales donde los especialistas son escasos. La cirugía robótica asistida por IA permite procedimientos más precisos y menos invasivos. Sin embargo, la implementación de la IA en medicina también plantea desafíos éticos y regulatorios que deben abordarse cuidadosamente para garantizar la seguridad del paciente y la privacidad de los datos.''',
                'tags': ['Medicina', 'Inteligencia Artificial', 'Tecnología'],
                'language': 'es'
            },
            {
                'title': 'Sostenibilidad Ambiental y Energías Renovables',
                'content': '''La sostenibilidad ambiental se ha convertido en una prioridad global urgente, impulsando la transición hacia fuentes de energía renovables y prácticas más ecológicas. La energía solar ha experimentado un crecimiento exponencial, con paneles fotovoltaicos cada vez más eficientes y económicos que se instalan en hogares, empresas y grandes plantas de energía. La energía eólica, tanto terrestre como marina, está contribuyendo significativamente a la matriz energética de muchos países, aprovechando los vientos constantes para generar electricidad limpia. La energía hidroeléctrica sigue siendo una fuente importante de energía renovable, mientras que tecnologías emergentes como la energía geotérmica y mareomotriz ofrecen nuevas oportunidades. El desarrollo de sistemas de almacenamiento de energía, especialmente baterías de ión-litio y otras tecnologías avanzadas, es crucial para gestionar la naturaleza intermitente de las fuentes renovables. Las redes inteligentes permiten una mejor integración de la energía renovable en la infraestructura existente, optimizando la distribución y reduciendo el desperdicio. Los vehículos eléctricos están ganando popularidad como una alternativa sostenible al transporte tradicional basado en combustibles fósiles. Las políticas gubernamentales y los incentivos económicos desempeñan un papel fundamental en acelerar la adopción de tecnologías limpias y promover la inversión en infraestructura sostenible.''',
                'tags': ['Medio Ambiente', 'Energía Renovable', 'Sostenibilidad'],
                'language': 'es'
            },
            {
                'title': 'La Educación Digital en la Era Post-Pandemia',
                'content': '''La pandemia de COVID-19 aceleró dramáticamente la adopción de tecnologías educativas digitales, transformando permanentemente el panorama educativo global. Las plataformas de aprendizaje en línea se convirtieron en herramientas esenciales, permitiendo la continuidad educativa durante los confinamientos y demostrando el potencial del aprendizaje remoto. Los sistemas de gestión del aprendizaje (LMS) evolucionaron para ofrecer experiencias más interactivas y personalizadas, incorporando elementos de gamificación y realidad virtual. La educación híbrida, que combina la enseñanza presencial con componentes digitales, ha emergido como un modelo preferido que ofrece flexibilidad tanto a estudiantes como a educadores. Las herramientas de colaboración digital han facilitado el trabajo en equipo y los proyectos grupales, incluso cuando los estudiantes están físicamente separados. La inteligencia artificial está siendo utilizada para crear tutores virtuales personalizados que se adaptan al ritmo y estilo de aprendizaje de cada estudiante. Los recursos educativos abiertos (REA) han democratizado el acceso al conocimiento, proporcionando materiales de alta calidad de forma gratuita. Sin embargo, la brecha digital ha puesto de manifiesto las desigualdades en el acceso a la tecnología y la conectividad a internet, especialmente en comunidades desfavorecidas. Los educadores han tenido que desarrollar nuevas competencias digitales y adaptar sus metodologías pedagógicas para el entorno virtual.''',
                'tags': ['Educación', 'Tecnología Digital', 'Aprendizaje'],
                'language': 'es'
            },
            {
                'title': 'Innovaciones en Biotecnología y Medicina Personalizada',
                'content': '''La biotecnología moderna está revolucionando la medicina a través de innovaciones que permiten tratamientos más precisos y efectivos basados en las características individuales de cada paciente. La secuenciación del genoma humano ha abierto nuevas posibilidades para comprender las bases genéticas de las enfermedades y desarrollar terapias dirigidas. La tecnología CRISPR-Cas9 permite la edición genética con una precisión sin precedentes, ofreciendo esperanza para el tratamiento de enfermedades genéticas hereditarias. Los biomarcadores están siendo utilizados para identificar pacientes que responderán mejor a tratamientos específicos, reduciendo los efectos secundarios y mejorando los resultados clínicos. La inmunoterapia ha transformado el tratamiento del cáncer al aprovechar el sistema inmunológico del propio cuerpo para combatir las células cancerosas. Las terapias celulares, incluyendo las células madre y las células CAR-T, están mostrando resultados prometedores en el tratamiento de diversas condiciones médicas. La medicina regenerativa utiliza tejidos y órganos cultivados en laboratorio para reemplazar o reparar estructuras dañadas del cuerpo. Los dispositivos médicos inteligentes y los biosensores permiten el monitoreo continuo de parámetros de salud, facilitando la detección temprana de problemas médicos. La farmacogenómica estudia cómo los genes afectan la respuesta de una persona a los medicamentos, permitiendo la prescripción de dosis y tipos de medicamentos más apropiados.''',
                'tags': ['Biotecnología', 'Medicina Personalizada', 'Genética'],
                'language': 'es'
            },
            {
                'title': 'El Futuro del Trabajo en la Era de la Automatización',
                'content': '''La automatización y la inteligencia artificial están redefiniendo el mercado laboral global, creando tanto oportunidades como desafíos para trabajadores y empleadores. Los robots industriales y los sistemas automatizados están asumiendo tareas repetitivas y peligrosas, mejorando la eficiencia y la seguridad en el lugar de trabajo. Sin embargo, esta transformación también está desplazando ciertos tipos de empleos, particularmente aquellos que involucran tareas rutinarias y predecibles. Las habilidades digitales se han vuelto esenciales en prácticamente todos los sectores, requiriendo que los trabajadores se adapten continuamente a nuevas tecnologías. El trabajo remoto, acelerado por la pandemia, ha demostrado que muchas funciones pueden realizarse efectivamente desde cualquier ubicación con conectividad a internet. La economía gig y el trabajo freelance están creciendo, ofreciendo mayor flexibilidad pero también menos seguridad laboral tradicional. Las empresas están invirtiendo en programas de recapacitación y mejora de habilidades para ayudar a sus empleados a adaptarse a los cambios tecnológicos. La colaboración entre humanos y máquinas está emergiendo como un modelo donde la tecnología amplifica las capacidades humanas en lugar de reemplazarlas completamente. Los gobiernos están explorando políticas como la renta básica universal para abordar el desempleo tecnológico. La educación continua y el aprendizaje permanente se han vuelto cruciales para mantener la relevancia profesional en un mundo laboral en constante evolución.''',
                'tags': ['Trabajo', 'Automatización', 'Futuro'],
                'language': 'es'
            }
        ]

        # Create English articles
        self.stdout.write(f'Creating {count} English articles...')
        for i in range(count):
            article_data = english_articles[i % len(english_articles)]
            
            article = Article.objects.create(
                title=f"{article_data['title']} - Sample {i+1}",
                content=article_data['content'],
                url=f"https://example.com/en/article-{i+1}",
                language=article_data['language'],
                processing_status='complete',
                word_count=len(article_data['content'].split()),
                timestamp=timezone.now(),
                acquisition_source='sample_data',
                quiz_data=json.dumps({
                    "questions": [
                        {
                            "question": f"What is the main topic of this article about {article_data['tags'][0].lower()}?",
                            "options": [
                                f"The importance of {article_data['tags'][0].lower()}",
                                "Historical perspectives",
                                "Future predictions",
                                "Technical specifications"
                            ],
                            "answer": f"The importance of {article_data['tags'][0].lower()}",
                            "explanation": f"The article focuses on the significance and impact of {article_data['tags'][0].lower()}."
                        }
                    ]
                })
            )
            
            # Add tags
            for tag_name in article_data['tags']:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'language': article_data['language']}
                )
                article.tags.add(tag)

        # Create Spanish articles
        self.stdout.write(f'Creating {count} Spanish articles...')
        for i in range(count):
            article_data = spanish_articles[i % len(spanish_articles)]
            
            article = Article.objects.create(
                title=f"{article_data['title']} - Muestra {i+1}",
                content=article_data['content'],
                url=f"https://example.com/es/articulo-{i+1}",
                language=article_data['language'],
                processing_status='complete',
                word_count=len(article_data['content'].split()),
                timestamp=timezone.now(),
                acquisition_source='sample_data',
                quiz_data=json.dumps({
                    "questions": [
                        {
                            "question": f"¿Cuál es el tema principal de este artículo sobre {article_data['tags'][0].lower()}?",
                            "options": [
                                f"La importancia de {article_data['tags'][0].lower()}",
                                "Perspectivas históricas",
                                "Predicciones futuras",
                                "Especificaciones técnicas"
                            ],
                            "answer": f"La importancia de {article_data['tags'][0].lower()}",
                            "explanation": f"El artículo se centra en la importancia e impacto de {article_data['tags'][0].lower()}."
                        }
                    ]
                })
            )
            
            # Add tags
            for tag_name in article_data['tags']:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'language': article_data['language']}
                )
                article.tags.add(tag)

        total_created = count * 2
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {total_created} sample articles '
                f'({count} English, {count} Spanish) with language filtering support!'
            )
        )