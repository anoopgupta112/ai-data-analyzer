import pandas as pd
from typing import List, Dict, Any
from .db import SessionLocal, Form, Submission, init_db
from sqlalchemy.orm import Session, selectinload
import json
import os

init_db()

def create_form(form_id: str, fields: List[Dict[str, Any]]):
    db: Session = SessionLocal()
    form = Form(form_id=form_id, fields=json.dumps(fields))
    db.add(form)
    db.commit()
    db.close()

def get_form(form_id: str):
    db: Session = SessionLocal()
    form = db.query(Form).options(selectinload(Form.submissions)).filter(Form.form_id == form_id).first()
    if not form:
        db.close()
        return None
    result = {
        "fields": json.loads(form.fields),
        "submissions": [json.loads(s.data) for s in form.submissions]
    }
    db.close()
    return result

def add_submission(form_id: str, submission: Dict[str, Any]):
    db: Session = SessionLocal()
    sub = Submission(form_id=form_id, data=json.dumps(submission))
    db.add(sub)
    db.commit()
    db.close()

def export_to_excel(form_id: str) -> str:
    db: Session = SessionLocal()
    form = db.query(Form).options(selectinload(Form.submissions)).filter(Form.form_id == form_id).first()
    submissions = [json.loads(s.data) for s in form.submissions] if form else []
    db.close()
    df = pd.DataFrame(submissions)
    file_path = f"app/static/{form_id}_data.xlsx"
    df.to_excel(file_path, index=False)
    return file_path
