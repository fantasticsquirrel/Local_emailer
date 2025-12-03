from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from protonmailer.database import Base


class QueuedEmail(Base):
    __tablename__ = "queued_emails"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    last_error = Column(Text)
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    campaign = relationship("Campaign")
    account = relationship("Account")
