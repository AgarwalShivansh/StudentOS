def progress(goal):
    t=float(goal.get('target') or 0); c=float(goal.get('current') or 0)
    return 0 if t<=0 else max(0,min(100,c/t*100))
