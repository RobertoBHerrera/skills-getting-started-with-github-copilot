# Implementation Plan — Sistema de Reseñas y Valoraciones de Actividades

## Metodología SDD: Ejecutar, Revisar, Ajustar, Iterar

Cada paso de este plan se ejecutará con el agente de IA siguiendo este ciclo:

```
 ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
 │ EJECUTAR │ ──▶ │ REVISAR  │ ──▶ │ AJUSTAR  │ ──▶ │ ITERAR   │
 │ el paso  │     │ resultado│     │ si hay   │     │ siguiente│
 │ con IA   │     │ y tests  │     │ errores  │     │ paso     │
 └──────────┘     └──────────┘     └──────────┘     └──────────┘
```

**Convención:** Antes de dar un paso por completado, se debe:
1. Verificar que no hay errores de sintaxis.
2. Ejecutar los tests relevantes y confirmar que pasan.
3. Verificar visualmente el frontend si el paso incluye cambios de UI.

---

## Resumen de Pasos

| Paso | Descripción | Archivo(s) | Tipo |
|------|-------------|------------|------|
| 1 | Modelo de datos y almacén de reviews | `app.py` | Backend |
| 2 | Endpoint POST — Crear reseña | `app.py` | Backend |
| 3 | Endpoint GET — Obtener reseñas | `app.py` | Backend |
| 4 | Endpoint DELETE — Eliminar reseña | `app.py` | Backend |
| 5 | Modificar GET /activities con rating y sorting | `app.py` | Backend |
| 6 | Tests del backend completos | `test_app.py` | Tests |
| 7 | Ejecutar tests y corregir errores | Terminal | Validación |
| 8 | Estilos CSS del sistema de reseñas | `styles.css` | Frontend |
| 9 | Componente de estrellas y renderizado de reviews | `app.js` | Frontend |
| 10 | Formulario de reseña y eliminación | `app.js` | Frontend |
| 11 | Controles de ordenamiento | `index.html`, `app.js` | Frontend |
| 12 | Integración completa y test final | Todos | Validación |

---

## Paso 1: Modelo de datos y almacén de reviews

**Archivo:** `src/app.py`  
**Objetivo:** Establecer la estructura de datos de reseñas y el modelo Pydantic de validación.

**Tareas:**
- Importar `BaseModel`, `Field` de Pydantic y `datetime`, `timezone` de la librería estándar (por ejemplo: `from datetime import datetime, timezone`).
- Crear el modelo `ReviewRequest` con campos: `email` (str), `rating` (int, ge=1, le=5), `comment` (str).
- Crear el diccionario global `reviews = {}` que almacenará las listas de reseñas por nombre de actividad.
- Inicializar `reviews` con claves vacías para cada actividad existente.

> **Nota (RN-07):** El diccionario `reviews` es independiente de `activities`. Si un estudiante se desinscribe de una actividad (DELETE /unregister), sus reseñas se mantienen — ya participó y su opinión es válida. No se debe agregar lógica de borrado de reviews en el endpoint de unregister.

**Criterio de éxito:**  
- El servidor arranca sin errores.
- El diccionario `reviews` existe y tiene las mismas claves que `activities`.

**Verificación:**  
```
Ejecutar el servidor → verificar que arranca sin errores
```

---

## Paso 2: Endpoint POST — Crear reseña

**Archivo:** `src/app.py`  
**Objetivo:** Implementar el endpoint `POST /activities/{activity_name}/reviews`.

**Tareas:**
- Crear la función `create_review(activity_name: str, review: ReviewRequest)`.
- Implementar la cadena de validaciones en orden:
  1. Actividad existe → 404
  2. Email en participants → 403
  3. Review duplicada → 400
  4. Comment no vacío → 400
  5. Comment ≤ 500 chars → 400
- Crear el diccionario de review con email, rating, comment, timestamp (ISO format).
- Agregar la review a `reviews[activity_name]`.
- Retornar mensaje de éxito.

**Criterio de éxito:**  
- Llamar al endpoint con datos válidos crea la reseña.
- Cada caso de error retorna el status code y mensaje esperados.

**Verificación:**  
```
Probar manualmente con curl o test rápido → verificar respuestas
```

---

## Paso 3: Endpoint GET — Obtener reseñas

