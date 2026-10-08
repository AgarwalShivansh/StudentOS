import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from datetime import date

from database.db import save_profile, get_profile, add_goal, list_goals, update_goal, save_resume, save_jd, save_plan
from goals.goals import progress
from lifelog.analytics import analyze, REQUIRED
from rag.engine import StudyRAG
from intellihire.analyzer import analyze_resume, match
from intellihire.career import career_readiness
from tools.document_parser import extract_text
from tools.youtube import get_transcript
from planner.planner import build_plan
from core.groq_client import get_client, MODEL, ask_groq
from coach.coach import coach

load_dotenv()
st.set_page_config(page_title='StudentOS AI', page_icon='🎓',
                   layout='wide', initial_sidebar_state='collapsed')

# -------------------- STATE --------------------
if 'profile' not in st.session_state:
    st.session_state.profile = get_profile()
if 'lifelog' not in st.session_state:
    st.session_state.lifelog = None
if 'rag' not in st.session_state:
    st.session_state.rag = StudyRAG()
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ''
if 'resume_analysis' not in st.session_state:
    st.session_state.resume_analysis = None
if 'last_plan' not in st.session_state:
    st.session_state.last_plan = ''

# -------------------- UI THEME --------------------
st.markdown('''
<style>
    :root { --bg:#0b0d12; --panel:#121620; --border:rgba(255,255,255,.08); --muted:#8f98aa; --purple:#a78bfa; }
    .stApp { background:var(--bg); }
    .block-container { max-width:1450px; padding-top:1.15rem; padding-bottom:4rem; }
    #MainMenu, footer, header { visibility:hidden; }
    div[role="radiogroup"] { gap:.28rem; padding:.42rem; border:1px solid var(--border); border-radius:16px; background:rgba(18,22,32,.82); box-shadow:0 10px 35px rgba(0,0,0,.18); margin-bottom:1.8rem; overflow-x:auto; flex-wrap:nowrap; }
    div[role="radiogroup"] > label { min-width:max-content; border:1px solid transparent; border-radius:11px; padding:.48rem .78rem !important; transition:all .18s ease; color:#d8dce7; }
    div[role="radiogroup"] > label:hover { background:rgba(167,139,250,.10); border-color:rgba(167,139,250,.18); }
    div[role="radiogroup"] > label:has(input:checked) { background:linear-gradient(135deg,rgba(124,92,255,.24),rgba(103,232,249,.08)); border-color:rgba(167,139,250,.30); }
    h1 button, h2 button, h3 button { display:none !important; }
    .hero { padding:.2rem 0 1.15rem; }
    .eyebrow { color:var(--purple); font-size:.72rem; font-weight:800; text-transform:uppercase; letter-spacing:1.45px; margin-bottom:.28rem; }
    .hero-title { font-size:2.65rem; font-weight:820; letter-spacing:-1.7px; line-height:1.05; margin:0; }
    .hero-subtitle { color:var(--muted); font-size:.98rem; margin-top:.48rem; }
    .card { border:1px solid var(--border); background:linear-gradient(145deg,rgba(23,27,39,.98),rgba(14,17,24,.98)); border-radius:18px; padding:1.15rem 1.2rem; box-shadow:0 12px 32px rgba(0,0,0,.14); }
    .card-small { min-height:122px; }
    .card-title { color:#aeb6c7; font-size:.79rem; font-weight:750; margin-bottom:.55rem; }
    .card-value { font-size:2rem; font-weight:800; line-height:1.05; }
    .card-note { color:#7f889b; font-size:.77rem; margin-top:.48rem; line-height:1.35; }
    .ai-card { border:1px solid rgba(167,139,250,.24); background:radial-gradient(circle at 100% 0%,rgba(124,92,255,.19),transparent 42%),linear-gradient(145deg,rgba(35,29,56,.9),rgba(18,21,29,.98)); border-radius:18px; padding:1.3rem; min-height:210px; }
    .ai-label { color:#c4b5fd; font-weight:800; font-size:.76rem; letter-spacing:.7px; }
    .ai-heading { font-size:1.25rem; font-weight:780; margin:.52rem 0 .45rem; line-height:1.3; }
    .muted { color:var(--muted); line-height:1.5; }
    .section-kicker { color:var(--purple); font-size:.70rem; font-weight:800; text-transform:uppercase; letter-spacing:1.25px; margin-top:.7rem; }
    .section-title { font-size:1.35rem; font-weight:780; margin-bottom:.8rem; }
    .goal-row { margin:.85rem 0 .15rem; }
    .goal-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:.38rem; }
    .goal-name { font-weight:700; }
    .goal-percent { color:#aeb6c7; font-size:.82rem; font-weight:650; }
    .stButton > button, .stDownloadButton > button { border-radius:11px; font-weight:700; min-height:2.45rem; }
    .stButton > button[kind="primary"] { box-shadow:0 8px 24px rgba(124,92,255,.18); }
    div[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(23,27,39,.98),rgba(14,17,24,.98)); border:1px solid var(--border); border-radius:16px; padding:.85rem 1rem; }
    div[data-testid="stMetricLabel"] { color:#9ba4b7; }
    div[data-testid="stMetricValue"] { font-weight:800; }
    div[data-testid="stExpander"] { border-radius:14px; border-color:var(--border); background:rgba(18,22,32,.35); }
    div[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }
    .profile-hint { border-left:3px solid var(--purple); padding:.65rem .85rem; background:rgba(167,139,250,.06); border-radius:0 10px 10px 0; color:#aeb6c7; }
    @media (max-width:900px) { .hero-title { font-size:2.05rem; } div[role="radiogroup"] { overflow-x:auto; } }
</style>
''', unsafe_allow_html=True)

