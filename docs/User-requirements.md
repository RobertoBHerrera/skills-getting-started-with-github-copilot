# User Requirements — Sistema de Reseñas y Valoraciones de Actividades

## 1. Visión General

Mergington High School necesita que los estudiantes inscritos en actividades extracurriculares puedan **dejar reseñas públicas** (valoración de 1 a 5 estrellas + comentario de texto) sobre las actividades en las que participan. Esto permite a otros estudiantes tomar decisiones más informadas al elegir actividades y promueve la mejora continua de cada programa.

---

## 2. User Stories

### US-01: Dejar una reseña
**Como** estudiante inscrito en una actividad,  
**quiero** poder dejar una valoración de 1 a 5 estrellas y un comentario sobre esa actividad,  
**para que** otros estudiantes sepan qué esperar antes de inscribirse.

### US-02: Ver reseñas de una actividad
**Como** cualquier visitante del sitio,  
**quiero** ver las reseñas existentes y el promedio de estrellas de cada actividad directamente en su tarjeta,  
**para que** pueda evaluar la calidad de la actividad antes de inscribirme.

### US-03: Filtrar actividades por valoración
**Como** estudiante que busca actividades,  
**quiero** poder filtrar y/o ordenar las actividades por su promedio de valoración (de mayor a menor o viceversa),  
**para que** pueda encontrar rápidamente las mejor evaluadas.

### US-04: Eliminar mi propia reseña
**Como** estudiante que dejó una reseña,  
**quiero** poder eliminar mi reseña de una actividad,  
**para que** pueda corregir o retirar mi opinión si cambio de parecer.

### US-05: Una reseña por estudiante por actividad
**Como** sistema,  
**necesito** que cada estudiante solo pueda dejar **una única reseña** por actividad,  
**para que** las valoraciones sean justas y no se puedan manipular.

---

## 3. Requisitos Funcionales

### RF-01: Crear reseña
- El sistema debe permitir crear una reseña asociada a una actividad específica.
- La reseña contiene: `email` del autor, `rating` (entero 1-5), `comment` (texto, máximo 500 caracteres).
- Solo un estudiante que aparece en la lista de `participants` de esa actividad puede crear una reseña.
- Un estudiante solo puede dejar una reseña por actividad (unicidad email + actividad).

### RF-02: Leer reseñas
- El sistema debe exponer todas las reseñas de una actividad específica.
- Cada reseña debe incluir: email del autor, rating, comentario y timestamp de creación.
- El sistema debe calcular y devolver el promedio de valoración (`average_rating`) de cada actividad.

### RF-03: Eliminar reseña
- El autor de una reseña puede eliminarla proporcionando su email.
- Solo se puede eliminar una reseña propia (validación de autoría por email).

### RF-04: Obtener actividades con promedio de valoración
- El endpoint existente `GET /activities` debe incluir un campo nuevo `average_rating` (float, 1 decimal) y `review_count` (int) en cada actividad.
- Si no hay reseñas, `average_rating` será `null` y `review_count` será `0`.

### RF-05: Filtrar y ordenar actividades
- El endpoint `GET /activities` debe soportar un query parameter opcional `sort_by` con valores: `rating_asc`, `rating_desc`.
- Actividades sin reseñas se colocan al final cuando se ordena por rating.

### RF-06: Interfaz de estrellas interactiva
- En el frontend, cada tarjeta de actividad debe mostrar el promedio de estrellas de forma visual (estrellas llenas, medias, vacías).
- Debe existir un formulario de reseña con un selector de estrellas clicable (1-5) y un campo de texto para el comentario.
- Las reseñas existentes se muestran en una sección expandible/colapsable dentro de cada tarjeta.

### RF-07: Mensajes de feedback en UI
- Al crear o eliminar una reseña, se debe mostrar un mensaje de éxito o error visible al usuario.
- Los errores de validación (no inscrito, duplicado, texto vacío) deben mostrarse claramente.

---

## 4. Requisitos No Funcionales