**Archivo:** `src/app.py`  
**Objetivo:** Implementar `GET /activities/{activity_name}/reviews`.

**Tareas:**
- Crear la función `get_reviews(activity_name: str)`.
- Validar que la actividad existe → 404.
- Calcular `average_rating` (promedio de ratings, redondeado a 1 decimal) o `null` si no hay reseñas.
- Retornar JSON con: `reviews` (lista), `average_rating` (float|null), `review_count` (int).

**Criterio de éxito:**  
- Retorna la lista de reseñas con promedio correcto.
- Actividad sin reseñas retorna lista vacía, average_rating null, review_count 0.

**Verificación:**  
```
Crear una review (paso 2) → obtener reviews → verificar datos
```

---

## Paso 4: Endpoint DELETE — Eliminar reseña

**Archivo:** `src/app.py`  
**Objetivo:** Implementar `DELETE /activities/{activity_name}/reviews`.

**Tareas:**
- Crear la función `delete_review(activity_name: str, email: str)`.
- Validar que la actividad existe → 404.
- Buscar la review del email indicado.
- Si no existe → 404 "Review not found".
- Si existe → eliminarla de la lista y retornar mensaje de éxito.
- **Importante (RN-07):** Este endpoint solo elimina reviews explícitamente. El endpoint existente DELETE /unregister NO debe eliminar las reseñas del usuario — las reseñas persisten aunque el estudiante se desinscribe.

**Criterio de éxito:**  
- Eliminar una review existente funciona y el promedio se recalcula.
- Errores retornan los códigos esperados.

**Verificación:**  
```
Crear review → eliminar → verificar que no aparece en GET
```

---

## Paso 5: Modificar GET /activities con rating y sorting

**Archivo:** `src/app.py`  
**Objetivo:** Enriquecer la respuesta del endpoint existente `GET /activities`.

**Tareas:**
- Modificar `get_activities()` para aceptar un query parameter opcional `sort_by: str = None`.
- Para cada actividad, calcular `average_rating` y `review_count` a partir de `reviews`.
- Construir la respuesta con los campos nuevos incluidos.
- Si `sort_by == "rating_desc"`: ordenar por average_rating descendente (nulls al final).
- Si `sort_by == "rating_asc"`: ordenar por average_rating ascendente (nulls al final).
- Mantener compatibilidad total con tests existentes (sin sort_by, el orden no cambia).

**Criterio de éxito:**  
- `GET /activities` retorna `average_rating` y `review_count` en cada actividad.
- El parámetro `sort_by` ordena correctamente.
- Los 8 tests existentes siguen pasando sin modificación.

**Verificación:**  
```
Ejecutar tests existentes → todos deben pasar
Verificar que los campos nuevos aparecen en la respuesta
```

---

## Paso 6: Tests del backend completos

**Archivo:** `tests/test_app.py`  
**Objetivo:** Escribir la batería completa de tests para el sistema de reseñas.

**Tareas:**
- Importar `reviews` desde `src.app`.
- Crear fixture `reset_reviews` que limpia el diccionario `reviews` antes y después de cada test.
- Crear clase `TestCreateReview` (~7 tests):
  - test_create_review_success
  - test_create_review_activity_not_found
  - test_create_review_not_participant (403)
  - test_create_review_duplicate (400)
  - test_create_review_invalid_rating_low (422)
  - test_create_review_invalid_rating_high (422)
  - test_create_review_empty_comment (400)
  - test_create_review_comment_too_long (400)
- Crear clase `TestGetReviews` (~3 tests):
  - test_get_reviews_with_reviews
  - test_get_reviews_empty
  - test_get_reviews_activity_not_found
- Crear clase `TestDeleteReview` (~3 tests):
  - test_delete_review_success
  - test_delete_review_not_found
  - test_delete_review_activity_not_found
- Crear clase `TestActivitiesWithRatings` (~3 tests):
  - test_activities_include_rating_fields
  - test_activities_sort_by_rating_desc
  - test_activities_sort_by_rating_asc

**Criterio de éxito:**  
- Todos los tests nuevos y existentes pasan al ejecutar `pytest`.

**Verificación:**  
```
pytest -v → todos verdes
```

---

## Paso 7: Ejecutar tests y corregir errores

**Archivo:** Terminal  
**Objetivo:** Ejecutar toda la suite de tests y corregir cualquier fallo.

