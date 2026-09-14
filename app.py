"""
QuakeMind Global - Hugging Face Space Application
Author: Fabio Ignacio Torres Benítez (Psychologist & Data / AI Engineer)
License: MIT
"""

import os
import sys
import pandas as pd
import gradio as gr

# Ensure local imports work
sys.path.insert(0, os.path.dirname(__file__))

from quakemind_engine import (
    fetch_global_earthquakes,
    compute_perceived_shaking,
    get_pap_guidance,
    evaluate_structural_safety,
    debunk_seismic_myth,
    get_mmi_description,
    haversine_distance,
    hypocentral_distance,
    calculate_attenuation_mmi
)
from i18n import get_text, TRANSLATIONS

# Pre-defined global seismic hot-spot reference cities
GLOBAL_CITIES = {
    "Cali / Buenaventura, Colombia": (3.4516, -76.5320),
    "Bogotá, Colombia": (4.7110, -74.0721),
    "Caracas, Venezuela": (10.4806, -66.9036),
    "Mexico City, Mexico": (19.4326, -99.1332),
    "Santiago, Chile": (-33.4489, -70.6693),
    "Lima, Peru": (-12.0464, -77.0428),
    "Quito, Ecuador": (-0.1807, -78.4678),
    "San Francisco / Bay Area, USA": (37.7749, -122.4194),
    "Los Angeles, California, USA": (34.0522, -118.2437),
    "Tokyo, Japan": (35.6762, 139.6503),
    "Istanbul, Turkey": (41.0082, 28.9784),
    "Jakarta, Indonesia": (-6.2088, 106.8456),
    "Naples / Southern Italy": (40.8518, 14.2681),
    "Athens, Greece": (37.9838, 23.7275),
    "Christchurch, New Zealand": (-43.5321, 172.6362)
}


# =====================================================================
# GRADIO CONTROLLER FUNCTIONS
# =====================================================================

def update_feed_quakes(feed_key: str):
    """Fetch live USGS earthquakes and format dropdown choices and table."""
    quakes = fetch_global_earthquakes(feed_key)
    
    if not quakes:
        return gr.update(choices=["No earthquakes found"]), pd.DataFrame()
        
    choices = [f"[{q['mag']} {q['mag_type']}] {q['title']} ({q['time_iso']})" for q in quakes]
    
    df_data = []
    for q in quakes:
        df_data.append({
            "Mag": q["mag"],
            "Location": q["place"],
            "Depth (km)": q["depth_km"],
            "Time (UTC)": q["time_iso"],
            "Alert Level": q["alert"].upper(),
            "Felt Reports": q["felt"],
            "Lat": q["lat"],
            "Lon": q["lon"]
        })
    df = pd.DataFrame(df_data)
    
    return gr.update(choices=choices, value=choices[0] if choices else None), df


def on_city_selected(city_name: str):
    """Autofill latitude and longitude when a reference city is chosen."""
    if city_name in GLOBAL_CITIES:
        lat, lon = GLOBAL_CITIES[city_name]
        return lat, lon
    return 3.4516, -76.5320


