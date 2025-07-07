from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import uuid
from . import gemini, storage
from .models import FormDefinition
from fastapi.templating import Jinja2Templates
from .payloads import FIELD_DEFINITIONS, CUSTOM_FIELD_TYPES
from .templates_config import get_all_templates, get_template_by_name


def get_router(templates: Jinja2Templates):
    router = APIRouter()

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

    return router