**Tareas:**
- Ejecutar `pytest -v` desde la raíz del proyecto.
- Si hay fallos: analizar el error, corregir el código (backend o test), re-ejecutar.
- Iterar hasta que todos los tests pasen.

**Criterio de éxito:**  
- `pytest -v` → 0 failures, 0 errors.

**Verificación:**  
```
Salida de pytest limpia con todos los tests en verde
```

---

## Paso 8: Estilos CSS del sistema de reseñas

**Archivo:** `src/static/styles.css`  
**Objetivo:** Agregar todos los estilos necesarios para la UI de reseñas.

**Tareas:**
- Agregar estilos para estrellas (`.stars-display`, `.star`, `.star.filled`, `.star.half`, `.star.empty`).
- Agregar estilos para el formulario de reseña (`.review-form`, `.stars-input`, `.stars-input .star`).
- Agregar estilos para la lista de reseñas (`.review-section`, `.review-item`, `.review-meta`, `.review-comment`).
- Agregar estilos para el toggle de sección (`.review-section-toggle`).
- Agregar estilos para el botón de eliminar reseña (`.review-delete-btn`).
- Agregar estilos para el badge de rating (`.rating-badge`).
- Agregar estilos para controles de ordenamiento (`.sort-controls`).
- Usar la paleta existente: `#1a237e` (primario), `#0066cc` (headings), `#f9f9f9` (fondos), `#e3f2fd` (badges).
- Agregar estilos para estrellas con color dorado `#ffc107` (color estándar definido en Ruleset.md).
- Agregar media queries si es necesario para responsividad.

**Criterio de éxito:**  
- Los estilos existen y están listos para ser usados por el JavaScript.
- Consistencia visual con el resto de la UI.

**Verificación:**  
```
Inspección visual del archivo CSS → clases bien definidas
```

---

## Paso 9: Componente de estrellas y renderizado de reviews

**Archivo:** `src/static/app.js`  
**Objetivo:** Implementar las funciones de renderizado de estrellas y lista de reseñas.

**Tareas:**
- Crear función `renderStars(rating, maxStars=5)` que retorna HTML con estrellas Unicode (★/☆) con clases CSS aplicadas.
- Crear función `renderReviewsList(activityName, reviews)` que genera el HTML de todas las reseñas.
- Crear función `fetchReviews(activityName)` que llama a `GET /activities/{name}/reviews` y retorna los datos.
- Modificar la función `fetchActivities()` para:
  - Mostrar el promedio de estrellas y `(N reviews)` en cada tarjeta.
  - Agregar sección colapsable de reseñas dentro de cada tarjeta.
  - Agregar evento de toggle para expandir/colapsar.

**Criterio de éxito:**  
- Las tarjetas muestran el promedio de estrellas correctamente.
- La sección de reseñas se expande/colapsa al hacer clic.
- Las reseñas individuales se ven con estrellas, email y comentario.

**Verificación:**  
```
Abrir la página en el navegador → verificar que las estrellas se ven y las reseñas se cargan
```

---

## Paso 10: Formulario de reseña y eliminación

**Archivo:** `src/static/app.js`  
**Objetivo:** Implementar el formulario interactivo de nueva reseña y el botón de eliminar.

**Tareas:**
- Crear función `renderReviewForm(activityName)` que genera:
  - Input de email
  - Selector de estrellas interactivo (clicable, con highlight al hacer hover)
  - Textarea para comentario (con contador de caracteres)
  - Botón "Submit Review"
- Crear función `submitReview(activityName, email, rating, comment)`:
  - Valida que todos los campos estén completos.
  - Hace POST al API con body JSON.
  - Muestra mensaje de éxito/error.
  - Refresca la sección de reseñas de esa tarjeta.
- Crear función `deleteReview(activityName, email)`:
  - Pide confirmación al usuario.
  - Hace DELETE al API.
  - Refresca la sección de reseñas.
- Agregar event listeners para:
  - Click en estrellas del formulario (seleccionar rating).
  - Submit del formulario de reseña.
  - Click en botón de eliminar reseña.

**Criterio de éxito:**  
- Se puede crear una reseña desde la UI con estrellas clicables.
- Se puede eliminar una reseña propia.
- Los mensajes de éxito/error aparecen correctamente.
- Las estrellas del formulario responden al hover y click.

