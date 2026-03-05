# Design — Sistema de Reseñas y Valoraciones de Actividades

## 1. Contexto: Estado Actual del Sistema

### Arquitectura actual
```
┌─────────────────────────────────────────────────┐
│                   FRONTEND                       │
│  index.html ─ app.js ─ styles.css               │
│  (Vanilla JS, datos cargados via fetch API)      │
│  Servido como archivos estáticos por FastAPI     │
└────────────────────┬────────────────────────────┘
                     │  HTTP (POST/DELETE)
                     ▼
┌─────────────────────────────────────────────────┐
│                   BACKEND                        │
│  app.py (FastAPI)                                │
│  ┌─────────────────────────────────────────┐    │
│  │  Diccionario en memoria: activities{}    │    │
│  │  Endpoints: GET /, GET /activities,      │    │
│  │  POST /signup, DELETE /unregister        │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────┐
│                   TESTS                          │
│  test_app.py (pytest + TestClient, patrón AAA)  │
└─────────────────────────────────────────────────┘
```

### Archivos relevantes y su rol actual
| Archivo | Rol | Líneas aprox. |
|---------|-----|---------------|
| `src/app.py` | API FastAPI, diccionario `activities`, 4 endpoints | ~135 |
| `src/static/index.html` | Estructura HTML, contenedores vacíos para actividades y formulario signup | ~45 |
| `src/static/app.js` | Carga de actividades via fetch API, renderizado de tarjetas, formulario signup, botón unregister | ~140 |
| `src/static/styles.css` | Estilos visuales (tarjetas, formularios, participantes) | ~190 |
| `tests/test_app.py` | 8 tests existentes organizados en clases (AAA pattern) | ~200 |

### Patrón de datos actual
```
activities = {
    "Chess Club": {
        "description": str,
        "schedule": str,
        "max_participants": int,
        "participants": [str]    ← lista de emails
    },
    ...
}
```

### Particularidad importante
El frontend carga las actividades dinámicamente via `fetch()` al API. Las operaciones de lectura (GET /activities) y escritura (signup, unregister) usan endpoints del API. Las reseñas seguirán este patrón: lectura via GET /activities/{name}/reviews y escritura via POST/DELETE.

---

## 2. Estructura de Datos: Nuevas Entidades

### 2.1 Almacén de reseñas (nueva estructura en memoria)

Se creará un nuevo diccionario global `reviews` en `app.py`, independiente de `activities`:

```
reviews = {
    "Chess Club": [
        {
            "email": "michael@mergington.edu",
            "rating": 5,
            "comment": "Great club, very challenging!",
            "timestamp": "2026-03-05T10:30:00"
        },
        ...
    ],
    "Programming Class": [ ... ],
    ...
}
```

**Decisión de diseño:** Las reseñas se almacenan en un diccionario separado (no dentro de `activities`) para:
- Mantener la estructura existente de `activities` intacta y no romper tests ni frontend actual.
- Facilitar el reset en tests (limpiar reviews sin afectar activities).
- Separación de responsabilidades clara.

### 2.2 Campos calculados en la respuesta de actividades

El endpoint `GET /activities` se enriquece para incluir datos derivados de reviews:

```
{
    "Chess Club": {
        "description": "...",
        "schedule": "...",
        "max_participants": 12,
        "participants": [...],
        "average_rating": 4.3,      ← NUEVO (float | null)
        "review_count": 3           ← NUEVO (int)
    }
}
```

Estos campos se calculan dinámicamente al servir la respuesta, nunca se almacenan.

---

## 3. Diseño de API: Nuevos Endpoints

### 3.1 Tabla resumen

| Método | Ruta | Descripción | Request | Response |
|--------|------|-------------|---------|----------|
| `GET` | `/activities/{name}/reviews` | Obtener reseñas de una actividad | — | `{ reviews: [...], average_rating, review_count }` |
| `POST` | `/activities/{name}/reviews` | Crear una reseña | `{ email, rating, comment }` | `{ message }` |
| `DELETE` | `/activities/{name}/reviews` | Eliminar reseña propia | `?email=...` | `{ message }` |

### 3.2 Endpoint modificado

| Método | Ruta | Cambio |
|--------|------|--------|
| `GET` | `/activities` | Agrega `average_rating` y `review_count` a cada actividad. Acepta `?sort_by=rating_asc\|rating_desc` |

### 3.3 Flujo de validaciones por endpoint

**POST /activities/{name}/reviews**
```
1. ¿Existe la actividad?          → No → 404 "Activity not found"
2. ¿Email está en participants?   → No → 403 "Only participants can leave reviews"
3. ¿Ya existe review de este email? → Sí → 400 "You have already reviewed this activity"
4. ¿Rating entre 1 y 5?           → No → 422 (validación automática de Pydantic)
5. ¿Comment vacío o solo espacios? → Sí → 400 "Comment cannot be empty"
6. ¿Comment > 500 chars?          → Sí → 400 "Comment must be 500 characters or less"
7. Todo OK → Crear review → 200
```