| ID | Requisito | Detalle |
|----|-----------|---------|
| RNF-01 | Rendimiento | Las operaciones de reseña deben responder en < 200ms (datos en memoria) |
| RNF-02 | Compatibilidad | Funcionar en Chrome, Firefox, Edge, Safari (últimas 2 versiones) |
| RNF-03 | Responsividad | La UI de reseñas debe ser usable en pantallas ≥ 320px de ancho |
| RNF-04 | Accesibilidad | Los componentes de estrellas deben ser navegables por teclado y tener atributos ARIA |
| RNF-05 | Consistencia | El diseño visual de reseñas debe seguir la paleta y tipografía existente (#1a237e, #0066cc, Arial) |
| RNF-06 | Mantenibilidad | El código nuevo debe seguir los patrones ya establecidos en el proyecto (in-memory dict, vanilla JS, patrón AAA en tests) |

---

## 5. Reglas de Negocio

| # | Regla | Descripción |
|---|-------|-------------|
| RN-01 | Solo participantes pueden reseñar | Si el email no está en `activity["participants"]`, la reseña se rechaza con 403 |
| RN-02 | Una reseña por persona por actividad | Si ya existe una reseña del mismo email para esa actividad, se rechaza con 400 |
| RN-03 | Rating obligatorio entre 1 y 5 | Valores fuera de rango se rechazan con 422 |
| RN-04 | Comentario obligatorio y limitado | El comentario no puede estar vacío ni exceder 500 caracteres. Se rechaza con 400 |
| RN-05 | Solo el autor puede eliminar su reseña | Un email solo puede eliminar reseñas que creó él mismo. Se rechaza con 403 si no es el autor |
| RN-06 | El promedio se recalcula en cada lectura | No se almacena un promedio precalculado; se calcula dinámicamente a partir de las reseñas existentes |
| RN-07 | Las reseñas persisten independientemente | Si un estudiante se desinscribe de una actividad, sus reseñas **se mantienen** (ya participó y su opinión es válida) |

---

## 6. Criterios de Aceptación

### CA-01: Creación exitosa de reseña
- **Dado** que el estudiante `emma@mergington.edu` está inscrito en "Programming Class"
- **Cuando** envía una reseña con rating=5 y comment="Excellent class, learned a lot!"
- **Entonces** la API responde 200 con mensaje de confirmación
- **Y** la reseña aparece en la lista de reseñas de "Programming Class"
- **Y** el promedio de valoración se actualiza correctamente

### CA-02: Rechazo a no participante
- **Dado** que `stranger@mergington.edu` NO está inscrito en "Chess Club"
- **Cuando** intenta dejar una reseña en "Chess Club"
- **Entonces** la API responde 403 con detalle "Only participants can leave reviews"

### CA-03: Rechazo a reseña duplicada
- **Dado** que `emma@mergington.edu` ya dejó una reseña en "Programming Class"
- **Cuando** intenta dejar otra reseña en la misma actividad
- **Entonces** la API responde 400 con detalle "You have already reviewed this activity"

### CA-04: Eliminación de reseña propia
- **Dado** que `emma@mergington.edu` tiene una reseña en "Programming Class"
- **Cuando** envía una solicitud DELETE con su email
- **Entonces** la reseña se elimina y el promedio se recalcula

### CA-05: Rechazo a eliminar reseña ajena
- **Dado** que `emma@mergington.edu` tiene una reseña en "Programming Class"
- **Cuando** `sophia@mergington.edu` intenta eliminar esa reseña
- **Entonces** la API responde 403 con detalle "You can only delete your own review"

### CA-06: Validación de rating
- **Cuando** se envía un rating de 0 o 6
- **Entonces** la API responde 422 (validación de Pydantic/FastAPI)

### CA-07: Validación de comentario vacío
- **Cuando** se envía un comentario vacío o solo espacios
- **Entonces** la API responde 400 con detalle "Comment cannot be empty"

### CA-08: Validación de comentario largo
- **Cuando** se envía un comentario de más de 500 caracteres
- **Entonces** la API responde 400 con detalle "Comment must be 500 characters or less"

### CA-09: Promedio visible en tarjeta (Frontend)
- **Dado** que "Chess Club" tiene reseñas con ratings [4, 5, 3]
- **Cuando** el usuario carga la página
- **Entonces** la tarjeta de "Chess Club" muestra 4.0 estrellas (promedio visual) y "(3 reviews)"

### CA-10: Ordenamiento por valoración
- **Cuando** el usuario selecciona "Ordenar por: Mejor valoradas"
- **Entonces** las tarjetas se reordenan de mayor a menor promedio de estrellas
- **Y** las actividades sin reseñas aparecen al final

### CA-11: Formulario de reseña (Frontend)
- **Dado** que el usuario ve una tarjeta de actividad
- **Cuando** hace clic en las estrellas y escribe un comentario y presiona "Submit Review"
- **Entonces** se envía la petición POST y la reseña aparece inmediatamente en la tarjeta

### CA-12: Actividad inexistente
- **Cuando** se intenta crear una reseña para una actividad que no existe
- **Entonces** la API responde 404 con detalle "Activity not found"

---

## 7. Fuera de Alcance (Out of Scope)

- **Edición de reseñas:** no se puede editar una reseña, solo eliminar y crear una nueva.
- **Autenticación real:** la identidad se basa en el email proporcionado (consistente con el sistema actual).
- **Persistencia en base de datos:** las reseñas se almacenan en memoria (consistente con el patrón actual del proyecto).
- **Reseñas anónimas:** toda reseña debe estar asociada a un email.
- **Respuestas a reseñas:** no se implementan hilos de comentarios ni respuestas.
- **Reportar reseñas ofensivas:** no se implementa sistema de reportes ni moderación por contenido.