**Verificación:**  
```
Crear reseña desde la UI → verificar que aparece
Eliminar reseña → verificar que desaparece
Probar errores (no participante, duplicada) → verificar mensajes
```

---

## Paso 11: Controles de ordenamiento

**Archivos:** `src/static/index.html`, `src/static/app.js`  
**Objetivo:** Agregar la funcionalidad de filtrado/ordenamiento por valoración.

**Tareas:**
- En `index.html`: agregar un `<div class="sort-controls">` con un `<select>` encima de `activities-list` con opciones: "Default", "Best rated first", "Lowest rated first".
- En `app.js`: crear función `sortActivities(criteria)`:
  - Lee las tarjetas del DOM.
  - Extrae el promedio de estrellas de cada una.
  - Reordena los elementos del DOM según el criterio.
  - Actividades sin reseñas van al final.
- Agregar event listener al `<select>` de ordenamiento que llama a `sortActivities()`.

**Criterio de éxito:**  
- El dropdown de ordenamiento aparece encima de la lista de actividades.
- Seleccionar "Best rated first" reordena las tarjetas de mayor a menor rating.
- Seleccionar "Default" restaura el orden original.

**Verificación:**  
```
Crear varias reseñas con diferentes ratings → usar el dropdown → verificar que el orden cambia
```

---

## Paso 12: Integración completa y test final

**Archivos:** Todos  
**Objetivo:** Validación integral de todo el sistema.

**Tareas:**
- Ejecutar `pytest -v` → todos los tests pasan (existentes + nuevos).
- Levantar el servidor y probar manualmente en el navegador:
  - Ver actividades con estrellas y conteo de reviews.
  - Crear una reseña desde la UI (probar con participante y no-participante).
  - Ver la reseña creada en la tarjeta.
  - Eliminar la reseña desde la UI.
  - Probar el ordenamiento por valoración.
  - Verificar responsividad en ventana estrecha.
- Verificar que no hay errores en la consola del navegador.
- Revisar que los tests existentes no se rompieron.

**Criterio de éxito:**  
- 0 fallos en pytest.
- Todas las funcionalidades de reseñas operativas en la UI.
- Todos los criterios de aceptación de `User-requirements.md` cumplidos.

**Verificación:**  
```
pytest -v → all green
Checklist manual de criterios de aceptación CA-01 a CA-12
```

---

## Diagrama de Dependencias entre Pasos

```
Paso 1 (Modelo de datos)
  │
  ├──▶ Paso 2 (POST review)
  │      │
  ├──▶ Paso 3 (GET reviews) ◄── depende de Paso 2 para tener datos
  │      │
  ├──▶ Paso 4 (DELETE review) ◄── depende de Paso 2
  │      │
  └──▶ Paso 5 (Modificar GET /activities) ◄── depende de Paso 1
         │
         ▼
Paso 6 (Tests) ◄── depende de Pasos 2,3,4,5
  │
  ▼
Paso 7 (Ejecutar y corregir tests)
  │
  ▼
Paso 8 (CSS) ── independiente, se puede hacer en paralelo con 1-7
  │
  ▼
Paso 9 (Renderizado JS) ◄── depende de Paso 8 (estilos) y Paso 3 (API)
  │
  ▼
Paso 10 (Formulario JS) ◄── depende de Paso 9 y Pasos 2,4 (API)
  │
  ▼
Paso 11 (Ordenamiento) ◄── depende de Paso 9
  │
  ▼
Paso 12 (Integración final) ◄── depende de TODOS los anteriores
```

---

## Instrucciones para el Agente IA

Al ejecutar cada paso, seguir estas reglas:

1. **Leer antes de escribir:** Siempre leer el archivo completo actual antes de editarlo.
2. **Cambios mínimos:** Solo modificar lo que el paso indica. No adelantar trabajo de pasos futuros.
3. **No romper lo existente:** Cada cambio debe mantener la funcionalidad actual intacta.
4. **Tests primero en validación:** Después de cada paso de backend, ejecutar `pytest -v`.
5. **Un paso a la vez:** No combinar pasos. Completar uno, revisar, y luego el siguiente.
6. **Reportar resultado:** Al terminar cada paso, indicar qué se hizo y si hubo algún ajuste.
