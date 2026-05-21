# 🎓 Simulador CENEVAL EGEL-PLUS ISOFT

Sistema Experto Adaptativo de Evaluación tipo examen CENEVAL para el área de UVM 
**(ISOFT)**, basado en el banco oficial de reactivos PIXOGUÍAS 2025.

---

##  Estructura del proyecto

```
ceneval_app/
├── app.py                   # Aplicación Flask principal (lógica del sistema experto)
├── data/
│   └── preguntas.json       # Banco de preguntas extraídas del PDF REACTIVOS_1
├── templates/
│   ├── index.html           # Pantalla de inicio
│   ├── registro.html        # Registro del estudiante
│   ├── temas.html           # Menú de temas con progreso
│   ├── examen.html          # Pantalla de examen
│   ├── resultado_ronda.html # Resultado por ronda con retroalimentación
│   ├── final.html           # Calificación final interpretativa
│   └── ontologia.html       # Diagrama de ontología del dominio
└── static/
    ├── css/style.css        # Hoja de estilos (diseño profesional escolar)
    └── js/main.js           # Lógica del cliente (selección, validación)
```

---

##  Instrucciones para ejecutar en VS Code

### Requisitos previos
- Python 3.8+ instalado
- VS Code con extensión Python (opcional pero recomendado)

### Pasos

**1. Abre una terminal en VS Code**  
   `Terminal → New Terminal` o presiona `` Ctrl+` ``

**2. Navega a la carpeta del proyecto**
```bash
cd ceneval_app
```

**3. (Opcional) Crea un entorno virtual**
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Mac/Linux:
source venv/bin/activate
```

**4. Instala Flask**
```bash
pip install flask
```

**5. Ejecuta la aplicación**
```bash
python app.py
```

O también puedes usar:
```bash
flask run
```

**6. Abre en tu navegador**  
Ve a: **http://127.0.0.1:5000**

---

##  Arquitectura del Sistema Experto

### Motor de Inferencia (`app.py → inferir_siguiente_estado`)

El sistema usa un motor de reglas para decidir si el estudiante avanza o repite:

| Condición | Acción |
|-----------|--------|
| Aciertos ≥ 3 | Avanzar al siguiente tema |
| Aciertos < 3 y dificultad < 3 | Repetir con mayor dificultad |
| Aciertos < 3 y dificultad = 3 y intentos < 3 | Repetir misma dificultad |
| Intentos ≥ 3 en el mismo tema | Forzar avance (anti-bloqueo) |

### Agente Tutor (`app.py → generar_retroalimentacion_*`)

Genera retroalimentación adaptativa según:
- Porcentaje de aciertos en la ronda
- Nivel de dificultad alcanzado
- Temas donde el estudiante tiene debilidades
- Historial completo del simulacro

### Ontología del Dominio

Organiza el conocimiento en:
- **4 Áreas temáticas** principales (EGEL-PLUS ISOFT)
- **12 Subcategorías** de conocimiento
- **24+ Conceptos específicos** como hojas del árbol

### Calificación Final

Ponderada por dificultad (las preguntas más difíciles valen más):
- **Sobresaliente**: ≥ 85%
- **Suficiente**: 70–84%
- **Casi suficiente**: 55–69%
- **No suficiente**: < 55%

---

##  Temas evaluados (EGEL-PLUS ISOFT)

1. **Gestión y Administración de Proyectos de Software**  
   Planificación, alcance, tiempos (PERT), costos (COCOMO), PMBOK

2. **Proceso y Metodologías de Desarrollo de Software**  
   RUP, cascada, metodologías ágiles, riesgos, estimación

3. **Calidad y Estándares de Software**  
   ISO 9126, ISO 25000, ISO 15504 (SPICE), métricas, auditoría

4. **Planeación Estratégica de TI**  
   Estrategia FODA, seguridad de la información, arquitectura TI

---

## Referencias bibliográficas

- Pressman, R. S. (2019). *Software Engineering: A Practitioner's Approach*. McGraw-Hill.
- Sommerville, I. (2020). *Software Engineering* (10th ed.). Pearson.
- PMI. (2017). *A Guide to the Project Management Body of Knowledge* (PMBOK Guide) 6th ed.
- Kerzner, H. (2022). *Project Management: A Systems Approach to Planning*. Wiley.
- ISO/IEC 25000 (2014). Systems and Software Quality Requirements and Evaluation (SQuaRE).
- ISO/IEC 15504 (2004). Information technology – Process assessment.

---

##  Solución de problemas comunes

**Error: "flask" no se reconoce**  
→ Asegúrate de haber instalado Flask: `pip install flask`

**Error de puerto en uso**  
→ Cambia el puerto: `flask run --port 5001`

**Página en blanco**  
→ Verifica que estés en la carpeta `ceneval_app/` al ejecutar

---

*Simulador CENEVAL EGEL-PLUS ISOFT — Prototipo educativo 2025*  
*Basado en reactivos PIXOGUÍAS 2025 · Ingeniería de Software*

## Este sistema no es propiedad de nadie

El sistema es o la plantilla puede ser usada por cualquier alumno con fines
de aprendizaje.

---

## Creadores

Libreros Coronado Fernando
Jesus Yael Arellano Limon
Jonathan Mauricio Miranda Rico

"Nadie le sabe a la IA namas yo"
-FLC