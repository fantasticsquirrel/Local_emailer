from sqlalchemy import Column, DateTime, Integer, String, func

from protonmailer.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    name = Column(String)
    tags = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
