from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from protonmailer import models, schemas
from protonmailer.dependencies import get_db

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("/", response_model=schemas.CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    campaign_data = campaign.dict()
    if campaign_data.get("schedule_config") is not None:
        campaign_data["schedule_config"] = campaign_data["schedule_config"].dict()
    db_campaign = models.Campaign(**campaign_data)
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


@router.get("/", response_model=list[schemas.CampaignRead])
def list_campaigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Campaign).offset(skip).limit(limit).all()


@router.get("/{campaign_id}", response_model=schemas.CampaignRead)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=schemas.CampaignRead)
def update_campaign(
    campaign_id: int, campaign_update: schemas.CampaignUpdate, db: Session = Depends(get_db)
):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    update_data = campaign_update.dict(exclude_unset=True)
    if "schedule_config" in update_data and update_data["schedule_config"] is not None:
        update_data["schedule_config"] = update_data["schedule_config"].dict()

    for field, value in update_data.items():
        setattr(campaign, field, value)

    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    db.delete(campaign)
    db.commit()
    return None


@router.post("/{campaign_id}/activate", response_model=schemas.CampaignRead)
def activate_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    campaign.active = True
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/deactivate", response_model=schemas.CampaignRead)
def deactivate_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    campaign.active = False
    db.commit()
    db.refresh(campaign)
    return campaign
