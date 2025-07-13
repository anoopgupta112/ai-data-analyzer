from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import uuid
from ..services import storage
from fastapi.templating import Jinja2Templates
from .payloads import FIELD_DEFINITIONS, CUSTOM_FIELD_TYPES
from .templates_config import get_all_templates, get_template_by_name
import tempfile
import shutil
import os
import json
from fastapi import UploadFile, File, Form
from app.services.github_questions import process_uploaded_pdfs
from app.services.utils import get_form_submissions
from app.services.github_agent import generate_questions_from_github
from ..services.match_agent import evaluate_resume_against_jd
from ..services.ocr_engine import extract_text_from_pdf


def get_router(templates: Jinja2Templates):
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    async def landing_page(request: Request):
        return templates.TemplateResponse("landing.html", {"request": request})

    @router.get("/match_upload", response_class=HTMLResponse)
    async def upload_resumes_page(request: Request):
        return templates.TemplateResponse("match_upload.html", {"request": request})

    # @router.get("/match_upload", response_class=HTMLResponse)
    # async def upload_resumes_page(request: Request):
    #     return templates.TemplateResponse("match_upload.html", {"request": request})

    @router.post("/api/v1/match_from_pdfs")
    async def match_from_pdfs(
            jd: str = Form(...),
            pdf_files: list[UploadFile] = File(...)
    ):
        import tempfile
        temp_dir = tempfile.mkdtemp()

        results = process_uploaded_pdfs(pdf_files, jd, temp_dir)
        return JSONResponse(content={"matches": results})

    @router.get("/match_results", response_class=HTMLResponse)
    async def match_results(request: Request):
        return templates.TemplateResponse("match_results.html", {"request": request})

    @router.get("/analyze_pdfs/{form_id}", response_class=HTMLResponse)
    async def analyze_pdfs_page(request: Request, form_id: str):
        # Get all submissions for this form to show available PDFs
        submissions = get_form_submissions(form_id)
        pdf_list = []
        for sub in submissions:
            if 'resume' in sub and sub['resume']:
                pdf_name = sub['resume'].split('/')[-1] if '/' in sub['resume'] else sub['resume']
                pdf_list.append({
                    'name': pdf_name,
                    'path': sub['resume'],
                    'submission_id': sub.get('id', '')
                })
        return templates.TemplateResponse("analyze_pdfs.html", {
            "request": request, 
            "form_id": form_id,
            "pdfs": pdf_list
        })

    @router.post("/api/v1/match_from_excel")
    async def match_from_excel(jd: str = Form(...), excel_file: UploadFile = Form(...)):
        temp_dir = tempfile.mkdtemp()
        excel_path = os.path.join(temp_dir, excel_file.filename)
        with open(excel_path, "wb") as f:
            shutil.copyfileobj(excel_file.file, f)

        results = process_excel_and_match_jd(excel_path, jd)
        return JSONResponse(content={"matches": results})

    @router.get("/api/v1/template_fields/{name}")
    async def get_template_fields(name: str):
        fields = get_template_by_name(name)
        if not fields:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"fields": fields}

    @router.get("/api/v1/templates")
    async def get_templates():
        return get_all_templates()

    @router.get("/api/v1/fields")
    async def get_fields():
        return {"fields": FIELD_DEFINITIONS, "custom_types": CUSTOM_FIELD_TYPES}

    @router.post("/api/v1/create_form")
    async def create_form(request: Request):
        data = await request.json()
        selected_fields = data.get("fields", [])
        custom_fields = data.get("custom_fields", [])
        # Build the field list
        fields = [f for f in FIELD_DEFINITIONS if f["name"] in selected_fields]
        for cf in custom_fields:
            field = {
                "name": cf["name"],
                "label": cf["name"].replace('_', ' ').title(),
                "data_type": cf["data_type"]
            }
            if cf["data_type"] == "file" and cf.get("accept"):
                field["accept"] = cf["accept"]
            fields.append(field)
        if not fields:
            raise HTTPException(status_code=400, detail="At least one field is required.")
        form_id = str(uuid.uuid4())[:10]
        storage.create_form(form_id, fields)
        return {"form_url": f"/api/v1/data/{form_id}", "fields": fields}

    @router.get("/api/v1/data/{form_id}", response_class=HTMLResponse)
    async def serve_form(request: Request, form_id: str):
        form = storage.get_form(form_id)
        if not form:
            raise HTTPException(status_code=404, detail="Form not found.")
        return templates.TemplateResponse("form.html", {"request": request, "fields": form['fields'], "form_id": form_id})

    @router.post("/api/v1/data/{form_id}")
    async def submit_form(request: Request, form_id: str):
        import os
        import shutil
        from uuid import uuid4
        form = storage.get_form(form_id)
        if not form:
            raise HTTPException(status_code=404, detail="Form not found.")
        data = await request.form()
        submission = {}
        upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        for field in form["fields"]:
            fname = field["name"]
            ftype = field.get("data_type", "text")
            if ftype == "file":
                upload = data.get(fname)
                if upload and hasattr(upload, 'filename') and upload.filename:
                    ext = os.path.splitext(upload.filename)[-1]
                    safe_name = f"{uuid4().hex}_{upload.filename}"
                    file_path = os.path.join(upload_dir, safe_name)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(upload.file, buffer)
                    submission[fname] = f"/uploads/{safe_name}"
                else:
                    submission[fname] = ""
            else:
                submission[fname] = data.get(fname, "")
        storage.add_submission(form_id, submission)
        return JSONResponse(content=submission)

    @router.get("/api/v1/data/{form_id}/excel")
    async def download_excel(form_id: str):
        form = storage.get_form(form_id)
        if not form or not form["submissions"]:
            raise HTTPException(status_code=404, detail="No data found.")
        file_path = storage.export_to_excel(form_id)
        return FileResponse(file_path, filename=f"{form_id}_data.xlsx")

    @router.post("/api/v1/analyze_from_excel/{form_id}")
    async def analyze_from_excel(form_id: str, jd: str = Form(...), selected_pdfs: str = Form(...)):

        # Get all submissions for this form
        submissions = get_form_submissions(form_id)
        if not submissions:
            return JSONResponse(content={"error": "No submissions found."}, status_code=404)

        # Parse selected PDFs
        selected_pdf_list = json.loads(selected_pdfs) if selected_pdfs else []
        
        results = []
        for sub in submissions:
            # Assume the resume file is stored under the key 'resume'
            pdf_path = sub.get('resume')
            if not pdf_path or not os.path.exists(os.path.join(os.getcwd(), pdf_path.lstrip('/'))):
                continue
            
            # Check if this PDF is selected for analysis
            pdf_name = pdf_path.split('/')[-1] if '/' in pdf_path else pdf_path
            if selected_pdf_list and pdf_name not in selected_pdf_list:
                continue
                
            abs_pdf_path = os.path.join(os.getcwd(), pdf_path.lstrip('/'))
            resume_text, links = extract_text_from_pdf(abs_pdf_path)
            match_report = evaluate_resume_against_jd(jd, resume_text)

            # Extract GitHub repo links and process them
            github_questions = []
            if links:
                import re
                github_links = [l['uri'] for l in links if isinstance(l, dict) and 'uri' in l and re.match(r'https://github.com/[^/]+/[^/]+', l['uri'])]
                unique_repos = list(set(github_links))
                for gh_url in unique_repos:
                    qdata = generate_questions_from_github([gh_url], 10)
                    github_questions.append({
                        'repo': gh_url,
                        'questions': qdata.get('questions', []),
                        'summary': qdata.get('summary', '')
                    })
            results.append({
                "pdf_path": os.path.basename(abs_pdf_path),
                "match_report": match_report,
                "links": links,
                "github_questions": github_questions
            })
        return JSONResponse(content=results)

    @router.get("/form-builder", response_class=HTMLResponse)
    async def form_builder(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @router.get("/github_questions", response_class=HTMLResponse)
    async def github_questions_page(request: Request):
        return templates.TemplateResponse("github_questions.html", {"request": request})

    @router.post("/api/v1/github_questions")
    async def github_questions(request: Request):
        data = await request.json()
        github_urls = data.get("github_urls", [])
        num_questions = int(data.get("num_questions", 10))
        result = generate_questions_from_github(github_urls, num_questions)
        return JSONResponse(content=result)

    return router
