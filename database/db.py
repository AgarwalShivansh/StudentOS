import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / 'studentos.db'


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS student_profile (
            id INTEGER PRIMARY KEY CHECK(id=1), name TEXT, degree TEXT, year INTEGER,
            cgpa REAL, target_role TEXT, skills TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT,
            target REAL, current REAL DEFAULT 0, deadline TEXT, status TEXT DEFAULT 'Active',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, content TEXT, score REAL,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, minutes INTEGER,
            session_date TEXT, source TEXT
        );
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, plan_date TEXT, content TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, score REAL, total INTEGER,
            created_at TEXT
        );
        ''')


def save_profile(p):
    with conn() as c:
        c.execute('''INSERT INTO student_profile(id,name,degree,year,cgpa,target_role,skills,updated_at)
                     VALUES(1,?,?,?,?,?,?,?)
                     ON CONFLICT(id) DO UPDATE SET name=excluded.name,degree=excluded.degree,
                     year=excluded.year,cgpa=excluded.cgpa,target_role=excluded.target_role,
                     skills=excluded.skills,updated_at=excluded.updated_at''',
                  (p.get('name',''),p.get('degree',''),p.get('year',1),p.get('cgpa',0),p.get('role',''),p.get('skills',''),datetime.now().isoformat()))


def get_profile():
    with conn() as c:
        r=c.execute('SELECT * FROM student_profile WHERE id=1').fetchone()
        return dict(r) if r else {}


def add_goal(title, category, target, current, deadline):
    with conn() as c:
        c.execute('INSERT INTO goals(title,category,target,current,deadline,created_at) VALUES(?,?,?,?,?,?)',
                  (title,category,target,current,deadline,datetime.now().isoformat()))


def list_goals():
    with conn() as c:
        return [dict(r) for r in c.execute('SELECT * FROM goals ORDER BY deadline IS NULL, deadline').fetchall()]


def update_goal(goal_id, current, status=None):
    with conn() as c:
        if status:
            c.execute('UPDATE goals SET current=?, status=? WHERE id=?',(current,status,goal_id))
        else:
            c.execute('UPDATE goals SET current=? WHERE id=?',(current,goal_id))


def save_resume(filename, content, score=None):
    with conn() as c:
        c.execute('INSERT INTO resumes(filename,content,score,created_at) VALUES(?,?,?,?)',(filename,content,score,datetime.now().isoformat()))


def save_jd(title, content):
    with conn() as c:
        c.execute('INSERT INTO job_descriptions(title,content,created_at) VALUES(?,?,?)',(title,content,datetime.now().isoformat()))


def save_plan(plan_date, content):
    with conn() as c:
        c.execute('INSERT INTO plans(plan_date,content,created_at) VALUES(?,?,?)',(plan_date,content,datetime.now().isoformat()))


def add_study_session(subject, minutes, source='Focus Mode'):
    with conn() as c:
        c.execute('INSERT INTO study_sessions(subject,minutes,session_date,source) VALUES(?,?,?,?)',
                  (subject,minutes,datetime.now().date().isoformat(),source))


def recent_study_minutes():
    with conn() as c:
        return sum(r['minutes'] for r in c.execute("SELECT minutes FROM study_sessions WHERE session_date >= date('now','-7 day')").fetchall())

init_db()
