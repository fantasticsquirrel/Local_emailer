from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from protonmailer import models, schemas
from protonmailer.dependencies import get_db

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=schemas.AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    db_account = models.Account(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.get("/", response_model=list[schemas.AccountRead])
def list_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Account).offset(skip).limit(limit).all()


@router.get("/{account_id}", response_model=schemas.AccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=schemas.AccountRead)
def update_account(
    account_id: int, account_update: schemas.AccountUpdate, db: Session = Depends(get_db)
):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    for field, value in account_update.dict(exclude_unset=True).items():
        setattr(account, field, value)

    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    db.delete(account)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
