[Español](README.es.md) | [English](README.en.md)

---

# WorkPulse

WorkPulse es una aplicacion de escritorio local-first para equipos de desarrollo, creada con Python, Flet y SQLite.

No intenta competir con un gestor generico de proyectos ni con un IDE. Es una herramienta tecnica de coordinacion y ejecucion que reune en una interfaz compacta:

- tablero kanban orientado a tareas tecnicas,
- foco de trabajo en una tarea activa,
- contexto tecnico por tarea: repo, rama y ruta local,
- cierre de tareas con commit opcional u obligatorio,
- pomodoro y sesiones de trabajo,
- seguimiento local de tiempo,
- sincronizacion opcional mediante un repositorio Git privado.

Todo el estado principal vive localmente. La sincronizacion es opcional.

## Que resuelve

Ayuda a responder rapidamente:

- en que tarea estoy trabajando,
- que rama y repositorio pertenecen a esa tarea,
- si la tarea requiere commit antes de cerrarse,
- cual es la ruta local correcta en esta maquina,
- que hizo el resto del equipo segun el ultimo estado sincronizado,
- que sesiones o pomodoros se registraron hoy,
- que cambios faltan por sincronizar.

## Principios

- `Local-first`: SQLite local como fuente principal.
- `Offline-friendly`: funciona sin red ni repo de sincronizacion.
- `Git-native`: la sincronizacion usa Git CLI.
- `Developer-centric`: tareas, ramas, repos y commits son entidades principales.
- `Compact desktop UI`: ventana flotante, fijable y responsive.

## Funciones

### Board

Columnas `Backlog`, `Doing`, `Review` y `Done`, tarjetas con responsable, repo, rama, prioridad y politica de commit, filtros y seleccion de tarea activa.

### Focus

Vista destacada de la tarea activa con descripcion, repo, rama, ruta local y acciones para abrir ruta, iniciar pomodoro, completar o limpiar seleccion.

### Time

Pomodoro, sesiones manuales, clock in/out, historial y metricas derivadas de estado real.

### Team

Miembros, estado, ultima actividad, tarea activa, ultima entrada de reloj y ultima tarea completada con commit.

### Sincronizacion

Sincronizacion opcional con repositorio Git privado para compartir estado entre miembros sin backend central.

## Instalacion y ejecucion

Consulta la version inglesa para detalles completos si necesitas todas las opciones avanzadas, pero el flujo habitual es ejecutar el instalador local del proyecto y arrancar la app desde el entorno virtual creado.
