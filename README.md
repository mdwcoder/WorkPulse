# WorkPulse

WorkPulse es una aplicación desktop local-first para equipos de desarrollo, construida con Python, Flet y SQLite.

Su objetivo no es competir con un gestor genérico de proyectos ni con un IDE. Está pensada como una herramienta técnica de coordinación y ejecución que une, en una sola interfaz compacta:

- tablero kanban orientado a tareas técnicas
- foco de trabajo sobre una tarea activa
- contexto técnico por tarea: repo, rama y path local por usuario
- cierre de tareas con commit opcional o requerido
- pomodoro y sesiones de trabajo
- fichaje local
- sincronización opcional usando un repositorio Git privado como backend

Todo el estado principal vive en local. La sincronización es opcional. Sin sync, WorkPulse sigue funcionando al 100%.

## Qué resuelve

WorkPulse está diseñado para el caso en el que un desarrollador necesita responder rápido a preguntas como:

- en qué tarea estoy trabajando ahora mismo
- qué rama y qué repo están asociados a esa tarea
- si esa tarea requiere commit para cerrarse
- dónde está el path local correcto para ese repo en esta máquina
- qué ha estado haciendo el resto del equipo según el último estado conocido
- qué sesiones de foco, pomodoro o fichaje se han registrado hoy
- qué cambios siguen pendientes de sincronizar

## Principios del producto

- `Local-first`: el estado principal siempre vive en SQLite local.
- `Offline-friendly`: la aplicación es usable sin red y sin repo de sync.
- `Git-native`: la sync usa Git CLI del sistema, no un backend externo.
- `Developer-centric`: tareas, ramas, repos, commits y paths locales son entidades de primera clase.
- `Compact desktop UI`: ventana flotante, pineable, minimizable y responsive.

## Funcionalidades

### Board

- columnas `Backlog`, `Doing`, `Review`, `Done`
- tarjetas de tarea con assignee, repo, branch, prioridad y commit policy
- filtros por:
  - asignadas al usuario actual
  - repo
  - status
  - commit policy
  - tarea activa
- edición y movimiento de tareas
- selección de tarea activa
- warnings cuando falta el path local del repo para el usuario actual

### Focus

- tarea activa grande y destacada
- descripción resumida
- repo, branch y local path
- warning si falta el path local
- botones para abrir path, iniciar pomodoro, completar tarea o limpiar tarea activa

### Time

- pomodoro con start, pause, resume y reset
- work sessions manuales
- clock in / clock out
- historial corto de actividad
- métricas derivadas del estado real, no de números fake

### Team

- miembros del workspace
- estado `active`, `idle`, `offline`
- última actividad conocida
- tarea activa
- último fichaje
- última tarea completada con commit registrado

### Completion Flow

- inspección del repo local antes de cerrar tarea
- lectura de branch actual
- listado de ficheros modificados
- staged / unstaged
- commit policy `none`, `optional`, `required`
- soporte para `Close only` y `Close + Commit`
- bloqueo de cierre cuando la policy requiere commit y el contexto Git no es válido

### Sync opcional por Git

- export de snapshots y eventos a disco
- pull / push / full sync usando Git CLI
- repo privado elegido por el usuario o por el equipo
- sin servidor propio
- sin SaaS obligatorio

## Stack técnico

- Python 3.11+
- Flet desktop
- SQLite
- Git CLI del sistema
- `subprocess`
- `pathlib`

## Requisitos

- Python 3.11 o superior
- `git` disponible en `PATH`
- macOS o Linux

En Linux, el runtime desktop de Flet puede necesitar `libmpv`.

## Instalación

### Instalación recomendada

Desde la raíz del proyecto:

```bash
./init.sh
```

`init.sh` hace lo siguiente:

1. detecta macOS o Linux
2. comprueba Python 3.11+
3. crea `.venv` si no existe
4. actualiza `pip`
5. instala dependencias desde `requirements.txt`
6. crea un launcher ejecutable llamado `workpulse`
7. instala ese launcher en una ruta de usuario razonable
8. avisa si esa ruta no está en `PATH`

Después puedes arrancar WorkPulse con:

```bash
workpulse
```

### Ejecución local sin launcher

```bash
./run.sh
```

## Dependencias Linux y Flet desktop

### Arch / Manjaro

Instala `mpv`:

```bash
sudo pacman -S mpv
```

