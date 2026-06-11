import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medha.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=True)
    primary_archetype = db.Column(db.String(10), nullable=True)
    caste = db.Column(db.String(10), nullable=True)
    agency = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(50), default='Active')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    projects = db.relationship('ProjectPerson', back_populates='person')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Active')
    project_type = db.Column(db.String(50), default='community')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    people = db.relationship('ProjectPerson', back_populates='project')

class ProjectPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    what_the_person_is_doing = db.Column(db.String(200), nullable=True)
    involvement_level = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    project = db.relationship('Project', back_populates='people')
    person = db.relationship('Person', back_populates='projects')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    owner_person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    necessary_info = db.Column(db.Text, nullable=True)
    assigned_person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=True)
    status = db.Column(db.String(50), default='Pending')
    due_date = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))
    assigned_person = db.relationship('Person', foreign_keys=[assigned_person_id], backref=db.backref('assigned_tasks', lazy=True))
    owner = db.relationship('Person', foreign_keys=[owner_person_id], backref=db.backref('owned_tasks', lazy=True))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.String(50), nullable=True)
    event_time = db.Column(db.String(50), nullable=True)
    event_link = db.Column(db.String(500), nullable=True)
    report_content = db.Column(db.Text, nullable=True)

class ProjectLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    title = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(500), nullable=False)
    link_type = db.Column(db.String(50), default='general')
    project = db.relationship('Project', backref=db.backref('links', lazy=True))

class EventAttendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    event = db.relationship('Event', backref=db.backref('attendees', lazy=True))
    person = db.relationship('Person', backref=db.backref('events_attended', lazy=True))

def organize_kanban(tasks):
    columns = {'Pending': [], 'In Progress': [], 'Done': [], 'Skipped': []}
    for t in tasks:
        status = t.status if t.status in columns else 'Pending'
        columns[status].append(t)
    return columns

# Routes
@app.route('/')
def dashboard():
    people = Person.query.all()
    projects = Project.query.all()
    relations = ProjectPerson.query.all()
    now = datetime.utcnow()

    archetype_counts = {'B': 0, 'W': 0, 'M': 0, 'S': 0}
    agency_counts = {'High': 0, 'Medium': 0, 'Low': 0}
    forgotten_people = []
    unassigned_people_list = []

    for p in people:
        if p.primary_archetype in archetype_counts:
            archetype_counts[p.primary_archetype] += 1
        if p.agency in agency_counts:
            agency_counts[p.agency] += 1
        if not p.projects:
            unassigned_people_list.append(p)
        if p.updated_at:
            days = (now - p.updated_at).days
            if days >= 7:
                p.days_since_update = days
                forgotten_people.append(p)
    forgotten_people.sort(key=lambda x: x.days_since_update, reverse=True)

    project_status_counts = {'Active': 0, 'Paused': 0, 'Occasional': 0, 'Waiting': 0}
    project_type_counts = {'experiential': 0, 'knowledge': 0, 'community': 0, 'media': 0, 'startup': 0}
    slow_projects = []
    empty_projects_list = []
    for pr in projects:
        if pr.status in project_status_counts:
            project_status_counts[pr.status] += 1
        if pr.project_type and pr.project_type in project_type_counts:
            project_type_counts[pr.project_type] += 1
        elif pr.project_type:
            project_type_counts[pr.project_type] = 1
        if not pr.people:
            empty_projects_list.append(pr)
        if pr.updated_at:
            days = (now - pr.updated_at).days
            if days >= 7:
                pr.days_since_update = days
                slow_projects.append(pr)
    slow_projects.sort(key=lambda x: x.days_since_update, reverse=True)

    recent_updates = []
    for p in people:
        if p.updated_at:
            recent_updates.append({'type': 'Person', 'name': p.name, 'updated_at': p.updated_at})
    for pr in projects:
        if pr.updated_at:
            recent_updates.append({'type': 'Project', 'name': pr.title, 'updated_at': pr.updated_at})
    recent_updates.sort(key=lambda x: x['updated_at'], reverse=True)
    recent_updates = recent_updates[:10]

    # Upcoming tasks: next 5 non-Done tasks sorted by due_date
    upcoming_tasks = Task.query.filter(Task.status.in_(['Pending', 'In Progress'])).filter(Task.due_date != None).order_by(Task.due_date.asc()).limit(5).all()

    return render_template('dashboard.html',
        people_count=len(people), projects_count=len(projects),
        archetype_counts=archetype_counts, agency_counts=agency_counts,
        project_status_counts=project_status_counts, project_type_counts=project_type_counts,
        total_active_relations=len(relations),
        unassigned_people=len(unassigned_people_list),
        projects_with_no_people=len(empty_projects_list),
        forgotten_people=forgotten_people, slow_projects=slow_projects,
        unassigned_people_list=unassigned_people_list,
        empty_projects_list=empty_projects_list,
        recent_updates=recent_updates,
        upcoming_tasks=upcoming_tasks)

