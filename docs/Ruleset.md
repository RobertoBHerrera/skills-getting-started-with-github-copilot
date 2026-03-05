# Ruleset — Reglas Técnicas para el Desarrollo

## 1. Reglas de Arquitectura

### R-ARCH-01: Consistencia con el stack existente
- **Backend:** FastAPI con Python. No introducir frameworks adicionales (Django, Flask).
- **Frontend:** Vanilla JavaScript (ES6+). No introducir frameworks (React, Vue, etc.) ni bundlers (Webpack, Vite).
- **Estilos:** CSS puro. No introducir preprocesadores (Sass, Less) ni frameworks CSS (Tailwind, Bootstrap).
- **Tests:** pytest con FastAPI TestClient. No introducir otros frameworks de testing.

### R-ARCH-02: Almacenamiento en memoria
- Todos los datos se almacenan en diccionarios Python globales en `app.py`.
- No introducir bases de datos (SQLite, PostgreSQL), archivos JSON, ni sistemas de cache.
- Aceptar que los datos se pierden al reiniciar el servidor (esto es by design para este proyecto).

### R-ARCH-03: Estructura de archivos
- No crear archivos Python nuevos (ni módulos, ni packages). Todo el backend va en `app.py`.
- Los archivos frontend van exclusivamente en `src/static/`.
- Los tests van exclusivamente en `tests/test_app.py`.
- Los documentos SDD van en `docs/`.

### R-ARCH-04: Patrón de datos frontend
- Respetar el patrón actual: los datos se obtienen dinámicamente desde el API vía `fetch()` en `app.js` (`GET /activities`). El HTML solo contiene contenedores vacíos que se llenan desde JavaScript.
- Las operaciones de escritura (POST, DELETE) van al API de backend.
- Después de una operación de escritura exitosa, refrescar los datos relevantes de la sección afectada.

---

## 2. Reglas de Seguridad (Básicas)

### R-SEC-01: Validación en backend
- Usar Pydantic para validar automáticamente bodies JSON (tipos, rangos).
- Validar query parameters manualmente.

### R-SEC-02: XSS mínimo
- Usar `textContent` en lugar de `innerHTML` al renderizar contenido del usuario.
- Escapar `<`, `>`, `&`, `"`, `'` si es necesario usar `innerHTML`.

---

## 3. Reglas de Codificación Backend (Python)

### R-PY-01: Estilo de código
- Seguir PEP 8 para estilo y formato.
- Usar type hints en los parámetros de las funciones de endpoint.
- Docstrings de una línea para cada función de endpoint ("""Descripción""").

### R-PY-02: Manejo de errores
- Usar `HTTPException` de FastAPI para todos los errores manejados.
- Códigos de estado HTTP correctos: 200 (éxito), 400 (error de validación/negocio), 403 (no autorizado), 404 (no encontrado), 422 (validación de Pydantic).
- Mensajes de error en inglés, descriptivos y consistentes.

### R-PY-03: Estructura de endpoints
- Cada endpoint es una función independiente con decorador de ruta.
- Las validaciones van en orden: existencia → autorización → reglas de negocio → acción.
- Retornar siempre un diccionario JSON con `message` para éxito o `detail` para error.

### R-PY-04: Modelos Pydantic
- Usar `BaseModel` para request bodies con campos complejos (como reviews).
- Usar `Field()` con `ge`, `le`, `min_length`, `max_length` para restricciones.
- Mantener los modelos en el mismo archivo `app.py` (no crear archivos separados).

---

## 4. Reglas de Codificación Frontend (JavaScript)

### R-JS-01: Estilo de código
- ES6+ (arrow functions, template literals, const/let, async/await).
- No usar `var`.
- Nombres descriptivos en camelCase para funciones y variables.

### R-JS-02: Manipulación del DOM
- Usar `document.getElementById()`, `document.querySelector()` para seleccionar elementos.
- Usar `createElement()` + manipulación de propiedades cuando se puede.
- Template literals para HTML complejo, pero siempre escapar contenido del usuario.
- Event delegation cuando sea práctico (similar al patrón actual de click en `activitiesList`).

