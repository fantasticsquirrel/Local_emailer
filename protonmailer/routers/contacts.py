import csv
import io
from typing import Optional

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from protonmailer import models, schemas
from protonmailer.dependencies import get_db

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=schemas.ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    db_contact = models.Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.get("/", response_model=list[schemas.ContactRead])
def list_contacts(
    tag: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    query = db.query(models.Contact)
    if tag:
        query = query.filter(models.Contact.tags.contains(tag))
    return query.offset(skip).limit(limit).all()


@router.get("/{contact_id}", response_model=schemas.ContactRead)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=schemas.ContactRead)
def update_contact(
    contact_id: int, contact_update: schemas.ContactUpdate, db: Session = Depends(get_db)
):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    for field, value in contact_update.dict(exclude_unset=True).items():
        setattr(contact, field, value)

    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/import-csv")
async def import_contacts(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text_stream = io.StringIO(content.decode("utf-8"))
    reader = csv.DictReader(text_stream)

    created = 0
    updated = 0
    failed = 0

    for row in reader:
        email = (row.get("email") or "").strip()
        name = (row.get("name") or "").strip() or None
        tags = (row.get("tags") or "").strip()

        if not email:
            failed += 1
            continue

        try:
            normalized_email = validate_email(email, check_deliverability=False).email
        except EmailNotValidError:
            failed += 1
            continue

        contact = db.query(models.Contact).filter(models.Contact.email == normalized_email).first()
        if contact:
            contact.name = name or contact.name
            contact.tags = tags or contact.tags
            updated += 1
        else:
            contact = models.Contact(email=normalized_email, name=name, tags=tags)
            db.add(contact)
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "failed": failed}


@router.get("/export-csv")
def export_contacts(db: Session = Depends(get_db)):
    contacts = db.query(models.Contact).all()

    def iter_rows():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["email", "name", "tags"])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        for contact in contacts:
            writer.writerow([contact.email, contact.name or "", contact.tags or ""])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    headers = {"Content-Disposition": "attachment; filename=contacts.csv"}
    return StreamingResponse(iter_rows(), media_type="text/csv", headers=headers)