@app.route('/people', methods=['GET', 'POST'])
def people():
    if request.method == 'POST':
        name = request.form.get('name')
        primary_archetype = request.form.get('primary_archetype')
        caste = request.form.get('caste')
        agency = request.form.get('agency')
        status = request.form.get('status')
        if name:
            new_person = Person(name=name, primary_archetype=primary_archetype, caste=caste, agency=agency, status=status)
            db.session.add(new_person)
            db.session.commit()
        return redirect(url_for('people'))

    query = Person.query
    search = request.args.get('search')
    status_filter = request.args.get('status')
    agency_filter = request.args.get('agency')
    archetype_filter = request.args.get('archetype')
    caste_filter = request.args.get('caste')
    if search:
        query = query.filter(Person.name.ilike(f'%{search}%'))
    if status_filter:
        query = query.filter(Person.status == status_filter)
    if agency_filter:
        query = query.filter(Person.agency == agency_filter)
    if archetype_filter:
        query = query.filter(Person.primary_archetype == archetype_filter)
    if caste_filter:
        query = query.filter(Person.caste == caste_filter)

    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    valid_sort_columns = {'name': Person.name, 'primary_archetype': Person.primary_archetype, 'caste': Person.caste, 'agency': Person.agency, 'status': Person.status}
    if sort_by and sort_by != '_':
        col = valid_sort_columns.get(sort_by, Person.name)
        query = query.order_by(col.desc() if sort_order == 'desc' else col.asc())

    all_people = query.all()
    all_projects = Project.query.all()
    return render_template('people.html', people=all_people, projects=all_projects, sort_by=sort_by, sort_order=sort_order,
        applied_filters={'search': search, 'status': status_filter, 'agency': agency_filter, 'archetype': archetype_filter, 'caste': caste_filter})

@app.route('/person/<int:id>')
def person_detail(id):
    person = Person.query.get_or_404(id)
    assigned_tasks = Task.query.filter_by(assigned_person_id=id).all()
    personal_tasks = Task.query.filter_by(owner_person_id=id, project_id=None).all()
    kanban_columns = organize_kanban(assigned_tasks)
    personal_kanban = organize_kanban(personal_tasks)
    return render_template('person_detail.html', person=person, kanban_columns=kanban_columns, personal_kanban=personal_kanban)

@app.route('/person/<int:person_id>/add_personal_task', methods=['POST'])
def add_personal_task(person_id):
    title = request.form.get('title')
    if title:
        task = Task(
            title=title,
            owner_person_id=person_id,
            status=request.form.get('status', 'Pending'),
            due_date=request.form.get('due_date'),
            notes=request.form.get('notes'),
            description=request.form.get('description', ''),
            necessary_info=request.form.get('necessary_info', '')
        )
        db.session.add(task)
        db.session.commit()
    return redirect(url_for('person_detail', id=person_id))