WorkPulse incluye además un shim local en `run.sh` para compatibilizar el caso en el que Flet busque `libmpv.so.1` y el sistema exponga `libmpv.so.2`.

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install libmpv-dev libmpv2 mpv
```

Si el runtime sigue quejándose de `libmpv.so.1`, puedes necesitar este fallback:

```bash
sudo apt update
sudo apt install libmpv-dev libmpv2
sudo ln -s /usr/lib/x86_64-linux-gnu/libmpv.so /usr/lib/libmpv.so.1
```

### Fedora

```bash
sudo dnf install mpv-libs mpv
```

## Primer arranque

La primera vez que abras WorkPulse, el orden lógico es este:

1. crear un workspace
2. crear o seleccionar el usuario local actual
3. registrar repos lógicos
4. mapear paths locales por usuario y repo
5. crear tareas
6. marcar una tarea como activa
7. usar pomodoro, work session o fichaje según necesites

## Conceptos principales

### Workspace

Agrupa el estado operativo de un equipo:

- usuarios
- repos lógicos
- tareas
- eventos
- configuración de sync

### Repo lógico

No es una copia local concreta. Es una entidad funcional que identifica un repositorio dentro del workspace:

- nombre visible
- remote canónico o identificador
- branch por defecto

### Repo local mapping

Conecta un repo lógico con un path local concreto para un usuario concreto.

Esto permite que la misma tarea apunte al mismo repo lógico, pero cada miembro del equipo use su propio path local.

### Tarea activa

Cada usuario puede tener solo una tarea activa a la vez.

La tarea activa alimenta:

- la vista `Focus`
- la asociación automática con pomodoro
- la asociación opcional con work sessions

### Event log

Cada cambio importante genera un evento en SQLite.

Ejemplos:

- creación de workspace
- creación de usuario
- creación o actualización de repo
- actualización de mappings
- creación o cambio de tarea
- movimiento de tarea
- tarea activa
- pomodoro
- clock in / clock out
- cierre de tarea

Ese event log es la base del contador de cambios pendientes y del modelo de sync.

## Flujo de uso recomendado

### 1. Crear workspace

Abre el diálogo de workspace desde:

- `Configure now`
- `Settings`
- selector superior de workspace

Introduce:

- nombre del workspace
- usuario inicial opcional

### 2. Crear usuarios

Abre `Settings -> Manage users`.

Puedes:

- crear usuarios locales del workspace
- seleccionar el usuario actual de esta máquina

### 3. Registrar repos

Abre `Settings -> Manage repos`.

Para cada repo lógico:

- define nombre visible
- define remote canónico
- define branch por defecto

Después crea los mappings:

- selecciona repo
- selecciona usuario
- asigna path local

### 4. Crear tareas

En `Board` puedes crear tareas con:

- título
- descripción
- assignee
- status
- prioridad
- tags
- repo
- branch
- commit policy

### 5. Marcar tarea activa

Puedes hacerlo desde:

- menú de acciones de la tarjeta
- panel de detalle de la tarea

Si cambias a otra, la anterior se sustituye.

### 6. Trabajar en Focus

La vista `Focus` usa la tarea activa actual y muestra:

- contexto técnico
- path local
- botones de acción rápida
- estado de foco

### 7. Registrar tiempo

En `Time` puedes:

- lanzar un pomodoro
- pausarlo o reanudarlo
- iniciar y cerrar work sessions
- hacer clock in / clock out

### 8. Cerrar tarea con commit

Cuando usas `Mark as Done`, WorkPulse:

1. revisa si la tarea tiene repo
2. busca el mapping local del usuario actual
3. comprueba si la ruta existe
4. comprueba si es un repo Git válido
5. obtiene branch actual
6. obtiene status corto
7. muestra archivos modificados y staged / unstaged

Acciones posibles:

- `Close only`
- `Close + Commit`

Si la policy es `required`, `Close only` queda bloqueado.

Por defecto, no se permiten commits vacíos.

## Cómo funciona la sync

La sync es opcional y usa un repositorio Git privado como backend.

### Qué sigue siendo local

Siempre local:

- base de datos SQLite principal
- settings locales
- logs
- estado de ventana

### Qué se exporta al repo de sync

Dentro del repo configurado se escribe:

```text
workpulse-sync/
  workspace.json
  users.json
  repos.json
  events/YYYY-MM-DD.jsonl
  snapshots/latest.json
