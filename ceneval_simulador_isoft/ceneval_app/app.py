"""
app.py - Simulador CENEVAL EGEL-PLUS ISOFT
==========================================
Sistema Experto Adaptativo con:
- Motor de inferencia para avance/retroceso por tema
- Agente tutor con retroalimentación adaptativa
- Banco de preguntas basado en PIXOGUÍAS 2025
- Reasignación explícita de sesión para evitar bucles (fix principal)
"""
 
from flask import Flask, render_template, request, redirect, url_for, session
import json, os, random
from datetime import datetime
from flask.sessions import SecureCookieSessionInterface
 
import tempfile
app = Flask(__name__)
app.secret_key = 'ceneval_egel_isoft_2025_secret'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = tempfile.gettempdir()
app.config['SESSION_PERMANENT'] = False

from flask_session import Session
Session(app)
 
# ── Carga del banco de preguntas ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'data', 'preguntas.json'), encoding='utf-8') as f:
    BANCO = json.load(f)
 
TEMAS     = BANCO['temas']
PREGUNTAS = BANCO['preguntas']
 
# ── Constantes ────────────────────────────────────────────────
MAX_PREGUNTAS       = 30
PREGUNTAS_POR_RONDA = 5
ACIERTOS_PARA_AVANZAR = 3
DIFICULTAD_MAX      = 3
 
 
# ═════════════════════════════════════════════════════════════
# MOTOR DE INFERENCIA
# ═════════════════════════════════════════════════════════════
 
def inferir_siguiente_estado(aciertos, dificultad_actual, intentos_tema):
    """
    Reglas del sistema experto:
      R1: aciertos >= 3             → avanzar
      R2: aciertos < 3, dif < 3    → repetir con dificultad mayor
      R3: aciertos < 3, dif = 3, intentos < 3 → repetir misma dificultad
      R4: intentos >= 3             → forzar avance (anti-bucle)
    """
    if aciertos >= ACIERTOS_PARA_AVANZAR:
        return {'accion': 'avanzar', 'nueva_dificultad': 1,
                'mensaje': 'Has demostrado dominio de este tema.'}
    elif dificultad_actual < DIFICULTAD_MAX:
        return {'accion': 'repetir', 'nueva_dificultad': dificultad_actual + 1,
                'mensaje': 'Necesitas reforzar este tema. Aumentamos la dificultad.'}
    elif intentos_tema < 3:
        return {'accion': 'repetir', 'nueva_dificultad': DIFICULTAD_MAX,
                'mensaje': 'Continúa practicando. Puedes mejorar con más intentos.'}
    else:
        return {'accion': 'forzar', 'nueva_dificultad': 1,
                'mensaje': 'Avanzamos al siguiente tema. Repasa los conceptos anteriores.'}
 
 
def obtener_preguntas_ronda(tema_id, dificultad, ya_usadas):
    """
    Selecciona preguntas para la ronda.
    Prioridad: dificultad exacta → otras dificultades → reutilizar vistas.
    Garantiza siempre PREGUNTAS_POR_RONDA preguntas (nunca devuelve lista vacía).
    """
    candidatas = [p for p in PREGUNTAS
                  if p['tema'] == tema_id
                  and p['dificultad'] == dificultad
                  and p['id'] not in ya_usadas]
 
    if len(candidatas) < PREGUNTAS_POR_RONDA:
        extra = [p for p in PREGUNTAS
                 if p['tema'] == tema_id
                 and p['id'] not in ya_usadas
                 and p not in candidatas]
        candidatas.extend(extra)
 
    # Si aún faltan, reutilizar preguntas ya vistas
    if len(candidatas) < PREGUNTAS_POR_RONDA:
        reuso = [p for p in PREGUNTAS
                 if p['tema'] == tema_id
                 and p not in candidatas]
        random.shuffle(reuso)
        candidatas.extend(reuso)
 
    random.shuffle(candidatas)
    return candidatas[:PREGUNTAS_POR_RONDA]
 
 