@app.route('/projects', methods=['GET', 'POST'])
def projects():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        status = request.form.get('status', 'Active')
        project_type = request.form.get('project_type', 'community')
        person_ids = request.form.getlist('person_ids')
        if title:
            new_project = Project(title=title, description=description, status=status, project_type=project_type)
            db.session.add(new_project)
            db.session.flush()
            seen_ids = set()
            for pid in person_ids:
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    db.session.add(ProjectPerson(project_id=new_project.id, person_id=int(pid), involvement_level='Active', what_the_person_is_doing='', notes=''))
            db.session.commit()
        return redirect(url_for('projects'))

    query = Project.query
    type_filter = request.args.get('project_type')
    status_filter = request.args.get('status')
    search = request.args.get('search')
    if search:
        query = query.filter(Project.title.ilike(f'%{search}%'))
    if type_filter:
        query = query.filter(Project.project_type == type_filter)
    if status_filter:
        query = query.filter(Project.status == status_filter)

    sort_by = request.args.get('sort_by', 'title')
    sort_order = request.args.get('sort_order', 'asc')
    valid_sort_columns = {'title': Project.title, 'project_type': Project.project_type, 'status': Project.status}
    if sort_by and sort_by != '_':
        col = valid_sort_columns.get(sort_by, Project.title)
        query = query.order_by(col.desc() if sort_order == 'desc' else col.asc())

    all_projects = query.all()
    all_people = Person.query.all()
    return render_template('projects.html', projects=all_projects, all_people=all_people, sort_by=sort_by, sort_order=sort_order,
        applied_filters={'project_type': type_filter, 'status': status_filter, 'search': search})

@app.route('/project/<int:id>')
def project_detail(id):
    project = Project.query.get_or_404(id)
    assigned_person_ids = [rel.person_id for rel in project.people]
    available_people = Person.query.filter(~Person.id.in_(assigned_person_ids)).all() if assigned_person_ids else Person.query.all()
    kanban_columns = organize_kanban(project.tasks)
    return render_template('project_detail.html', project=project, available_people=available_people, kanban_columns=kanban_columns)

@app.route('/project/<int:project_id>/add_person', methods=['POST'])
def add_person_to_project(project_id):
    person_id = request.form.get('person_id')
    if person_id and not ProjectPerson.query.filter_by(project_id=project_id, person_id=person_id).first():
        rel = ProjectPerson(project_id=project_id, person_id=person_id,
            what_the_person_is_doing=request.form.get('what_the_person_is_doing'),
            involvement_level=request.form.get('involvement_level'), notes=request.form.get('notes'))
        db.session.add(rel)
        p = Project.query.get(project_id)
        person = Person.query.get(person_id)
        if p: p.updated_at = datetime.utcnow()
        if person: person.updated_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('project_detail', id=project_id))

@app.route('/relation/<int:rel_id>/edit', methods=['POST'])
def edit_relation(rel_id):
    relation = ProjectPerson.query.get_or_404(rel_id)
    relation.involvement_level = request.form.get('involvement_level')
    relation.what_the_person_is_doing = request.form.get('what_the_person_is_doing')
    relation.notes = request.form.get('notes')
    if relation.project: relation.project.updated_at = datetime.utcnow()
    if relation.person: relation.person.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/relation/<int:rel_id>/delete', methods=['POST'])
def delete_relation(rel_id):
    relation = ProjectPerson.query.get_or_404(rel_id)
    if relation.project: relation.project.updated_at = datetime.utcnow()
    if relation.person: relation.person.updated_at = datetime.utcnow()
    db.session.delete(relation)
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/project/<int:project_id>/add_task', methods=['POST'])
def add_task(project_id):
    title = request.form.get('title')
    if title:
        task = Task(
            project_id=project_id,
            title=title,
            assigned_person_id=request.form.get('assigned_person_id') or None,
            status=request.form.get('status', 'Pending'),
            due_date=request.form.get('due_date'),
            notes=request.form.get('notes'),
            description=request.form.get('description', ''),
            necessary_info=request.form.get('necessary_info', '')
        )
        db.session.add(task)
        db.session.commit()
    return redirect(url_for('project_detail', id=project_id))

@app.route('/task/<int:task_id>')
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('task_detail.html', task=task)

