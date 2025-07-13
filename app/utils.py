# Utility functions can be added here
def get_form_submissions(form_id: str):
    # Returns a list of submission dicts for a given form_id
    from .db import SessionLocal, Submission
    import json
    session = SessionLocal()
    subs = session.query(Submission).filter_by(form_id=form_id).all()
    session.close()
    return [json.loads(s.data) for s in subs]