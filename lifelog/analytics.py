import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

REQUIRED = ['date', 'study_hours', 'questions_attempted',
            'accuracy', 'assignment_completed', 'deadline_missed', 'topic']


def validate_activity(df):
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return False, f'Missing columns: {", ".join(missing)}'
    out = df.copy()
    out['date'] = pd.to_datetime(out['date'], errors='coerce')
    numeric = ['study_hours', 'questions_attempted',
               'accuracy', 'assignment_completed', 'deadline_missed']
    for c in numeric:
        out[c] = pd.to_numeric(out[c], errors='coerce')
    out['topic'] = out['topic'].astype(str).str.strip()
    out = out.dropna(subset=['date', 'topic'])
    out = out.drop_duplicates(
        subset=['date', 'topic'], keep='last').sort_values('date')
    out['assignment_completed'] = out['assignment_completed'].clip(0, 1)
    out['deadline_missed'] = out['deadline_missed'].clip(lower=0)
    out['study_hours'] = out['study_hours'].clip(lower=0)
    out['questions_attempted'] = out['questions_attempted'].clip(lower=0)
    out['accuracy'] = out['accuracy'].clip(0, 100)
    return True, out


def analyze(df):
    ok, data = validate_activity(df)
    if not ok:
        return {'error': data}
    if len(data) < 7:
        return {'error': 'Upload at least 7 dated activity records for a meaningful LifeLog analysis.'}

    features = ['study_hours', 'questions_attempted',
                'accuracy', 'assignment_completed', 'deadline_missed']
    X = data[features].fillna(data[features].median()
                              ).replace([np.inf, -np.inf], 0)
    contamination = min(0.20, max(0.05, 5/len(data)))
    model = IsolationForest(
        n_estimators=300, contamination=contamination, random_state=42)
    model.fit(X)
    data['anomaly_score'] = model.decision_function(X)
    data['anomaly'] = model.predict(X) == -1
    data["is_anomaly"] = data["anomaly"] == -1

    split = max(3, len(data)//3)
    recent = data.tail(split)
    previous = data.iloc[:-split] if len(data) > split else data.head(split)

    def means(frame):
        return {
            'study_hours': float(frame.study_hours.mean()),
            'accuracy': float(frame.accuracy.mean()),
            'assignment_completion': float(frame.assignment_completed.mean()*100),
            'deadline_misses': float(frame.deadline_missed.sum()),
            'questions': float(frame.questions_attempted.mean())
        }

    r, p = means(recent), means(previous)
    topic = data.groupby('topic').agg(
        sessions=('topic', 'size'), study_hours=('study_hours', 'mean'),
        accuracy=('accuracy', 'mean'), assignments=('assignment_completed', 'mean'),
        deadline_misses=('deadline_missed', 'sum')
    ).reset_index()
    topic['assignments'] *= 100
    topic['priority'] = (100-topic.accuracy)*0.65 + \
        (100-topic.assignments)*0.25 + topic.deadline_misses*5
    topic = topic.sort_values('priority', ascending=False)

    consistency = max(
        0, 100*(1 - data.study_hours.std(ddof=0)/(data.study_hours.mean()+1e-6)))
    health = np.clip(0.35*r['accuracy'] + 0.25*r['assignment_completion'] + 0.20*min(
        r['study_hours']/4, 1)*100 + 0.20*max(0, 100-r['deadline_misses']*10), 0, 100)
    recommendations = []
    if r['study_hours'] < p['study_hours']*0.85:
        recommendations.append(
            'Your recent study time is below your earlier baseline; restore a sustainable daily study block.')
    if r['accuracy'] < p['accuracy']-5:
        recommendations.append(
            'Accuracy has fallen recently; prioritize active problem solving and error review.')
    if r['deadline_misses'] > p['deadline_misses'] + 1:
        recommendations.append(
            'Deadline misses increased; schedule assignments before exam preparation blocks.')
    if not topic.empty:
        recommendations.append(
            f"Prioritize {topic.iloc[0]['topic']} based on the weakest combined performance indicators.")
    if data.anomaly.any():
        recommendations.append(
            f"Review the {int(data.anomaly.sum())} anomalous activity records and identify what changed on those dates.")

    return {'data': data, 'recent': r, 'previous': p, 'topic': topic, 'health': float(health), 'consistency': float(np.clip(consistency, 0, 100)), 'recommendations': recommendations}