@app.route('/task/<int:task_id>/update', methods=['POST'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.title = request.form.get('title', task.title)
    task.description = request.form.get('description', task.description)
    task.necessary_info = request.form.get('necessary_info', task.necessary_info)
    task.notes = request.form.get('notes', task.notes)
    task.due_date = request.form.get('due_date', task.due_date)
    task.status = request.form.get('status', task.status)
    db.session.commit()
    return redirect(request.referrer or url_for('task_detail', task_id=task_id))

@app.route('/task/<int:task_id>/update_status', methods=['POST'])
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = request.form.get('status', 'Pending')
    db.session.commit()
    return redirect(request.referrer or url_for('projects'))

@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(request.referrer or url_for('projects'))

@app.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'POST':
        title = request.form.get('title')
        if title:
            event = Event(title=title, description=request.form.get('description'),
                event_date=request.form.get('event_date'), event_time=request.form.get('event_time'),
                event_link=request.form.get('event_link'))
            db.session.add(event)
            db.session.commit()
        return redirect(url_for('events'))

    query = Event.query
    search = request.args.get('search')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if search:
        query = query.filter(db.or_(Event.title.ilike(f'%{search}%'), Event.description.ilike(f'%{search}%')))
    if date_from:
        query = query.filter(Event.event_date >= date_from)
    if date_to:
        query = query.filter(Event.event_date <= date_to)

    sort_by = request.args.get('sort_by', 'event_date')
    sort_order = request.args.get('sort_order', 'desc')
    valid_sort_columns = {'title': Event.title, 'event_date': Event.event_date, 'event_time': Event.event_time}
    if sort_by and sort_by != '_':
        col = valid_sort_columns.get(sort_by, Event.event_date)
        query = query.order_by(col.asc() if sort_order == 'asc' else col.desc())

    all_events = query.all()
    return render_template('events.html', events=all_events, sort_by=sort_by, sort_order=sort_order,
        applied_filters={'search': search, 'date_from': date_from, 'date_to': date_to})

@app.route('/project/<int:project_id>/add_link', methods=['POST'])
def add_project_link(project_id):
    url = request.form.get('url')
    if url:
        db.session.add(ProjectLink(project_id=project_id, title=request.form.get('title'), url=url, link_type=request.form.get('link_type', 'general')))
        db.session.commit()
    return redirect(url_for('project_detail', id=project_id))

@app.route('/link/<int:link_id>/delete', methods=['POST'])
def delete_project_link(link_id):
    link = ProjectLink.query.get_or_404(link_id)
    pid = link.project_id
    db.session.delete(link)
    db.session.commit()
    return redirect(url_for('project_detail', id=pid))

@app.route('/events/reports')
def event_reports():
    all_events = Event.query.all()
    total_events = len(all_events)
    events_with_links = sum(1 for e in all_events if e.event_link)
    monthly_counts = {}
    for e in all_events:
        if e.event_date:
            try:
                mk = e.event_date[:7]
                monthly_counts[mk] = monthly_counts.get(mk, 0) + 1
            except: pass
    sorted_events = sorted(all_events, key=lambda e: e.event_date or '', reverse=True)
    return render_template('event_reports.html', total_events=total_events, events_with_links=events_with_links,
        monthly_counts=monthly_counts, events=sorted_events)

@app.route('/event/<int:id>', methods=['GET', 'POST'])
def event_detail(id):
    event = Event.query.get_or_404(id)
    all_people = Person.query.all()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save_report':
            event.report_content = request.form.get('report_content', '')
        # Always save description if provided
        if request.form.get('description'):
            event.description = request.form.get('description')
        db.session.commit()
        return redirect(url_for('event_detail', id=id))
    return render_template('event_detail.html', event=event, all_people=all_people)

@app.route('/event/<int:event_id>/add_attendee', methods=['POST'])
def add_event_attendee(event_id):
    person_id = request.form.get('person_id')
    if person_id and not EventAttendee.query.filter_by(event_id=event_id, person_id=person_id).first():
        db.session.add(EventAttendee(event_id=event_id, person_id=int(person_id)))
        db.session.commit()
    return redirect(url_for('event_detail', id=event_id))

@app.route('/event/<int:event_id>/remove_attendee/<int:attendee_id>', methods=['POST'])
def remove_event_attendee(event_id, attendee_id):
    attendee = EventAttendee.query.get_or_404(attendee_id)
    db.session.delete(attendee)
    db.session.commit()
    return redirect(url_for('event_detail', id=event_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import sqlite3
        conn = sqlite3.connect('instance/medha.db')
        c = conn.cursor()
        for col in ['description', 'necessary_info', 'owner_person_id']:
            try: c.execute(f"ALTER TABLE task ADD COLUMN {col} TEXT")
            except: pass
        try: c.execute("ALTER TABLE event ADD COLUMN report_content TEXT")
        except: pass
        conn.commit()
        conn.close()
    app.run(debug=True, port=5001)