### R-JS-03: Comunicación con API
- Usar `fetch()` nativo (no axios, no jQuery).
- Encodear parámetros de URL con `encodeURIComponent()`.
- Manejar errores con try/catch y mostrar mensajes al usuario.
- Para POST de reviews, enviar body JSON con `Content-Type: application/json`.

### R-JS-04: Feedback al usuario
- Usar el `messageDiv` existente para mensajes de éxito/error globales.
- Clases CSS: `success`, `error` para estilizar mensajes.
- Ocultar mensajes automáticamente después de 5 segundos (patrón existente).

---

## 5. Reglas de Estilos (CSS)

### R-CSS-01: Paleta de colores
- Primario: `#1a237e` (header, botones principales)
- Secundario: `#0066cc` (títulos de tarjetas)
- Fondo: `#f5f5f5` (body), `#f9f9f9` (tarjetas), `#e3f2fd` (badges)
- Éxito: `#2e7d32` / `#e8f5e9`
- Error: `#c62828` / `#ffebee`
- Estrellas: `#ffc107` (dorado, para estrellas llenas)
- Estrellas vacías: `#ddd`

### R-CSS-02: Diseño
- Bordes redondeados: `border-radius: 4-5px` para tarjetas y botones, `12px` para badges.
- Sombras sutiles: `box-shadow: 0 2px 5px rgba(0,0,0,0.1)`.
- Transiciones: `transition: 0.2s` para hovers.
- Consistencia con los patrones de padding/margin existentes.

### R-CSS-03: Responsividad
- La UI debe funcionar en pantallas desde 320px de ancho.
- Usar `max-width: 500px` para secciones (patrón existente).
- No usar media queries salvo que sea estrictamente necesario.

---

## 6. Reglas de Testing

### R-TEST-01: Patrón AAA
- Todos los tests siguen el patrón **Arrange-Act-Assert** con comentarios explícitos.
- Arrange: preparar datos y estado.
- Act: ejecutar la acción (llamar al endpoint).
- Assert: verificar el resultado esperado.

### R-TEST-02: Aislamiento
- Cada test debe ser completamente independiente de los demás.
- Usar fixtures con `autouse=True` para limpiar estado global (`activities`, `reviews`) antes y después de cada test.
- No depender del orden de ejecución de los tests.

### R-TEST-03: Organización
- Agrupar tests en clases por endpoint/funcionalidad: `TestCreateReview`, `TestGetReviews`, etc.
- Nombres descriptivos: `test_<accion>_<condicion>_<resultado_esperado>`.
- Un assertion principal por test (assertions adicionales son aceptables para verificar side effects).

### R-TEST-04: Cobertura mínima
- Cada endpoint debe tener al menos: 1 test de caso exitoso + 1 test por cada caso de error.
- Los tests existentes no deben modificarse ni eliminarse.
- Los tests nuevos no deben romper los existentes.

### R-TEST-05: Ejecución
- Comando de ejecución: `pytest -v` desde la raíz del proyecto.
- El archivo de configuración `pytest.ini` ya existe y no debe modificarse.
- Todos los tests deben pasar antes de dar un paso por completado.

---

## 7. Reglas de Proceso (SDD)

### R-PROC-01: Documentación primero
- No empezar a codificar hasta que los 4 documentos SDD estén completos y aprobados.
- Cualquier cambio de scope durante la implementación debe reflejarse en los documentos.

### R-PROC-02: Un paso a la vez
- Seguir el Implementation Plan en orden secuencial.
- Completar un paso, revisarlo, y solo entonces avanzar al siguiente.
- Si un paso falla, corregirlo antes de avanzar.

### R-PROC-03: No sobrediseñar
- Implementar solo lo que está especificado en los documentos.
- No agregar funcionalidades extra "por si acaso" (ni logging, ni métricas, ni feature flags).
- YAGNI (You Ain't Gonna Need It).

### R-PROC-04: Mensajes de commit sugeridos
- Usar el formato: `feat(reviews): <descripción del paso>`
- Ejemplo: `feat(reviews): add review data model and storage`
- Un commit por paso completado.
