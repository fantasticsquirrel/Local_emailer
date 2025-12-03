from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from protonmailer import models, schemas
from protonmailer.dependencies import get_db
from protonmailer.services.template_service import render_template

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplatePreviewRequest(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)


@router.post("/", response_model=schemas.TemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(template: schemas.TemplateCreate, db: Session = Depends(get_db)):
    db_template = models.Template(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.get("/", response_model=list[schemas.TemplateRead])
def list_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Template).offset(skip).limit(limit).all()


@router.get("/{template_id}", response_model=schemas.TemplateRead)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=schemas.TemplateRead)
def update_template(
    template_id: int, template_update: schemas.TemplateUpdate, db: Session = Depends(get_db)
):
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    db.delete(template)
    db.commit()
    return None


@router.post("/{template_id}/preview")
def preview_template(
    template_id: int, preview_data: TemplatePreviewRequest, db: Session = Depends(get_db)
):
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    subject, body_html = render_template(template, preview_data.context)

    return {"subject": subject, "body_html": body_html}