**DELETE /activities/{name}/reviews?email=...**
```
1. ¿Existe la actividad?          → No → 404 "Activity not found"
2. ¿Existe review de este email?  → No → 404 "Review not found"
3. Todo OK → Eliminar review → 200
```

---

## 4. Diseño Frontend: Componentes Nuevos y Modificados

### 4.1 Mapa de cambios por archivo

#### `app.py` — Nuevas estructuras de datos
- **Nuevo diccionario `reviews`**: Almacena reseñas separadas de `activities`, con estructura: `reviews = { "Activity Name": [{ "email": str, "rating": int, "comment": str, "timestamp": str }, ...] }`
- **Nuevo modelo Pydantic `ReviewRequest`**: Valida POST requests con campos `email` (str), `rating` (int 1-5), `comment` (str, no vacío, máx 500 caracteres)
- **Inicialización en startup**: Opcionalmente, cargar reviews de un archivo o inicializar vacío

#### `app.py` — Nuevos endpoints
| Endpoint | Método | Cambios |
|----------|--------|---------|
| `/activities/{name}/reviews` | `GET` | Obtiene lista de reviews, calcula `average_rating` y `review_count` |
| `/activities/{name}/reviews` | `POST` | Crea nueva review con validaciones (participante, no duplicado, rating, comment) |
| `/activities/{name}/reviews` | `DELETE` | Elimina review propia del usuario (query param `?email=...`) |

#### `app.py` — Endpoint modificado
| Endpoint | Cambio |
|----------|--------|
| `/activities` | Agregar al response `average_rating` (float o null) y `review_count` (int) calculados dinámicamente para cada actividad. Soportar query param `?sort_by=rating_asc` o `?sort_by=rating_desc` para ordenamiento opcional en backend |

#### `index.html`
- Agregar sección de controles de ordenamiento (dropdown "Ordenar por") encima de la lista de actividades.
- El HTML solo contiene contenedores vacíos (`<div id="activities-container">`) que se rellenan desde JavaScript. Las actividades se cargan dinámicamente via `fetch()` al endpoint `GET /activities` desde `app.js`, que ahora incluye `average_rating` y `review_count` en cada actividad.

#### `app.js` — Nuevas funciones
| Función | Responsabilidad |
|---------|----------------|
| `renderStars(rating)` | Genera HTML de estrellas visuales (llenas, mitad, vacías) para un rating dado |
| `renderReviewForm(activityName)` | Genera el formulario con selector de estrellas clicable + textarea + botón submit |
| `renderReviewsList(activityName, reviews)` | Genera la lista de reseñas individuales con estrellas, email, comentario, botón eliminar |
| `submitReview(activityName, email, rating, comment)` | Llama POST al API y refresca la tarjeta |
| `deleteReview(activityName, email)` | Llama DELETE al API y refresca la tarjeta |
| `fetchReviews(activityName)` | Llama GET al API de reviews para una actividad |
| `sortActivities(criteria)` | Reordena las tarjetas en el DOM según el criterio seleccionado |

#### `app.js` — Funciones modificadas
| Función | Cambio |
|---------|--------|
| `fetchActivities()` | Incluir `average_rating` y `review_count` en el renderizado de cada tarjeta. Agregar sección de reseñas colapsable dentro de cada tarjeta |

#### `styles.css` — Nuevas clases
| Clase | Propósito |
|-------|-----------|
| `.stars-display` | Contenedor de estrellas en modo solo lectura (promedio) |
| `.star` / `.star.filled` / `.star.half` / `.star.empty` | Estrella individual con estados visuales |
| `.stars-input` | Contenedor de estrellas clicables para el formulario |
| `.stars-input .star:hover` | Efecto hover en estrellas del formulario |
| `.review-section` | Contenedor colapsable de reseñas dentro de la tarjeta |
| `.review-section-toggle` | Botón para expandir/colapsar reseñas |
| `.review-item` | Una reseña individual dentro de la lista |
| `.review-form` | Formulario de nueva reseña |
| `.review-comment` | Texto del comentario de una reseña |
| `.review-meta` | Metadatos de la reseña (email, fecha) |
| `.review-delete-btn` | Botón para eliminar reseña propia |
| `.sort-controls` | Barra de controles de ordenamiento |
| `.rating-badge` | Badge con el promedio de estrellas en la tarjeta |

### 4.2 Mockup estructural de tarjeta con reseñas