def calcular_calificacion_final(historial_rondas):
    total_pond, max_pond = 0, 0
    for ronda in historial_rondas:
        peso = ronda.get('dificultad', 1)
        total_pond += ronda['aciertos'] * peso
        max_pond   += ronda['total']    * peso
    if max_pond == 0:
        return 0, 'Sin datos'
    porcentaje = round((total_pond / max_pond) * 100, 1)
    if porcentaje >= 85: nivel = 'Sobresaliente'
    elif porcentaje >= 70: nivel = 'Suficiente'
    elif porcentaje >= 55: nivel = 'Casi suficiente'
    else: nivel = 'No suficiente'
    return porcentaje, nivel
 
 
# ═════════════════════════════════════════════════════════════
# AGENTE TUTOR
# ═════════════════════════════════════════════════════════════
 
def generar_retroalimentacion_ronda(aciertos, total, tema_nombre, dificultad):
    porcentaje = (aciertos / total) * 100 if total > 0 else 0
    if porcentaje == 100:
        return {'tipo': 'excelente',
                'titulo': 'Ronda perfecta',
                'mensaje': f'Dominas completamente el tema de {tema_nombre}. Respondiste correctamente las {total} preguntas.',
                'recomendacion': 'Mantén este nivel de preparación antes del examen real.'}
    elif aciertos >= ACIERTOS_PARA_AVANZAR:
        return {'tipo': 'bien',
                'titulo': 'Buen resultado — avanzas al siguiente tema',
                'mensaje': f'Obtuviste {aciertos} de {total} aciertos en {tema_nombre}.',
                'recomendacion': 'Repasa los reactivos donde fallaste. Revisa las justificaciones para consolidar el conocimiento.'}
    elif aciertos == 2:
        return {'tipo': 'regular',
                'titulo': 'Casi lo logras — otra ronda para reforzar',
                'mensaje': f'Obtuviste {aciertos} de {total} aciertos en {tema_nombre}. Estás muy cerca.',
                'recomendacion': f'Lee con atención las justificaciones. La dificultad sube a nivel {min(dificultad+1, 3)}.'}
    elif aciertos == 1:
        return {'tipo': 'bajo',
                'titulo': 'Necesitas reforzar este tema',
                'mensaje': f'Obtuviste {aciertos} de {total} aciertos en {tema_nombre}.',
                'recomendacion': 'Estudia los conceptos base antes de continuar. Revisa cada justificación con atención.'}
    else:
        return {'tipo': 'muy_bajo',
                'titulo': 'Refuerzo intensivo necesario',
                'mensaje': f'Obtuviste {aciertos} de {total} aciertos en {tema_nombre}.',
                'recomendacion': 'Revisa el material de estudio del tema. Consulta la bibliografía de referencia.'}
 
 
def generar_retroalimentacion_final(porcentaje, nivel, historial_rondas, temas_completados):
    temas_debiles = list(set(
        r['tema_nombre'] for r in historial_rondas
        if r['total'] > 0 and (r['aciertos'] / r['total']) < 0.6
    ))
    if nivel == 'Sobresaliente':
        comentario = f'Excelente desempeño. Con un {porcentaje}% demuestras dominio sólido de Ingeniería de Software.'
        recomendaciones = ['Realiza simulacros adicionales para mantener tu nivel.',
                           'Revisa los temas de mayor dificultad para consolidar tu ventaja.',
                           'Practica la gestión del tiempo durante el examen real.']
    elif nivel == 'Suficiente':
        comentario = f'Buen trabajo. Con un {porcentaje}% demuestras conocimientos adecuados.'
        recomendaciones = [f'Refuerza especialmente: {", ".join(temas_debiles) if temas_debiles else "todos los temas"}.',
                           'Practica reactivos de dificultad alta (nivel 3).',
                           'Revisa normas ISO/IEC relevantes para el área de calidad.']
    elif nivel == 'Casi suficiente':
        comentario = f'Vas por buen camino, pero necesitas más práctica. Con un {porcentaje}% es importante reforzar.'
        recomendaciones = [f'Prioriza el estudio de: {", ".join(temas_debiles) if temas_debiles else "los temas con menor desempeño"}.',
                           'Dedica al menos 2 horas diarias de estudio.',
                           'Estudia las justificaciones de cada reactivo, no solo la respuesta correcta.',
                           'Consulta el PMBOK Guide y Pressman para gestión de proyectos.']
    else:
        comentario = f'Tu desempeño de {porcentaje}% indica que necesitas preparación adicional.'
        recomendaciones = ['Comienza por revisar los conceptos fundamentales de cada área.',
                           'Consulta: Pressman, Sommerville, PMBOK Guide.',
                           f'Focaliza tu estudio en: {", ".join(temas_debiles) if temas_debiles else "todos los temas"}.',
                           'Considera un curso de preparación o estudio grupal.',
                           'Resuelve este simulador al menos 3 veces antes del examen.']
    return {'comentario': comentario, 'recomendaciones': recomendaciones, 'temas_debiles': temas_debiles}
 
 
