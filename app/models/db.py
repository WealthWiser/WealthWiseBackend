from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Date, Numeric, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    first_name = Column(String)
    last_name = Column(String)
    gender = Column(String)
    country = Column(String)
    dob = Column(Date)

    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_hash = Column(String, nullable=False)
    revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class LoginAudit(Base):
    __tablename__ = "login_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)

    ip_address = Column(INET)
    user_agent = Column(String)
    success = Column(Boolean)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    txn_date = Column(Date, nullable=False)
    description = Column(String, nullable=False)

    debit = Column(Numeric(16, 2))
    credit = Column(Numeric(16, 2))
    amount = Column(Numeric(16, 2))
    balance = Column(Numeric(16, 2))

    category = Column(JSONB, nullable=False, server_default="{}")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(debit, credit) <= 1",
            name="debit_credit_exclusive"
        ),
        UniqueConstraint(
            "user_id", "txn_date", "amount", "description", "balance",
            name="unique_txn_per_user"
        ),
    )