```
┌─────────────────────────────────────────┐
│  Chess Club                             │
│  ★★★★☆ 4.0 (3 reviews)                │  ← rating-badge + stars-display
│                                         │
│  Learn strategies and compete...        │
│  Schedule: Fridays, 3:30 PM - 5:00 PM  │
│  Availability: 10 spots left            │
│                                         │
│  ├─ Participants: ──────────────────┤  │
│  │  michael@mergington.edu     ✕    │  │
│  │  daniel@mergington.edu      ✕    │  │
│  ├──────────────────────────────────┤  │
│                                         │
│  ▼ Reviews (3)          [colapsable]    │  ← review-section-toggle
│  ┌──────────────────────────────────┐  │
│  │ ★★★★★ michael@mergington.edu    │  │  ← review-item
│  │ "Great club, very challenging!"  │  │
│  │ 2026-03-05              [🗑️]    │  │
│  ├──────────────────────────────────┤  │
│  │ ★★★★☆ daniel@mergington.edu     │  │
│  │ "Good but needs more sessions"   │  │
│  │ 2026-03-04              [🗑️]    │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌─ Write a Review ─────────────────┐  │  ← review-form
│  │  Your email: [_________________] │  │
│  │  Rating:  ☆ ☆ ☆ ☆ ☆             │  │  ← stars-input (clicables)
│  │  Comment: [____________________] │  │
│  │           [____________________] │  │
│  │           [Submit Review]        │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 4.3 Mockup de controles de ordenamiento

```
┌──────────────────────────────────────────────────────┐
│  Sort by: [ Default ▼ ]                              │
│           ├─ Default (as loaded)                     │
│           ├─ Best rated first                        │
│           └─ Lowest rated first                      │
└──────────────────────────────────────────────────────┘
```

---

## 5. Diseño de Tests: Estructura Esperada

### 5.1 Nuevas clases de test en `test_app.py`

| Clase | Tests | Qué valida |
|-------|-------|------------|
| `TestCreateReview` | 7-8 | Creación exitosa, actividad inexistente, no participante, duplicado, rating inválido, comment vacío, comment largo |
| `TestGetReviews` | 3-4 | Obtener reseñas, actividad sin reseñas, actividad inexistente, cálculo de promedio |
| `TestDeleteReview` | 3-4 | Eliminación exitosa, review no encontrada, actividad inexistente |
| `TestActivitiesWithRatings` | 3-4 | GET /activities incluye average_rating y review_count, ordenamiento por rating |

### 5.2 Fixture nuevo necesario

Se necesita un fixture `reset_reviews` (análogo a `reset_activities`) que limpie el diccionario `reviews` entre cada test para asegurar aislamiento.

---

## 6. Impacto en Archivos Existentes

| Archivo | Tipo de cambio | Riesgo |
|---------|---------------|--------|
| `src/app.py` | **Extensión** — Se agregan ~80-100 líneas (nuevo dict, 3 endpoints, Pydantic model, lógica en GET /activities) | Bajo: no se modifica lógica existente, solo se amplía |
| `src/static/index.html` | **Mínimo** — Agregar dropdown de ordenamiento. Los datos se cargan dinámicamente via `fetch()` desde `app.js` | Bajo |
| `src/static/app.js` | **Extensión significativa** — ~150-200 líneas nuevas (componentes de estrellas, formulario, sección reviews, sorting) | Medio: se modifica `fetchActivities()` para renderizar nueva UI |
| `src/static/styles.css` | **Extensión** — ~80-100 líneas nuevas de estilos | Bajo: solo se agregan clases nuevas |
| `tests/test_app.py` | **Extensión** — ~150-200 líneas nuevas (4 clases de test, fixture nuevo) | Bajo: se agregan clases independientes |
| `requirements.txt` | **Sin cambios** — Pydantic viene incluido con FastAPI | Ninguno |

---

## 7. Decisiones de Diseño Clave

| # | Decisión | Justificación |
|---|----------|---------------|
| D-01 | Reviews en diccionario separado, no dentro de `activities` | No rompe la estructura existente ni los tests actuales. Separación limpia de concerns |
| D-02 | Promedio calculado dinámicamente, nunca almacenado | Simplicidad. Con datos en memoria y pocas reseñas, el cálculo es instantáneo |
| D-03 | Body JSON para POST de review (no query params) | A diferencia de signup que usa query params, una review tiene campos complejos que encajan mejor en un body JSON con validación Pydantic |
| D-04 | Las reseñas sobreviven a la desinscripción | El participante tuvo la experiencia; su opinión sigue siendo válida |
| D-05 | Reseñas colapsables en la tarjeta | Evita que la UI se vuelva demasiado larga con muchas reseñas |
| D-06 | Estrellas en CSS puro (Unicode ★☆ + colores) | No se requieren iconos externos ni SVGs complejos. Consistente con el enfoque vanilla del proyecto |
| D-07 | Ordenamiento en frontend (no solo API) | Permite reordenar sin recargar la página. El API también soporta `sort_by` para consistencia |