# ═════════════════════════════════════════════════════════════
# RUTAS
# ═════════════════════════════════════════════════════════════
 
@app.route('/')
def index():
    session.clear()
    return render_template('index.html')
 
 
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            return render_template('registro.html', error='El nombre es obligatorio.')
        session['estudiante'] = {
            'nombre':      nombre,
            'matricula':   request.form.get('matricula', '').strip(),
            'institucion': request.form.get('institucion', '').strip(),
            'fecha':       datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        session['examen'] = {
            'total_preguntas':  0,
            'tema_idx':         0,
            'dificultad':       1,
            'intentos_tema':    0,
            'preguntas_usadas': {},
            'historial_rondas': [],
            'temas_completados':[],
            'estado':           'activo'
        }
        return redirect(url_for('temas'))
    return render_template('registro.html')
 
 
@app.route('/temas')
def temas():
    if 'estudiante' not in session:
        return redirect(url_for('index'))
    examen = session['examen']
    progreso = round((examen['total_preguntas'] / MAX_PREGUNTAS) * 100)
    return render_template('temas.html',
                           estudiante=session['estudiante'],
                           temas=TEMAS,
                           examen=examen,
                           progreso=progreso,
                           max_preguntas=MAX_PREGUNTAS)
 
 
@app.route('/iniciar_ronda')
def iniciar_ronda():
    if 'estudiante' not in session:
        return redirect(url_for('index'))

    # Copia explícita para que Flask detecte cambios
    examen = dict(session['examen'])
    examen['preguntas_usadas']  = dict(examen['preguntas_usadas'])
    examen['historial_rondas']  = list(examen['historial_rondas'])
    examen['temas_completados'] = list(examen['temas_completados'])

    if examen['total_preguntas'] >= MAX_PREGUNTAS:
        return redirect(url_for('final'))
    if examen['tema_idx'] >= len(TEMAS):
        return redirect(url_for('final'))

    tema    = TEMAS[examen['tema_idx']]
    tema_id = tema['id']
    ya_usadas = list(examen['preguntas_usadas'].get(tema_id, []))
    preguntas_ronda = obtener_preguntas_ronda(tema_id, examen['dificultad'], ya_usadas)

    if not preguntas_ronda:
        examen['tema_idx'] += 1
        session['examen'] = examen
        session.modified = True
        return redirect(url_for('temas'))

    session['ronda'] = {
        'preguntas':    preguntas_ronda,
        'pregunta_idx': 0,
        'respuestas':   [],
        'tema_id':      tema_id,
        'tema_nombre':  tema['nombre'],
        'dificultad':   examen['dificultad']
    }
    session['examen'] = examen
    session.modified = True
    return redirect(url_for('examen'))
 
 
@app.route('/examen', methods=['GET'])
def examen():
    if 'ronda' not in session:
        return redirect(url_for('temas'))
 
    ronda       = session['ronda']
    examen_data = session['examen']
    idx         = ronda['pregunta_idx']
 
    if idx >= len(ronda['preguntas']):
        return redirect(url_for('resultado_ronda'))
 
    pregunta           = ronda['preguntas'][idx]
    num_pregunta_global = examen_data['total_preguntas'] + idx + 1
    total_en_ronda     = len(ronda['preguntas'])
    progreso_ronda     = round((idx / total_en_ronda) * 100) if total_en_ronda > 0 else 0
    progreso_global    = round((examen_data['total_preguntas'] / MAX_PREGUNTAS) * 100)
 
    return render_template('examen.html',
                           pregunta=pregunta,
                           num_pregunta=idx + 1,
                           total_ronda=total_en_ronda,
                           num_pregunta_global=num_pregunta_global,
                           progreso_ronda=progreso_ronda,
                           progreso_global=progreso_global,
                           tema_nombre=ronda['tema_nombre'],
                           dificultad=ronda['dificultad'],
                           estudiante=session['estudiante'],
                           examen_aciertos_seguidos=0)
 
 
@app.route('/responder', methods=['POST'])
def responder():
    if 'ronda' not in session:
        return redirect(url_for('temas'))
 
    # ── FIX CRÍTICO: copias explícitas para que Flask detecte los cambios ──
    ronda              = dict(session['ronda'])
    ronda['preguntas'] = list(ronda['preguntas'])
    ronda['respuestas']= list(ronda['respuestas'])
 
    idx = ronda['pregunta_idx']
 
    if idx >= len(ronda['preguntas']):
        session['ronda'] = ronda
        session.modified = True
        return redirect(url_for('resultado_ronda'))
 
    pregunta         = ronda['preguntas'][idx]
    respuesta_usuario = request.form.get('respuesta', '')
    es_correcta      = respuesta_usuario == pregunta['respuesta']
 
    ronda['respuestas'].append({
        'pregunta_id':        pregunta['id'],
        'pregunta_texto':     pregunta['pregunta'][:80] + '...',
        'respuesta_usuario':  respuesta_usuario,
        'respuesta_correcta': pregunta['respuesta'],
        'es_correcta':        es_correcta,
        'justificacion':      pregunta['justificacion'],
        'opciones':           pregunta['opciones'],
        'contexto':           pregunta.get('contexto', '')
    })
 
    ronda['pregunta_idx'] = idx + 1

    # Verificar 3 aciertos consecutivos al final de las respuestas
    respuestas = ronda['respuestas']
    if len(respuestas) >= 3:
        ultimas_3 = respuestas[-3:]
        if all(r['es_correcta'] for r in ultimas_3):
            # Forzar aciertos = 3 para que el motor de inferencia decida avanzar
            ronda['aciertos_consecutivos'] = 3
            session['ronda'] = ronda
            session.modified = True
            return redirect(url_for('resultado_ronda'))

    session['ronda'] = ronda
    session.modified = True

    if ronda['pregunta_idx'] >= len(ronda['preguntas']):
        return redirect(url_for('resultado_ronda'))

    return redirect(url_for('examen'))
 
 
@app.route('/resultado_ronda')
def resultado_ronda():
    if 'ronda' not in session:
        return redirect(url_for('temas'))
 
    ronda = session['ronda']
 
    # ── FIX CRÍTICO: copias explícitas del estado del examen ──
    examen_data = dict(session['examen'])
    examen_data['preguntas_usadas']  = dict(examen_data['preguntas_usadas'])
    examen_data['historial_rondas']  = list(examen_data['historial_rondas'])
    examen_data['temas_completados'] = list(examen_data['temas_completados'])
 
    # Si hubo 3 consecutivos se fuerza aciertos = 3 para que el motor avance
    if ronda.get('aciertos_consecutivos') == 3:
        aciertos = 3
    else:
        aciertos = sum(1 for r in ronda['respuestas'] if r['es_correcta'])
    total = len(ronda['respuestas'])    
 
    estado_inferido = inferir_siguiente_estado(
        aciertos, examen_data['dificultad'], examen_data['intentos_tema'])
 
    feedback = generar_retroalimentacion_ronda(
        aciertos, total, ronda['tema_nombre'], examen_data['dificultad'])
 
    # Actualizar preguntas usadas
    tema_id   = ronda['tema_id']
    ids_usados = [p['pregunta_id'] for p in ronda['respuestas']]
    prev_usadas = list(examen_data['preguntas_usadas'].get(tema_id, []))
    examen_data['preguntas_usadas'][tema_id] = prev_usadas + ids_usados
 
    examen_data['historial_rondas'].append({
        'tema_id':     tema_id,
        'tema_nombre': ronda['tema_nombre'],
        'dificultad':  ronda['dificultad'],
        'aciertos':    aciertos,
        'total':       total,
        'respuestas':  ronda['respuestas']
    })
 
    examen_data['total_preguntas'] += total
    examen_data['intentos_tema']   += 1
 
    if estado_inferido['accion'] in ('avanzar', 'forzar'):
        examen_data['temas_completados'].append(tema_id)
        examen_data['tema_idx']     += 1
        examen_data['dificultad']    = 1
        examen_data['intentos_tema'] = 0
    else:
        examen_data['dificultad'] = estado_inferido['nueva_dificultad']
 
    # ── Reasignar objeto completo a la sesión ──
    session['examen'] = examen_data
    session.modified  = True
 
    examen_terminado = (
        examen_data['total_preguntas'] >= MAX_PREGUNTAS or
        examen_data['tema_idx'] >= len(TEMAS)
    )
 
    porcentaje_ronda = round((aciertos / total) * 100) if total > 0 else 0
 
    return render_template('resultado_ronda.html',
                           aciertos=aciertos,
                           total=total,
                           porcentaje_ronda=porcentaje_ronda,
                           ronda=ronda,
                           feedback=feedback,
                           estado_inferido=estado_inferido,
                           examen_terminado=examen_terminado,
                           preguntas_usadas=examen_data['total_preguntas'],
                           max_preguntas=MAX_PREGUNTAS,
                           estudiante=session['estudiante'])
 
 
@app.route('/final')
def final():
    if 'estudiante' not in session:
        return redirect(url_for('index'))
 
    examen_data = session['examen']
    historial   = examen_data.get('historial_rondas', [])
 
    if not historial:
        return redirect(url_for('temas'))
 
    porcentaje, nivel = calcular_calificacion_final(historial)
    analisis = generar_retroalimentacion_final(
        porcentaje, nivel, historial, examen_data['temas_completados'])
 
    resumen_temas = {}
    for ronda in historial:
        t = ronda['tema_id']
        if t not in resumen_temas:
            resumen_temas[t] = {'nombre': ronda['tema_nombre'], 'aciertos': 0, 'total': 0}
        resumen_temas[t]['aciertos'] += ronda['aciertos']
        resumen_temas[t]['total']    += ronda['total']
    for t in resumen_temas:
        a, tot = resumen_temas[t]['aciertos'], resumen_temas[t]['total']
        resumen_temas[t]['porcentaje'] = round((a / tot * 100)) if tot > 0 else 0
 
    examen_data['estado'] = 'finalizado'
    session['examen'] = examen_data
    session.modified  = True
 
    return render_template('final.html',
                           estudiante=session['estudiante'],
                           porcentaje=porcentaje,
                           nivel=nivel,
                           analisis=analisis,
                           resumen_temas=resumen_temas,
                           historial=historial,
                           total_respondidas=examen_data['total_preguntas'])
 
 
@app.route('/ontologia')
def ontologia():
    return render_template('ontologia.html')
 
 
@app.route('/reiniciar')
def reiniciar():
    session.clear()
    return redirect(url_for('index'))

@app.route('/retroalimentacion')
def retroalimentacion():
    if 'estudiante' not in session:
        return redirect(url_for('index'))
    examen_data = session.get('examen', {})
    historial = examen_data.get('historial_rondas', [])
    if not historial:
        return render_template('retroalimentacion.html',
                               estudiante=session['estudiante'],
                               historial=[],
                               porcentaje=None,
                               nivel=None,
                               analisis=None,
                               resumen_temas={},
                               total_respondidas=0)
    porcentaje, nivel = calcular_calificacion_final(historial)
    analisis = generar_retroalimentacion_final(
        porcentaje, nivel, historial, examen_data.get('temas_completados', []))
    resumen_temas = {}
    for ronda in historial:
        t = ronda['tema_id']
        if t not in resumen_temas:
            resumen_temas[t] = {'nombre': ronda['tema_nombre'], 'aciertos': 0, 'total': 0}
        resumen_temas[t]['aciertos'] += ronda['aciertos']
        resumen_temas[t]['total']    += ronda['total']
    for t in resumen_temas:
        a, tot = resumen_temas[t]['aciertos'], resumen_temas[t]['total']
        resumen_temas[t]['porcentaje'] = round((a / tot * 100)) if tot > 0 else 0
    return render_template('retroalimentacion.html',
                           estudiante=session['estudiante'],
                           historial=historial,
                           porcentaje=porcentaje,
                           nivel=nivel,
                           analisis=analisis,
                           resumen_temas=resumen_temas,
                           total_respondidas=examen_data.get('total_preguntas', 0))

@app.route('/ayuda')
def ayuda():
    if 'estudiante' not in session:
        return redirect(url_for('index'))
    return render_template('ayuda.html', estudiante=session['estudiante'])
 
 
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
 
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 