# -------------------- NAVIGATION --------------------
pages = [
    '🏠 Home', '📊 LifeLog', '📚 Study Hub', '💼 IntelliHire',
    '🎯 Goals', '🗓️ Planner', '🤖 AI Coach', '📈 Career', '📄 Reports'
]
selected = st.radio('Navigation', pages, horizontal=True,
                    label_visibility='collapsed')
page_map = {
    '🏠 Home': 'Home',
    '📊 LifeLog': 'LifeLog AI',
    '📚 Study Hub': 'Study',
    '💼 IntelliHire': 'IntelliHire',
    '🎯 Goals': 'Goals',
    '🗓️ Planner': 'AI Study Planner',
    '🤖 AI Coach': 'AI Coach',
    '📈 Career': 'Career Readiness',
    '📄 Reports': 'Reports',
}
page = page_map[selected]

# -------------------- HELPERS --------------------


def app_header(kicker, title, subtitle):
    st.markdown(f'''<div class="hero">
        <div class="eyebrow">{kicker}</div>
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>''', unsafe_allow_html=True)


def card(title, value, note=''):
    st.markdown(f'''<div class="card card-small">
        <div class="card-title">{title}</div>
        <div class="card-value">{value}</div>
        <div class="card-note">{note}</div>
    </div>''', unsafe_allow_html=True)