def calculate_impact_ui(selected_quake_str: str, user_lat: float, user_lon: float, feed_key: str, lang: str):
    """Calculates ground motion attenuation and generates the perceived shaking report."""
    if not selected_quake_str:
        return "⚠️ Please select an earthquake from the list first."
        
    quakes = fetch_global_earthquakes(feed_key)
    
    # Match the selected earthquake by string or fallback to first
    target_q = None
    for q in quakes:
        q_str = f"[{q['mag']} {q['mag_type']}] {q['title']} ({q['time_iso']})"
        if q_str == selected_quake_str:
            target_q = q
            break
            
    if not target_q and quakes:
        target_q = quakes[0]

    if not target_q:
        return "No earthquake data available."

    report = compute_perceived_shaking(user_lat, user_lon, target_q, lang=lang)

    # HTML Card layout
    is_es = (lang == "es")
    
    html = f"""
    <div style="background: #1e293b; color: #f8fafc; border-radius: 12px; padding: 24px; border-left: 8px solid {report['color_hex']}; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="margin: 0; color: #f8fafc; font-size: 1.3rem;">{report['earthquake_title']}</h3>
            <span style="background: {report['color_hex']}; color: #000; font-weight: 800; padding: 6px 14px; border-radius: 20px; font-size: 1.1rem;">
                {report['mmi_title']}
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px;">
            <div style="background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155;">
                <div style="font-size: 0.8rem; color: #94a3b8;">{'Distancia al Epicentro' if is_es else 'Distance to Epicenter'}</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #38bdf8;">{report['epicentral_dist_km']} km</div>
            </div>
            <div style="background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155;">
                <div style="font-size: 0.8rem; color: #94a3b8;">{'Profundidad Hipocentral' if is_es else 'Focal Depth'}</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #38bdf8;">{report['depth_km']} km</div>
            </div>
            <div style="background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155;">
                <div style="font-size: 0.8rem; color: #94a3b8;">{'Distancia 3D (Hipocentro)' if is_es else '3D Slant Distance'}</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #38bdf8;">{report['hypocentral_dist_km']} km</div>
            </div>
            <div style="background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155;">
                <div style="font-size: 0.8rem; color: #94a3b8;">{'Aceleración Estimada' if is_es else 'Estimated Intensity'}</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: {report['color_hex']};">MMI {report['mmi_estimated']} / 12</div>
            </div>
        </div>

        <div style="margin-bottom: 14px;">
            <h4 style="margin: 0 0 6px 0; color: #38bdf8; font-size: 1rem;">
                {'🧠 Percepción Humana en tu Ubicación:' if is_es else '🧠 Human Perception at Your Location:'}
            </h4>
            <p style="margin: 0; font-size: 1.05rem; line-height: 1.5; color: #e2e8f0;">
                {report['human_perception']}
            </p>
        </div>

        <div>
            <h4 style="margin: 0 0 6px 0; color: #fcd34d; font-size: 1rem;">
                {'🏗️ Riesgo Estructural Estimado (Norma Sismorresistente):' if is_es else '🏗️ Estimated Structural Risk:'}
            </h4>
            <p style="margin: 0; font-size: 1rem; line-height: 1.5; color: #cbd5e1;">
                {report['structural_risk']}
            </p>
        </div>
    </div>
    """
    return html


def run_structural_triage_ui(element: str, crack_type: str, gas_water: str, lang: str):
    """Evaluates ATC-20 citizen safety and generates actionable steps."""
    has_gas = (gas_water == "gas_yes")
    res = evaluate_structural_safety(element, crack_type, has_gas, lang=lang)

    is_es = (lang == "es")
    actions_html = "".join([f"<li style='margin-bottom: 6px;'>{a}</li>" for a in res["action_steps"]])

    html = f"""
    <div style="background: #1e293b; color: #f8fafc; border-radius: 12px; padding: 24px; border: 2px solid {res['color_hex']}; margin-top: 12px;">
        <h3 style="color: {res['color_hex']}; margin-top: 0; font-size: 1.3rem;">{res['title']}</h3>
        <p style="font-size: 1.1rem; font-weight: bold; margin-bottom: 16px; color: #f1f5f9;">
            {res['recommendation']}
        </p>
        <h4 style="color: #38bdf8; margin-bottom: 8px;">
            {'Pasos Inmediatos de Seguridad:' if is_es else 'Immediate Safety Action Plan:'}
        </h4>
        <ul style="padding-left: 20px; font-size: 0.95rem; line-height: 1.6; color: #cbd5e1;">
            {actions_html}
        </ul>
    </div>
    """
    return html


def run_mythbuster_ui(user_claim: str, lang: str):
    """Runs the NLP seismic fact-checker."""
    if not user_claim.strip():
        return "⚠️ Por favor ingresa una afirmación, rumor o pregunta sísmica." if lang == "es" else "⚠️ Please enter a seismic claim, rumor, or question."
        
    res = debunk_seismic_myth(user_claim, lang=lang)
    is_es = (lang == "es")

    html = f"""
    <div style="background: #1e293b; color: #f8fafc; border-radius: 12px; padding: 24px; border-left: 6px solid #38bdf8; margin-top: 12px;">
        <div style="font-size: 1.25rem; font-weight: 800; margin-bottom: 8px; color: #f43f5e;">
            {res['verdict']}
        </div>
        <div style="font-size: 0.95rem; color: #94a3b8; margin-bottom: 16px;">
            <strong>{'Tema Analizado:' if is_es else 'Topic Analyzed:'}</strong> {res['myth_topic']}
        </div>
        <div style="margin-bottom: 16px;">
            <h4 style="color: #38bdf8; margin: 0 0 6px 0;">{'Fundamento Geofísico y Científico:' if is_es else 'Scientific & Geophysical Fact:'}</h4>
            <p style="margin: 0; font-size: 1.05rem; line-height: 1.6; color: #e2e8f0;">
                {res['scientific_fact']}
            </p>
        </div>
        <div style="background: #0f172a; padding: 12px 16px; border-radius: 8px; border: 1px solid #334155;">
            <strong style="color: #22c55e;">{'Conducta Recomendada:' if is_es else 'Recommended Action:'}</strong>
            <span style="color: #cbd5e1;"> {res['action']}</span>
        </div>
    </div>
    """
    return html


