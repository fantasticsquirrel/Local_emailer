from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import relationship

from protonmailer.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    schedule_type = Column(String, nullable=False)
    schedule_config = Column(JSON, nullable=True)
    target_tags = Column(String)
    active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    account = relationship("Account")
    template = relationship("Template")
