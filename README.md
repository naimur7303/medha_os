<p align="center">
  <br>
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square">
  <img src="https://img.shields.io/badge/python-3.x-3b82f6?style=flat-square">
  <img src="https://img.shields.io/badge/flask-SQLite-ffffff?style=flat-square">
  <img src="https://img.shields.io/badge/license-MIT-6b7280?style=flat-square">
  <br><br>
  <strong>M E D H A &nbsp; O S</strong><br>
  <em>people · projects · progress · presence</em>
</p>

---

**Medha OS** is a minimal, dark-mode relationship-and-project operating system — a single-user Flask app to track people, manage projects with Kanban boards, log events with markdown reports, and maintain systemic awareness across everything.

Built for facilitators, community organizers, and research coordinators who need a grounded, structured system to hold the complexity of people and their work.

---

## Features

### 👥 People Directory
- Add, filter, and sort people by name, archetype, caste, agency, and status
- Person profiles with connected projects, assigned tasks, and personal tasks
- Archetype–caste mapping with cascading dropdowns

### 📁 Projects & Kanban
- Create projects with types (Community, Experiential, Knowledge, Media, Startup) and statuses
- Assign people with involvement levels (Core → Active → Occasional → Observer)
- **Kanban board**: drag-free task management — Pending → In Progress → Done → Skipped
  - Undo/back, skip, and delete from every card
  - Click any card to edit Description, Necessary Info, Due Date, Status, and Notes
- Project links with type badges (Repository, Documentation, Design, Deployment)
- Dedicated task detail page

### 📅 Events & Reports
- Log events with date, time, and external links
- **Markdown report editor** with live preview — write reports with headings, bold, italic, lists, and blockquotes
- Track event attendees
- Reports overview with monthly breakdown

### 📊 Dashboard
- At-a-glance stats: people, active links, unassigned, empty projects
- Donut charts for archetype, agency, and project status distributions
- Forgotten people (>7 days), slow projects, and empty projects alerts
- Recent updates feed and upcoming tasks (next 5 by due date)

### 🔍 Sort & Filter
- Sortable column headers — click to sort ascending (▸), click again to remove sort
- Filter panels with search, status, type, date range, archetype, caste, and agency

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| **Framework** | Flask (Python) |
| **Database** | SQLite via SQLAlchemy |
| **Templates** | Jinja2 |
| **Charts** | Chart.js |
| **Markdown** | marked.js |
| **Styling** | Brutalist dark theme (inline CSS) |

---

## Getting Started

```bash
# Clone
git clone https://github.com/naimur7303/medha_os.git
cd medha_os

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Open `http://localhost:5001` in your browser.

---

## Data Model

```
Person ──┬── ProjectPerson ──── Project ──── ProjectLink
         │                                    │
         └── Task (assigned)                  └── Task (project)
         │
         └── Task (personal, no project)
         │
         └── EventAttendee ──── Event
```

- **Person** — name, archetype, caste, agency, status, updated_at
- **Project** — title, description, type, status, updated_at
- **ProjectPerson** — join with involvement level, role, notes
- **Task** — title, description, necessary_info, status, due_date, notes, project or personal
- **Event** — title, description, date, time, link, report_content
- **ProjectLink** — title, URL, type
- **EventAttendee** — event–person join

---

## Design Notes

Medha OS is intentionally brutalist — a dark interface with monospace-adjacent typography, thin borders, no rounded corners, and monochrome with blue accents. The aesthetic favours clarity and structure over polish.

All panels are toggleable. Input panels open on demand, keeping the working surface clean.

---

<p align="center">
  <sub>built with intent · medha os</sub>
</p>
