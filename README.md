# WorkPulse

WorkPulse is a local-first desktop application for development teams, built with Python, Flet, and SQLite.

Its goal is not to compete with a generic project manager or an IDE. It is designed as a technical coordination and execution tool that brings together, in a single compact interface:

- a kanban board oriented around technical tasks
- work focus on one active task
- technical context per task: repo, branch, and local path per user
- task completion with optional or required commit
- pomodoro and work sessions
- local time tracking
- optional synchronization using a private Git repository as the backend

All primary state lives locally. Synchronization is optional. Without sync, WorkPulse still works at 100%.

## What It Solves

WorkPulse is designed for the case where a developer needs to quickly answer questions like:

- what task am I working on right now
- which branch and repo are associated with that task
- whether that task requires a commit before closing
- where the correct local path for that repo is on this machine
- what the rest of the team has been doing based on the last known state
- which focus sessions, pomodoros, or time tracking entries were recorded today
- which changes are still pending synchronization

## Product Principles

- `Local-first`: the primary state always lives in local SQLite.
- `Offline-friendly`: the application is usable without network access and without a sync repo.
- `Git-native`: sync uses the system Git CLI, not an external backend.
- `Developer-centric`: tasks, branches, repos, commits, and local paths are first-class entities.
- `Compact desktop UI`: floating, pinnable, minimizable, and responsive window.

## Features

### Board

- `Backlog`, `Doing`, `Review`, `Done` columns
- task cards with assignee, repo, branch, priority, and commit policy
- filters by:
  - assigned to the current user
  - repo
  - status
  - commit policy
  - active task
- task editing and movement
- active task selection
- warnings when the repo local path is missing for the current user

### Focus

- large, highlighted active task
- summarized description
- repo, branch, and local path
- warning when the local path is missing
- buttons to open path, start pomodoro, complete task, or clear active task

### Time

- pomodoro with start, pause, resume, and reset
- manual work sessions
- clock in / clock out
- short activity history
- metrics derived from real state, not fake numbers

### Team

- workspace members
- `active`, `idle`, `offline` status
- last known activity
- active task
- last clock entry
- last completed task with recorded commit

### Completion Flow

- local repo inspection before closing a task
- current branch reading
- modified files listing
- staged / unstaged
- `none`, `optional`, `required` commit policy
- support for `Close only` and `Close + Commit`
- closing blocked when the policy requires a commit and the Git context is not valid

### Optional Git-Based Sync

- export of snapshots and events to disk
- pull / push / full sync using Git CLI
- private repo chosen by the user or the team
- no own server
- no mandatory SaaS

## Tech Stack

- Python 3.11+
- Flet desktop
- SQLite
- system Git CLI
- `subprocess`
- `pathlib`

## Requirements

- Python 3.11 or higher
- `git` available in `PATH`
- macOS or Linux

On Linux, the Flet desktop runtime may require `libmpv`.

## Installation

### Recommended Installation

From the project root:

```bash
./init.sh
```

`init.sh` does the following:

1. detects macOS or Linux
2. checks for Python 3.11+
3. creates `.venv` if it does not exist
4. updates `pip`
5. installs dependencies from `requirements.txt`
6. creates an executable launcher named `workpulse`
7. installs that launcher in a reasonable user path
8. warns if that path is not in `PATH`

After that, you can start WorkPulse with:

```bash
workpulse
```

### Local Run Without Launcher

```bash
./run.sh
```

## Linux Dependencies and Flet Desktop

### Arch / Manjaro

Install `mpv`:

```bash
sudo pacman -S mpv
```

