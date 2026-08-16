from datetime import date, datetime
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


money = Numeric(20, 4)
percentage = Numeric(9, 4)


class FinancialAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "financial_accounts"

    notion_page_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    notion_last_edited_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_account_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    institution: Mapped[str] = mapped_column(String(120), default="")
    account_type: Mapped[str] = mapped_column(String(60), default="OTHER")
    currency: Mapped[str] = mapped_column(String(3), default="KRW")
    source_type: Mapped[str] = mapped_column(String(20), default="NOTION")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    include_in_net_worth: Mapped[bool] = mapped_column(Boolean, default=True)
    memo: Mapped[str | None] = mapped_column(Text)


class ManualAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "manual_assets"

    notion_page_id: Mapped[str] = mapped_column(String(64), unique=True)
    notion_last_edited_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("financial_accounts.id"))
    name: Mapped[str] = mapped_column(String(200))
    asset_type: Mapped[str] = mapped_column(String(80), default="OTHER")
    asset_class: Mapped[str] = mapped_column(String(40), default="기타자산")
    amount_native: Mapped[Decimal] = mapped_column(money, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="KRW")
    amount_krw: Mapped[Decimal] = mapped_column(money, default=0)
    liquidity: Mapped[str | None] = mapped_column(String(30))
    include_in_net_worth: Mapped[bool] = mapped_column(Boolean, default=True)
    valued_at: Mapped[date | None] = mapped_column(Date)


class SavingsProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "savings_products"

    notion_page_id: Mapped[str] = mapped_column(String(64), unique=True)
    notion_last_edited_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("financial_accounts.id"))
    name: Mapped[str] = mapped_column(String(200))
    institution: Mapped[str] = mapped_column(String(120), default="")
    product_type: Mapped[str] = mapped_column(String(80), default="OTHER")
    current_balance: Mapped[Decimal] = mapped_column(money, default=0)
    initial_deposit: Mapped[Decimal] = mapped_column(money, default=0)
    monthly_contribution: Mapped[Decimal] = mapped_column(money, default=0)
    base_rate: Mapped[Decimal] = mapped_column(percentage, default=0)
    bonus_rate: Mapped[Decimal] = mapped_column(percentage, default=0)
    interest_method: Mapped[str | None] = mapped_column(String(80))
    contribution_method: Mapped[str | None] = mapped_column(String(80))
    tax_type: Mapped[str | None] = mapped_column(String(40))
    opened_at: Mapped[date | None] = mapped_column(Date)
    maturity_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    include_in_net_worth: Mapped[bool] = mapped_column(Boolean, default=True)


class Debt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "debts"

    notion_page_id: Mapped[str] = mapped_column(String(64), unique=True)
    notion_last_edited_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("financial_accounts.id"))
    name: Mapped[str] = mapped_column(String(200))
    institution: Mapped[str] = mapped_column(String(120), default="")
    debt_type: Mapped[str] = mapped_column(String(80), default="OTHER")
    original_balance: Mapped[Decimal] = mapped_column(money, default=0)
    current_balance: Mapped[Decimal] = mapped_column(money, default=0)
    annual_rate: Mapped[Decimal] = mapped_column(percentage, default=0)
    repayment_type: Mapped[str | None] = mapped_column(String(80))
    monthly_payment: Mapped[Decimal] = mapped_column(money, default=0)
    opened_at: Mapped[date | None] = mapped_column(Date)
    maturity_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    include_in_net_worth: Mapped[bool] = mapped_column(Boolean, default=True)


class FinancialGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "financial_goals"

    notion_page_id: Mapped[str] = mapped_column(String(64), unique=True)
    notion_last_edited_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    name: Mapped[str] = mapped_column(String(200))
    goal_type: Mapped[str] = mapped_column(String(40))
    target_amount: Mapped[Decimal] = mapped_column(money)
    starting_amount: Mapped[Decimal] = mapped_column(money, default=0)
    start_date: Mapped[date | None] = mapped_column(Date)
    target_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    memo: Mapped[str | None] = mapped_column(Text)


class AllocationTarget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "allocation_targets"

    notion_page_id: Mapped[str] = mapped_column(String(64), unique=True)
    notion_last_edited_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    name: Mapped[str] = mapped_column(String(200))
    classification_type: Mapped[str] = mapped_column(String(40), default="ASSET_CLASS")
    target_key: Mapped[str] = mapped_column(String(80), index=True)
    target_weight: Mapped[Decimal] = mapped_column(percentage)
    minimum_weight: Mapped[Decimal | None] = mapped_column(percentage)
    maximum_weight: Mapped[Decimal | None] = mapped_column(percentage)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[date | None] = mapped_column(Date)