```

### Acciones de sync

Desde `Settings -> Sync`:

- `Init sync repo`
- `Pull`
- `Push`
- `Full sync`

### Qué hace cada una

`Init sync repo`

- prepara el repo local de metadata
- garantiza la branch configurada
- configura `origin` si hay remote URL

`Pull`

- hace `git pull --rebase`
- importa snapshot remoto al modelo local

`Push`

- exporta el estado local
- hace `git add`
- crea commit automático si hay cambios
- hace `git push`

`Full sync`

1. valida repo de sync
2. `git pull --rebase`
3. importa estado remoto
4. exporta estado local
5. `git add`
6. commit automático si hay cambios
7. `git push`
8. marca eventos como sincronizados

### Qué significa el contador Pending

`Pending` no es un número fake.

Cuenta los eventos locales del workspace cuyo `synced_at` sigue a `NULL`.

En otras palabras:

- si haces cambios locales y la sync está activada, `Pending` sube
- cuando la sync termina bien, esos eventos se marcan como sincronizados
- si la sync está desactivada, el footer muestra `Sync off`

## Ventana desktop

WorkPulse usa la API desktop de Flet para:

- ancho
- alto
- posición
- minimizado
- always-on-top
- resize

La geometría se puede persistir opcionalmente.

Comportamiento por defecto:

- Linux: geometría flotante sesgada a la izquierda
- macOS: geometría flotante sesgada a la derecha

## Datos y almacenamiento

### SQLite

La base local guarda:

- workspaces
- users
- repos
- repo mappings
- tasks
- active tasks
- pomodoro sessions
- work sessions
- punch records
- event logs

### Settings locales

Se guardan por separado:

- tema
- preferencias de ventana
- workspace restaurado
- usuario actual
- preferencias de sync
- configuración de pomodoro

### Logs

Se generan logs locales de:

- aplicación
- sync
- Git

En Linux y macOS el directorio de datos se resuelve automáticamente y, si la ruta preferida no es escribible, WorkPulse usa un fallback seguro.

También puedes forzar la ruta con:

```bash
WORKPULSE_DATA_DIR=/ruta/personalizada ./run.sh
```

## Estructura del proyecto

```text
workpulse/
  main.py
  init.sh
  run.sh
  requirements.txt
  README.md
  app/
    controllers/
      app_controller.py
      board_controller.py
      settings_controller.py
      sync_controller.py
      task_controller.py
      team_controller.py
      time_controller.py
    ui/
      board_view.py
      completion_dialog.py
      focus_view.py
      header.py
      main_window.py
      repo_dialog.py
      settings_dialog.py
      task_card.py
      task_detail_panel.py
      team_view.py
      theme.py
      time_view.py
      user_dialog.py
      workspace_dialog.py
  core/
    db.py
    enums.py
    models.py
    repositories.py
    services/
      event_service.py
      git_service.py
      pomodoro_service.py
      punch_service.py
      repo_service.py
      sync_service.py
      task_service.py
      window_service.py
      workspace_service.py
    sync/
      conflict_handler.py
      exporter.py
      importer.py
    utils/
      logger.py
      path_utils.py
      platform_utils.py
      time_utils.py
      validators.py
  storage/
    settings_store.py
  assets/
    icon.png
```

## Solución de problemas

### `libmpv.so.1` no encontrado en Linux

Instala `mpv` según tu distro. En Arch / Manjaro suele bastar con:

```bash
sudo pacman -S mpv
```

`run.sh` también intenta resolver automáticamente el caso en el que el sistema tenga `libmpv.so.2`.

### El launcher `workpulse` no se encuentra

Comprueba que la ruta esté en `PATH`:

```bash
echo $PATH
```

El launcher suele instalarse en:

- `~/.local/bin/workpulse`
- o `~/bin/workpulse`

### La sync no hace nada

Revisa:

- que el workspace tenga `Enable sync` activado
- que el `sync repo local path` exista
- que ese path sea un repo Git válido
- que la branch esté bien configurada
- que el remote y las credenciales funcionen

### Un botón aparece deshabilitado

Eso normalmente significa que el estado actual no permite esa acción.

Ejemplos:

- `Clock Out` deshabilitado si no estás `clocked in`
- `Pause` deshabilitado si no hay pomodoro corriendo
- `Pull/Push/Full sync` deshabilitados si la sync no está configurada
- `Open path` deshabilitado si no hay local path válido

## Limitaciones de la versión actual

- el movimiento de tareas está resuelto por acciones de menú, no por drag and drop nativo
- la resolución de conflictos de sync es deliberadamente simple
- no hay presencia realtime
- la sync depende de que Git y las credenciales del sistema estén bien configurados
- el foco es single-user per machine, aunque el workspace soporte varios usuarios

## Desarrollo

Flujo habitual:

```bash
./init.sh
./run.sh
```

o bien:

```bash
workpulse
```

## Resumen

WorkPulse está pensado para ser un punto de control técnico del trabajo diario:

- qué tarea estás ejecutando
- en qué repo y branch estás trabajando
- si puedes cerrarla sin commit o no
- qué sesiones de trabajo has registrado
- qué sabe el equipo del estado actual
- qué sigue pendiente de sincronizar

Si lo que necesitas es coordinación técnica ligera, local-first y Git-friendly, esa es exactamente la herramienta que intenta ser.