# ==================== HOME ====================
if page == 'Home':
    p = st.session_state.profile or {}
    name = p.get('name', 'Student') or 'Student'
    goals = list_goals()
    lifelog = st.session_state.lifelog

    st.markdown(f'''<div class="hero">
        <div class="eyebrow">PERSONAL STUDENT OPERATING SYSTEM</div>
        <div class="hero-title">Good to see you, {name} 👋</div>
        <div class="hero-subtitle">One workspace for academics, goals, study tools, AI coaching and career preparation.</div>
    </div>''', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap='medium')
    health = lifelog.get('health', 0) if lifelog else None
    health_value = f"{health:.0f}<span style='font-size:1rem;color:#7f889b'> / 100</span>" if health is not None else '—'
    health_note = 'Based on your latest LifeLog analysis' if lifelog else 'Analyze your activity to unlock this'
    c1.markdown(
        f'''<div class="card card-small"><div class="card-title">🧠 ACADEMIC HEALTH</div><div class="card-value">{health_value}</div><div class="card-note">{health_note}</div></div>''', unsafe_allow_html=True)
    c2.markdown(
        f'''<div class="card card-small"><div class="card-title">📚 STUDY LIBRARY</div><div class="card-value">{len(st.session_state.rag.chunks)}</div><div class="card-note">Indexed study chunks ready for RAG</div></div>''', unsafe_allow_html=True)
    active_goals = sum(1 for g in goals if str(
        g.get('status', 'Active')).lower() != 'completed')
    c3.markdown(
        f'''<div class="card card-small"><div class="card-title">🎯 ACTIVE GOALS</div><div class="card-value">{active_goals}</div><div class="card-note">{len(goals)} total goals saved</div></div>''', unsafe_allow_html=True)

    if st.session_state.resume_analysis:
        cr = career_readiness(
            p, st.session_state.resume_analysis, goals, lifelog)
        career_score = cr.get('overall', 0)
        career_note = 'Resume + profile + goals'
    else:
        career_score = None
        career_note = 'Analyze your resume to calculate'
    career_value = f"{career_score:.0f}%" if career_score is not None else '—'
    c4.markdown(
        f'''<div class="card card-small"><div class="card-title">💼 CAREER READINESS</div><div class="card-value">{career_value}</div><div class="card-note">{career_note}</div></div>''', unsafe_allow_html=True)

    st.write('')
    left, right = st.columns([1.05, 1], gap='large')

    with left:
        st.markdown('<div class="section-kicker">🤖 INTELLIGENCE</div><div class="section-title">What deserves your attention?</div>', unsafe_allow_html=True)
        if lifelog and lifelog.get('recommendations'):
            recommendation = lifelog['recommendations'][0]
            extra = lifelog['recommendations'][1:3]
            st.markdown(
                f'''<div class="ai-card"><div class="ai-label">STUDENTOS AI INSIGHT</div><div class="ai-heading">{recommendation}</div><div class="muted">Generated from your current LifeLog data. Recommendations change as your activity changes.</div></div>''', unsafe_allow_html=True)
            if extra:
                with st.expander('View more insights'):
                    for item in extra:
                        st.write('• ' + item)
        elif not p:
            st.markdown('''<div class="ai-card"><div class="ai-label">👤 FIRST STEP</div><div class="ai-heading">Set up your student profile.</div><div class="muted">Your profile gives StudentOS the context it needs for goals, planning, coaching and career recommendations.</div></div>''', unsafe_allow_html=True)
        else:
            st.markdown('''<div class="ai-card"><div class="ai-label">✨ READY FOR YOUR DATA</div><div class="ai-heading">Start with one of your student workflows.</div><div class="muted">Analyze activity, build your study library, create a goal or analyze your resume to unlock personalized intelligence.</div></div>''', unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div class="section-kicker">📅 TODAY</div><div class="section-title">Your study plan</div>', unsafe_allow_html=True)
        if st.session_state.last_plan:
            preview = st.session_state.last_plan[:900]
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(preview)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('''<div class="card"><div class="card-title">🗓️ NO PLAN YET</div><div class="card-value" style="font-size:1.22rem">Build a personalized study plan</div><div class="card-note">The planner can use your profile, goals and LifeLog weaknesses to prioritize your time.</div></div>''', unsafe_allow_html=True)
            st.write('')
            if st.button('Open AI Study Planner →', type='primary', key='home_planner'):
                st.info('Select **🗓️ Planner** from the navigation above.')

    st.markdown('<div class="section-kicker">🎯 PROGRESS</div><div class="section-title">Your active goals</div>',
                unsafe_allow_html=True)
    if goals:
        active = [g for g in goals if str(
            g.get('status', 'Active')).lower() != 'completed'][:5]
        if active:
            for g in active:
                pct = progress(g)
                st.markdown(
                    f'''<div class="goal-row"><div class="goal-head"><span class="goal-name">{g.get('title', 'Goal')}</span><span class="goal-percent">{pct:.0f}%</span></div></div>''', unsafe_allow_html=True)
                st.progress(pct / 100)
        else:
            st.success('All saved goals are completed. 🎉')
    else:
        st.markdown('''<div class="card"><div class="card-title">🎯 GET STARTED</div><div class="card-value" style="font-size:1.22rem">Create your first goal</div><div class="card-note">Track DSA, exams, projects, placements or any measurable target.</div></div>''', unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">⚡ QUICK ACTIONS</div><div class="section-title">Choose your next workflow</div>', unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4, gap='medium')
    q1.markdown('<div class="card"><div class="card-title">📊 LIFELOG</div><div class="card-value" style="font-size:1.1rem">Analyze activity</div><div class="card-note">Understand performance and weak topics.</div></div>', unsafe_allow_html=True)
    q2.markdown('<div class="card"><div class="card-title">📚 STUDY HUB</div><div class="card-value" style="font-size:1.1rem">Learn from material</div><div class="card-note">RAG, notes, YouTube summaries and quizzes.</div></div>', unsafe_allow_html=True)
    q3.markdown('<div class="card"><div class="card-title">💼 INTELLIHIRE</div><div class="card-value" style="font-size:1.1rem">Check career fit</div><div class="card-note">Analyze resumes and match job descriptions.</div></div>', unsafe_allow_html=True)
    q4.markdown('<div class="card"><div class="card-title">🤖 AI COACH</div><div class="card-value" style="font-size:1.1rem">Ask StudentOS</div><div class="card-note">Get personalized academic and career guidance.</div></div>', unsafe_allow_html=True)

    with st.expander('👤 Student Profile & Settings'):
        st.markdown('<div class="profile-hint">Your saved profile is used by the Study Planner, AI Coach and Career Readiness features.</div>', unsafe_allow_html=True)
        st.write('')
        with st.form('profile_form'):
            name = st.text_input('Name', p.get('name', ''))
            degree = st.text_input('Degree', p.get('degree', ''))
            year = st.selectbox('Year', [1, 2, 3, 4], index=max(
                0, min(3, int(p.get('year', 3) or 3) - 1)))
            cgpa = st.number_input('Current CGPA', 0.0, 10.0, float(
                p.get('cgpa', 0.0) or 0.0), 0.01)
            role = st.text_input('Target role', p.get(
                'role', p.get('target_role', '')))
            skills = st.text_input(
                'Skills (comma separated)', p.get('skills', ''))
            if st.form_submit_button('Save Profile', type='primary'):
                profile = {'name': name, 'degree': degree, 'year': year,
                           'cgpa': cgpa, 'role': role, 'skills': skills}
                save_profile(profile)
                st.session_state.profile = profile
                st.success('Profile saved to the student database.')

# ==================== LIFELOG ====================
elif page == 'LifeLog AI':
    app_header('ACADEMIC INTELLIGENCE', 'LifeLog AI',
               'Understand your study behavior, consistency and performance trends.')
    st.caption(
        'Upload your own activity CSV. Nothing is analyzed until you choose Analyze.')
    file = st.file_uploader('Upload activity CSV', type=['csv'])
    if file:
        df = pd.read_csv(file)
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            st.error('Missing columns: ' + ', '.join(missing))
        else:
            st.dataframe(df.head(10), use_container_width=True)
            if st.button('Analyze My Activity', type='primary'):
                result = analyze(df)
                if 'error' in result:
                    st.error(result['error'])
                else:
                    st.session_state.lifelog = result
                    st.success('Analysis completed from your uploaded data.')
    if st.session_state.lifelog:
        r = st.session_state.lifelog
        a, b, c, d = st.columns(4)
        a.metric('Academic Health', f"{r['health']:.0f}/100")
        b.metric('Consistency', f"{r['consistency']:.0f}/100")
        c.metric('Recent Accuracy', f"{r['recent']['accuracy']:.1f}%")
        anomaly_count = int((r['data']['anomaly'] == -1).sum()
                            ) if 'anomaly' in r['data'] else 0
        d.metric('Anomalies', anomaly_count)
        st.subheader('Performance trend')
        st.line_chart(r['data'].set_index('date')[['study_hours', 'accuracy']])
        st.subheader('Topic performance')
        st.dataframe(r['topic'], use_container_width=True)
        st.subheader('Detected behavioral anomalies')
        st.dataframe(r['data'][r['data']['anomaly'] == -1][['date', 'topic', 'study_hours',
                     'accuracy', 'deadline_missed', 'anomaly_score']], use_container_width=True)
        st.subheader('Recommended actions')
        for x in r['recommendations']:
            st.write('• ' + x)

# ==================== STUDY ====================
elif page == 'Study':
    app_header('STUDY HUB', 'Learn from your material',
               'RAG, notes, YouTube summaries and AI-generated quizzes in one workspace.')
    tabs = st.tabs(['📄 Study RAG', '📝 Text → Notes',
                   '▶️ YouTube', '❓ AI Quiz'])
    with tabs[0]:
        st.write(
            'Upload course PDFs and ask grounded questions with page-aware retrieval.')
        files = st.file_uploader('Upload course PDFs', type=[
                                 'pdf'], accept_multiple_files=True, key='rag_upload')
        if files and st.button('Build Study Library', type='primary'):
            try:
                st.success(
                    f"Indexed {st.session_state.rag.ingest(files)} page-aware chunks.")
            except Exception as e:
                st.error(str(e))
        if st.session_state.rag.chunks:
            mode = st.selectbox(
                'Answer mode', ['Explain', 'Exam Answer', 'Quick Revision', 'Quiz Me'])
            q = st.text_area('Ask your study question', key='rag_q')
            if st.button('Ask AI', key='rag_ask') and q.strip():
                hits = st.session_state.rag.search(q, 5)
                context = '\n\n'.join(
                    f"SOURCE: {h['source']} | PAGE: {h['page']}\n{h['text']}" for h in hits)
                prompt = f'''Answer using ONLY the supplied study material. If insufficient, say so. Mode: {mode}. Question: {q}\n\nMATERIAL:\n{context}'''
                try:
                    answer = ask_groq([{'role': 'system', 'content': 'You are a grounded study assistant. Never use knowledge outside supplied material.'}, {
                                      'role': 'user', 'content': prompt}], max_tokens=2200)
                    st.markdown(answer)
                    st.caption('Retrieved sources')
                    for h in hits:
                        st.write(
                            f"• {h['source']} — page {h['page']} — score {h['score']:.3f}")
                except Exception as e:
                    st.error(str(e))
    with tabs[1]:
        st.write('Convert pasted lecture material into structured revision notes.')
        raw = st.text_area('Paste text', height=260)
        style = st.selectbox('Note style', [
                             'Short Revision Notes', 'Detailed Notes', 'Exam Notes', '15-Mark Answer', 'Flashcards'])
        if st.button('Convert to Notes', type='primary') and raw.strip():
            try:
                if get_client():
                    out = ask_groq([{'role': 'system', 'content': 'Turn the supplied text into accurate study notes. Do not add unsupported facts.'}, {
                                   'role': 'user', 'content': f'Style: {style}\nTEXT:\n{raw}'}], max_tokens=2400)
                else:
                    out = '## Notes\n\n' + raw
                st.markdown(out)
                st.download_button('Download Notes', out,
                                   'studentos_notes.md', 'text/markdown')
            except Exception as e:
                st.error(str(e))
    with tabs[2]:
        st.write(
            'Summarize a YouTube video when a usable transcript/captions are available.')
        url = st.text_input('YouTube URL')
        if st.button('Summarize Video', type='primary') and url.strip():
            try:
                transcript = get_transcript(url)
                st.session_state.youtube_transcript = transcript
                if get_client():
                    out = ask_groq([{'role': 'system', 'content': 'Summarize the supplied transcript accurately. Create key concepts and exam-oriented notes. Do not invent facts.'}, {
                                   'role': 'user', 'content': transcript}], max_tokens=3000)
                else:
                    out = transcript[:12000]
                st.markdown(out)
                st.download_button('Download Summary', out,
                                   'youtube_summary.md', 'text/markdown')
            except Exception as e:
                st.error(str(e))
    with tabs[3]:
        st.write('Generate questions from the current Study RAG library.')
        n = st.slider('Number of questions', 3, 15, 5)
        if st.button('Generate Quiz', type='primary'):
            if not st.session_state.rag.chunks:
                st.warning('Build a Study Library first.')
            elif not get_client():
                st.error('Configure GROQ_API_KEY for AI quiz generation.')
            else:
                context = '\n\n'.join(c['text']
                                      for c in st.session_state.rag.chunks[:15])
                out = ask_groq([{'role': 'system', 'content': 'Create an accurate study quiz from only the supplied material. Include answer key and concise explanations.'}, {
                               'role': 'user', 'content': f'Create {n} MCQs.\nMATERIAL:\n{context}'}], max_tokens=3000)
                st.markdown(out)

# ==================== INTELLIHIRE ====================
elif page == 'IntelliHire':
    app_header('CAREER INTELLIGENCE', 'IntelliHire AI',
               'Analyze your resume, compare it with jobs and identify exactly what to improve.')
    tabs = st.tabs(['📄 Resume Analyzer', '🔎 Resume ↔ Job Matcher'])
    with tabs[0]:
        resume_file = st.file_uploader('Upload Resume (PDF, DOCX, or TXT)', type=[
                                       'pdf', 'docx', 'txt'], key='resume_file')
        resume_text = st.text_area(
            'Or paste resume text', value=st.session_state.resume_text, height=220, key='resume_text_box')
        if resume_file:
            try:
                resume_text = extract_text(resume_file)
                st.session_state.resume_text = resume_text
                st.success(f'Extracted text from {resume_file.name}.')
            except Exception as e:
                st.error(str(e))
        if st.button('Analyze Resume', type='primary') and resume_text.strip():
            a = analyze_resume(resume_text)
            st.session_state.resume_analysis = a
            save_resume(
                resume_file.name if resume_file else 'pasted_resume.txt', resume_text, a['score'])
        if st.session_state.resume_analysis:
            a = st.session_state.resume_analysis
            x, y, z = st.columns(3)
            x.metric('Resume Score', f"{a['score']:.0f}/100")
            y.metric('Detected Skills', len(a['skills']))
            z.metric('Sections', sum(a['sections'].values()))
            st.write('**Detected skills:**',
                     ', '.join(a['skills']) or 'None detected')
            st.subheader('Improvement suggestions')
            for s in a['suggestions']:
                st.write('• ' + s)
    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            rf = st.file_uploader(
                'Resume (PDF/DOCX/TXT)', type=['pdf', 'docx', 'txt'], key='match_resume')
            rtxt = st.text_area('Resume text', height=220, key='match_rtxt')
            if rf:
                try:
                    rtxt = extract_text(rf)
                except Exception as e:
                    st.error(str(e))
        with col2:
            jf = st.file_uploader(
                'Job Description (PDF/DOCX/TXT)', type=['pdf', 'docx', 'txt'], key='jd_file')
            jtxt = st.text_area('Job description text',
                                height=220, key='match_jtxt')
            if jf:
                try:
                    jtxt = extract_text(jf)
                except Exception as e:
                    st.error(str(e))
        if st.button('Analyze Match', type='primary') and rtxt.strip() and jtxt.strip():
            r = match(rtxt, jtxt)
            save_jd(jf.name if jf else 'pasted_jd.txt', jtxt)
            a, b, c = st.columns(3)
            a.metric('Overall Match', f"{r['final']:.1f}%")
            b.metric('Semantic Match', f"{r['similarity']:.1f}%")
            c.metric('Skill Coverage', f"{r['skill_score']:.1f}%")
            st.write('**Covered skills:**',
                     ', '.join(r['covered']) or 'None detected')
            st.write('**Missing skills:**',
                     ', '.join(r['missing']) or 'None detected')

# ==================== GOALS ====================
elif page == 'Goals':
    app_header('PERSONAL PROGRESS', 'Goal Tracker',
               'Turn your ambitions into measurable targets with deadlines and progress.')
    with st.form('goal_form'):
        title = st.text_input('Goal title')
        category = st.text_input('Category (DSA, ML, Exams, Placement...)')
        c1, c2 = st.columns(2)
        target = c1.number_input('Target', min_value=1.0, value=100.0)
        current = c2.number_input('Current progress', min_value=0.0, value=0.0)
        deadline = st.date_input('Deadline', value=date.today())
        if st.form_submit_button('Add Goal', type='primary'):
            if title.strip():
                add_goal(title, category, target,
                         current, deadline.isoformat())
                st.success('Goal saved.')
    goals = list_goals()
    if goals:
        for g in goals:
            pct = progress(g)
            st.markdown(f'### 🎯 {g["title"]}')
            st.progress(pct / 100)
            c1, c2, c3 = st.columns(3)
            c1.metric('Progress', f'{pct:.0f}%')
            c2.write(f"{g.get('current', 0)} / {g.get('target', 0)}")
            c3.write(f"Deadline: {g.get('deadline', '—')}")
            new = st.number_input('Update current value', min_value=0.0, value=float(
                g.get('current', 0)), key=f'goal_{g["id"]}')
            if st.button('Update', key=f'upd_{g["id"]}'):
                update_goal(g['id'], new, 'Completed' if new >=
                            float(g['target']) else 'Active')
                st.rerun()
    else:
        st.info('No goals yet. Add your first goal above.')

# ==================== PLANNER ====================
elif page == 'AI Study Planner':
    app_header('PERSONALIZED PLANNING', 'AI Study Planner',
               'Build a realistic plan using your profile, goals and LifeLog weaknesses.')
    hours = st.slider('Available study hours per day', 1, 12, 3)
    days = st.slider('Plan duration (days)', 1, 14, 7)
    if st.button('Generate My Study Plan', type='primary'):
        goals = list_goals()
        plan = build_plan(st.session_state.profile, goals,
                          st.session_state.lifelog, hours, days)
        st.session_state.last_plan = plan
        save_plan(date.today().isoformat(), plan)
    if st.session_state.last_plan:
        st.markdown(st.session_state.last_plan)
        st.download_button('Download Study Plan', st.session_state.last_plan,
                           'studentos_study_plan.txt', 'text/plain')

# ==================== COACH ====================
elif page == 'AI Coach':
    app_header('PERSONAL AI', 'AI Student Coach',
               'Ask for study, career and productivity guidance using your saved student context.')
    q = st.text_area('Ask your coach', 'What should I focus on this week?')
    if st.button('Ask Coach', type='primary'):
        if not st.session_state.profile:
            st.warning('Save your student profile on Home first.')
        elif not get_client():
            st.error(
                f'Groq is not configured. Add GROQ_API_KEY to .env. Current model: {MODEL}')
        else:
            try:
                st.markdown(coach(st.session_state.profile,
                            st.session_state.lifelog, q))
            except Exception as e:
                st.error(f'Groq request failed: {e}')

# ==================== CAREER ====================
elif page == 'Career Readiness':
    app_header('CAREER INTELLIGENCE', 'Career Readiness',
               'See how prepared you are for internships and placements — and what to improve next.')
    if not st.session_state.resume_analysis:
        st.info('Analyze a resume in IntelliHire first to populate the dashboard.')
    else:
        cr = career_readiness(
            st.session_state.profile, st.session_state.resume_analysis, list_goals(), st.session_state.lifelog)
        a, b, c, d = st.columns(4)
        a.metric('Career Readiness', f"{cr['overall']:.0f}/100")
        b.metric('Resume', f"{cr['resume']:.0f}")
        c.metric('Technical', f"{cr['technical']:.0f}")
        d.metric('DSA', f"{cr['dsa']:.0f}")
        st.subheader('Readiness breakdown')
        st.dataframe(pd.DataFrame({'Area': ['Resume', 'Projects', 'Academics', 'Technical Skills', 'DSA'], 'Score': [
                     cr['resume'], cr['projects'], cr['academic'], cr['technical'], cr['dsa']]}), hide_index=True, use_container_width=True)
        st.subheader('Priority improvements')
        for x in cr['gaps']:
            st.write('• ' + x)

# ==================== REPORTS ====================
elif page == 'Reports':
    app_header('INSIGHTS & EXPORTS', 'Student Reports',
               'Turn your activity analysis into a simple report you can save and review.')
    if not st.session_state.lifelog:
        st.info('Run LifeLog analysis first to create an academic report.')
    else:
        r = st.session_state.lifelog
        anomaly_count = int((r['data']['anomaly'] == -1).sum()
                            ) if 'anomaly' in r['data'] else 0
        report = f'''STUDENTOS AI — LIFELOG REPORT\n\nAcademic Health: {r['health']:.0f}/100\nConsistency: {r['consistency']:.0f}/100\nRecent Accuracy: {r['recent']['accuracy']:.1f}%\nAnomalies Detected: {anomaly_count}\n\nRecommended Actions:\n''' + '\n'.join(
            '- ' + x for x in r['recommendations'])
        st.text(report)
        st.download_button('Download Report', report,
                           'studentos_lifelog_report.txt', 'text/plain')