WorkPulse also includes a local shim in `run.sh` to handle the case where Flet looks for `libmpv.so.1` and the system exposes `libmpv.so.2`.

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install libmpv-dev libmpv2 mpv
```

If the runtime still complains about `libmpv.so.1`, you may need this fallback:

```bash
sudo apt update
sudo apt install libmpv-dev libmpv2
sudo ln -s /usr/lib/x86_64-linux-gnu/libmpv.so /usr/lib/libmpv.so.1
```

### Fedora

```bash
sudo dnf install mpv-libs mpv
```

## First Launch

The first time you open WorkPulse, the logical order is:

1. create a workspace
2. create or select the current local user
3. register logical repos
4. map local paths by user and repo
5. create tasks
6. mark a task as active
7. use pomodoro, work session, or time tracking as needed

## Core Concepts

### Workspace

Groups a team's operational state:

- users
- logical repos
- tasks
- events
- sync configuration

### Logical Repo

It is not a specific local copy. It is a functional entity that identifies a repository inside the workspace:

- display name
- canonical remote or identifier
- default branch

### Local Repo Mapping

Connects a logical repo with a specific local path for a specific user.

This allows the same task to point to the same logical repo while each team member uses their own local path.

### Active Task

Each user can only have one active task at a time.

The active task feeds:

- the `Focus` view
- the automatic association with pomodoro
- the optional association with work sessions

### Event Log

Every important change generates an event in SQLite.

Examples:

- workspace creation
- user creation
- repo creation or update
- mapping updates
- task creation or change
- task movement
- active task
- pomodoro
- clock in / clock out
- task completion

That event log is the basis for the pending changes counter and the sync model.

## Recommended Usage Flow

### 1. Create Workspace

Open the workspace dialog from:

- `Configure now`
- `Settings`
- the top workspace selector

Enter:

- workspace name
- optional initial user

### 2. Create Users

Open `Settings -> Manage users`.

You can:

- create local workspace users
- select the current user for this machine

### 3. Register Repos

Open `Settings -> Manage repos`.

For each logical repo:

- define display name
- define canonical remote
- define default branch

Then create the mappings:

- select repo
- select user
- assign local path

### 4. Create Tasks

In `Board` you can create tasks with:

- title
- description
- assignee
- status
- priority
- tags
- repo
- branch
- commit policy

### 5. Mark Active Task

You can do this from:

- the card action menu
- the task detail panel

If you switch to another one, the previous task is replaced.

### 6. Work in Focus

The `Focus` view uses the current active task and shows:

- technical context
- local path
- quick action buttons
- focus state

### 7. Track Time

In `Time` you can:

- start a pomodoro
- pause or resume it
- start and close work sessions
- clock in / clock out

### 8. Close Task With Commit

When you use `Mark as Done`, WorkPulse:

1. checks whether the task has a repo
2. looks up the current user's local mapping
3. verifies that the path exists
4. verifies that it is a valid Git repo
5. gets the current branch
6. gets short status
7. shows modified files and staged / unstaged

Possible actions:

- `Close only`
- `Close + Commit`

If the policy is `required`, `Close only` is blocked.

By default, empty commits are not allowed.

## How Sync Works

Sync is optional and uses a private Git repository as the backend.

### What Stays Local

Always local:

- primary SQLite database
- local settings
- logs
- window state

### What Gets Exported to the Sync Repo

Inside the configured repo, the following is written:

```text
workpulse-sync/
  workspace.json
  users.json
  repos.json
  events/YYYY-MM-DD.jsonl
  snapshots/latest.json
```

### Sync Actions

From `Settings -> Sync`:

- `Init sync repo`
- `Pull`
- `Push`
- `Full sync`

### What Each One Does

`Init sync repo`

- prepares the local metadata repo
- ensures the configured branch
- configures `origin` if there is a remote URL

`Pull`

- runs `git pull --rebase`
- imports remote snapshot into the local model

`Push`

- exports local state
- runs `git add`
- creates an automatic commit if there are changes
- runs `git push`

`Full sync`

1. validates the sync repo
2. `git pull --rebase`
3. imports remote state
4. exports local state
5. `git add`
6. automatic commit if there are changes
7. `git push`
8. marks events as synchronized

### What the Pending Counter Means

`Pending` is not a fake number.

It counts the local workspace events whose `synced_at` is still `NULL`.

In other words:

- if you make local changes and sync is enabled, `Pending` goes up
- when sync finishes successfully, those events are marked as synchronized
- if sync is disabled, the footer shows `Sync off`

## Desktop Window

WorkPulse uses the Flet desktop API for:

- width
- height
- position
- minimized
- always-on-top
- resize

Geometry can optionally be persisted.

Default behavior:

- Linux: floating geometry biased to the left
- macOS: floating geometry biased to the right

## Data and Storage

### SQLite

The local database stores:

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

### Local Settings

These are stored separately:

- theme
- window preferences
- restored workspace
- current user
- sync preferences
- pomodoro configuration

### Logs

Local logs are generated for:

- application
- sync
- Git

On Linux and macOS, the data directory is resolved automatically and, if the preferred path is not writable, WorkPulse uses a safe fallback.

You can also force the path with:

```bash
WORKPULSE_DATA_DIR=/custom/path ./run.sh
```

## Project Structure

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

## Troubleshooting

### `libmpv.so.1` Not Found on Linux

Install `mpv` according to your distro. On Arch / Manjaro this is usually enough:

```bash
sudo pacman -S mpv
```

`run.sh` also tries to automatically handle the case where the system has `libmpv.so.2`.

### The `workpulse` Launcher Is Not Found

Check that the path is in `PATH`:

```bash
echo $PATH
```

The launcher is usually installed in:

- `~/.local/bin/workpulse`
- or `~/bin/workpulse`

### Sync Does Nothing

Check:

- that the workspace has `Enable sync` enabled
- that the `sync repo local path` exists
- that this path is a valid Git repo
- that the branch is correctly configured
- that the remote and credentials work

### A Button Appears Disabled

That usually means the current state does not allow that action.

Examples:

- `Clock Out` disabled if you are not `clocked in`
- `Pause` disabled if no pomodoro is running
- `Pull/Push/Full sync` disabled if sync is not configured
- `Open path` disabled if there is no valid local path

## Current Version Limitations

- task movement is handled through menu actions, not native drag and drop
- sync conflict resolution is deliberately simple
- there is no realtime presence
- sync depends on Git and system credentials being correctly configured
- the focus model is single-user per machine, although the workspace supports multiple users

## Development

Typical flow:

```bash
./init.sh
./run.sh
```

or:

```bash
workpulse
```

## Summary

WorkPulse is meant to be a technical control point for daily work:

- which task you are executing
- which repo and branch you are working on
- whether you can close it without a commit
- which work sessions you have recorded
- what the team knows about the current state
- what is still pending synchronization

If what you need is lightweight technical coordination, local-first, and Git-friendly, that is exactly the tool it is trying to be.
