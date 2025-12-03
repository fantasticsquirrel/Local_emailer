from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from protonmailer.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    email_address = Column(String, nullable=False, index=True)
    smtp_host = Column(String, nullable=False)
    smtp_port = Column(Integer, nullable=False)
    smtp_username = Column(String, nullable=False)
    smtp_password_encrypted = Column(String, nullable=False)  # TODO: store encrypted
    use_ssl = Column(Boolean, default=False, nullable=False)
    use_tls = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