# =====================================================================
# GRADIO APPLICATION INTERFACE
# =====================================================================

custom_css = """
#main-header { text-align: center; margin-bottom: 10px; }
.gradio-container { max-width: 1100px !important; margin: auto !important; }
"""

with gr.Blocks(title="QuakeMind Global - Seismic Intelligence and Crisis Hub") as demo:
    
    with gr.Row(elem_id="main-header"):
        with gr.Column():
            gr.Markdown("""
            # 🌐 QuakeMind Global *(SismoMente Global)*
            ### Real-Time Global Seismic Intelligence, Psychological First Aid (PAP) & Zero-Network Survival Hub
            *Created by **Fabio Ignacio Torres Benítez** (Psychologist & Data / AI Engineer) • 100% Free & Open Source (MIT License)*
            """)
            lang_radio = gr.Radio(choices=["es", "en"], value="es", label="Idioma / Language", interactive=True)

    # -------------------------------------------------------------
    # TAB 1: GLOBAL LIVE SEISMIC RADAR & SHAKING ESTIMATOR
    # -------------------------------------------------------------
    with gr.Tab("🌍 Monitor Sísmico Global & Aceleración Local"):
        gr.Markdown("""
        ### 📡 Radar de Sismicidad en Vivo & Calculadora de Impacto Humano (MMI)
        Conexión directa a los feeds globales del **USGS (United States Geological Survey)**. 
        Calcula la **Intensidad Mercalli Modificada (MMI)** en tu ciudad exacta mediante ecuaciones empíricas de atenuación de ondas sísmicas (*GMPE*).
        """)

        with gr.Row():
            feed_select = gr.Dropdown(
                choices=[
                    ("Últimas 24 Horas (Magnitud 4.5+ Global)", "day_45"),
                    ("Última Hora (Todos los sismos)", "hour"),
                    ("Últimas 24 Horas (Todos los sismos)", "day_all"),
                    ("Último Mes (Sismos Significativos Mundiales)", "month_sig")
                ],
                value="day_45",
                label="Fuente Sísmica en Tiempo Real",
                interactive=True
            )
            refresh_feed_btn = gr.Button("🔄 Actualizar Datos USGS", variant="secondary")

        quake_dropdown = gr.Dropdown(choices=[], label="Selecciona un Sismo de la Lista Global", interactive=True)

        with gr.Accordion("📍 Ubicación del Observador / Tu Ciudad", open=True):
            with gr.Row():
                city_preset = gr.Dropdown(
                    choices=list(GLOBAL_CITIES.keys()),
                    value="Cali / Buenaventura, Colombia",
                    label="O selecciona una ciudad sísmica de referencia",
                    interactive=True
                )
            with gr.Row():
                lat_input = gr.Number(value=3.4516, label="Latitud (ej: 3.4516)", interactive=True)
                lon_input = gr.Number(value=-76.5320, label="Longitud (ej: -76.5320)", interactive=True)

        calc_btn = gr.Button("⚡ Calcular Aceleración e Impacto Percibido (MMI)", variant="primary")
        impact_output = gr.HTML(label="Resultado de Impacto Humano")

        with gr.Accordion("📋 Tabla Completa de Sismos Recientes", open=False):
            quakes_table = gr.DataFrame(headers=["Mag", "Location", "Depth", "Time", "Alert", "Felt", "Lat", "Lon"])

    # -------------------------------------------------------------
    # TAB 2: PSYCHOLOGICAL FIRST AID (PAP) & AUTONOMIC VAGAL PACER
    # -------------------------------------------------------------
    with gr.Tab("🧠 Primeros Auxilios Psicológicos (PAP)"):
        gr.Markdown("""
        ### 🫁 Manejo del Pánico Agudo y Estabilización Neurocognitiva
        *Protocolo clínico diseñado bajo estándares de la Organización Mundial de la Salud (OMS) y el modelo de crisis ABCDE.*
        En un sismo, el mayor número de accidentes graves ocurre por estampidas, bloqueos y desmayos por hiperventilación.
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("""
                #### 🫁 Marcapasos de Suspiro Cíclico (4-4-7)
                *Activa el nervio vago y reduce el cortisol en 60 segundos.*
                1. **Inhala** profundamente por la nariz durante **4 segundos** (inflando el abdomen).
                2. **Retén** el aire durante **4 segundos**.
                3. **Exhala** lentamente por la boca entreabierta durante **7 segundos**.
                *Repite este ciclo 4 veces seguidas.*
                """)
                gr.HTML("""
                <div style="text-align: center; padding: 20px; background: #0f172a; border-radius: 12px; border: 2px dashed #38bdf8;">
                    <div style="font-size: 2.5rem; font-weight: bold; color: #38bdf8; margin-bottom: 8px;">4 - 4 - 7</div>
                    <p style="color: #94a3b8; font-size: 0.9rem;">Sigue este ritmo con la mano sobre el estómago para calmar taquicardias y temblores motores.</p>
                </div>
                """)

            with gr.Column(scale=2):
                gr.Markdown("""
                #### 📋 Protocolo ABCDE de Intervención en Crisis:
                * **A - Escucha Activa & Grounding (5-4-3-2-1):** Nombra 5 cosas que ves, toca 4 texturas, escucha 3 sonidos, siente 2 olores y evoca 1 pensamiento de calma.
                * **B - Reentrenamiento de la Respiración:** Respiración diafragmática para evitar la alcalosis respiratoria y el desmayo.
                * **C - Categorización de Necesidades:** Aislar problemas: 1° Heridas graves, 2° Fuga de gas, 3° Estructura. Todo lo demás espera.
                * **D - Derivación y Comunicación:** Un solo SMS o mensaje de texto breve. NO saturar las redes celulares con llamadas ni videos.
                * **E - Psicoeducación:** Comprender que temblar involuntariamente en las piernas tras el sismo es la descarga biológica normal de adrenalina.
                """)

    # -------------------------------------------------------------
    # TAB 3: STRUCTURAL DAMAGE TRIAGE (ATC-20)
    # -------------------------------------------------------------
    with gr.Tab("🏗️ Triaje de Grietas y Seguridad del Hogar (ATC-20)"):
        gr.Markdown("""
        ### 🔍 Asistente de Evaluación Rápida Post-Sismo (Estándar ATC-20 / NSR-10 / COVENIN)
        Responde las siguientes 3 preguntas para saber si tu vivienda es segura para habitar o si debes evacuar de inmediato.
        """)

        with gr.Row():
            elem_dropdown = gr.Dropdown(
                choices=[
                    ("Pared Divisoria / Muro de Ladrillo o Drywall", "elem_wall"),
                    ("Columna o Pilar Principal de Concreto", "elem_column"),
                    ("Viga Horizontal de Concreto o Techo", "elem_beam"),
                    ("Losa de Piso o Pavimento", "elem_floor")
                ],
                value="elem_wall",
                label="¿Dónde se encuentra el daño principal?",
                interactive=True
            )

            crack_dropdown = gr.Dropdown(
                choices=[
                    ("Fisura superficial / cabello (< 1-2 mm, solo pintura/estuco)", "crack_hairline"),
                    ("Grieta horizontal o vertical en juntas de mampostería (2-5 mm)", "crack_horizontal"),
                    ("Grieta diagonal en 'X' (45 grados) atravesando concreto", "crack_diagonal"),
                    ("Desprendimiento severo de concreto con varillas de hierro expuestas", "crack_spalling"),
                    ("Inclinación visible de la estructura o descuadre de marcos", "crack_tilt")
                ],
                value="crack_hairline",
                label="¿Qué forma tiene la grieta?",
                interactive=True
            )

            utility_dropdown = gr.Dropdown(
                choices=[
                    ("No se detecta daño en servicios", "gas_no"),
                    ("Sí: Olor a gas, chispas eléctricas o tubería rota de agua", "gas_yes")
                ],
                value="gas_no",
                label="¿Hay fugas de servicios públicos?",
                interactive=True
            )

        triage_btn = gr.Button("🛡️ Evaluar Nivel de Seguridad de la Estructura", variant="primary")
        triage_output = gr.HTML(label="Diagnóstico de Seguridad Estructural")

    # -------------------------------------------------------------
    # TAB 4: SEISMIC MYTH-BUSTER & FACT-CHECKER
    # -------------------------------------------------------------
    with gr.Tab("🔍 Cazador de Mitos y Desinformación"):
        gr.Markdown("""
        ### 🔬 Verificador Científico de Rumores y Cadenas Virales
        Ingresa un texto, audio transcrito o mensaje de redes sociales para obtener un dictamen científico inmediato.
        """)

        myth_input = gr.Textbox(
            lines=2,
            placeholder="Ejemplo: 'Predijeron un terremoto de 9.0 para hoy a las 6 pm' o 'hace mucho calor, seguro va a temblar'",
            label="Mensaje, rumor o afirmación a verificar"
        )
        
        with gr.Row():
            ex1 = gr.Button("Ej: 'Predijeron terremoto a las 6 PM'", size="sm")
            ex2 = gr.Button("Ej: 'El calor produce temblores'", size="sm")
            ex3 = gr.Button("Ej: 'Los animales predicen horas antes'", size="sm")
            ex4 = gr.Button("Ej: 'El triángulo de la vida'", size="sm")

        check_myth_btn = gr.Button("🔬 Verificar Científicamente", variant="primary")
        myth_output = gr.HTML(label="Dictamen Científico")

        ex1.click(lambda: "Predijeron un terremoto de 8.5 para hoy a las 6 pm", outputs=myth_input)
        ex2.click(lambda: "Hace demasiado calor y bochorno, seguro hoy va a temblar", outputs=myth_input)
        ex3.click(lambda: "Los perros y gatos saben horas antes que va a temblar", outputs=myth_input)
        ex4.click(lambda: "Debo usar el triángulo de la vida en vez de cubrirme", outputs=myth_input)

    # -------------------------------------------------------------
    # TAB 5: OFFLINE PWA & SURVIVAL BEACON
    # -------------------------------------------------------------
    with gr.Tab("📡 PWA de Supervivencia Offline (Sin Internet)"):
        gr.Markdown("""
        ### 🚨 Aplicación Web Progresiva (PWA) de Emergencia Total
        Cuando tiembla fuerte, las torres celulares colapsan. Por eso diseñamos la PWA **QuakeMind Offline**:
        
        * 🔊 **Silbato Acústico de Rescate SOS (3.500 Hz):** Sintetiza en tu celular un tono puro penetrante en código Morse (`... --- ...`) mediante *Web Audio API* para alertar a brigadas de rescate sin agotar tu garganta.
        * 🔦 **Baliza Estroboscópica de Pantalla:** Destellos de alto contraste para visibilidad nocturna.
        * 🎒 **Mochila de las 72 Horas:** Checklist interactivo que se guarda en la memoria de tu teléfono.
        * 💳 **Tarjeta de Emergencia Familiar:** Genera y descarga una imagen PNG de identificación sin internet.
        
        #### 👉 Cómo usar la PWA:
        Abre el archivo `pwa/index.html` en cualquier navegador móvil (Chrome/Safari) y pulsa **"Agregar a Pantalla de Inicio"**. Funcionará al 100% incluso en modo avión.
        """)
        
        gr.HTML("""
        <div style="background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; text-align: center;">
            <p style="font-size: 1.1rem; color: #38bdf8; font-weight: bold; margin-bottom: 12px;">
                Descarga y código fuente completo disponible en el repositorio de GitHub
            </p>
            <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
                <a href="https://github.com/neurodeveloper11/centinela-sismico" target="_blank" style="background: #ef4444; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">
                    Ver Repositorio en GitHub
                </a>
                <a href="https://huggingface.co/neurodeveloper" target="_blank" style="background: #eab308; color: #0f172a; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">
                    🤗 Perfil en Hugging Face (@neurodeveloper)
                </a>
            </div>
        </div>
        """)

    # -------------------------------------------------------------
    # EVENT BINDINGS
    # -------------------------------------------------------------
    # Populate on startup / refresh
    demo.load(fn=update_feed_quakes, inputs=[feed_select], outputs=[quake_dropdown, quakes_table])
    refresh_feed_btn.click(fn=update_feed_quakes, inputs=[feed_select], outputs=[quake_dropdown, quakes_table])
    feed_select.change(fn=update_feed_quakes, inputs=[feed_select], outputs=[quake_dropdown, quakes_table])
    
    city_preset.change(fn=on_city_selected, inputs=[city_preset], outputs=[lat_input, lon_input])
    
    calc_btn.click(
        fn=calculate_impact_ui,
        inputs=[quake_dropdown, lat_input, lon_input, feed_select, lang_radio],
        outputs=impact_output
    )

    triage_btn.click(
        fn=run_structural_triage_ui,
        inputs=[elem_dropdown, crack_dropdown, utility_dropdown, lang_radio],
        outputs=triage_output
    )

    check_myth_btn.click(
        fn=run_mythbuster_ui,
        inputs=[myth_input, lang_radio],
        outputs=myth_output
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
