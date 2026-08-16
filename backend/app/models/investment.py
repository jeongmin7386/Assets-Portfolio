from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


money = Numeric(24, 8)


class InvestmentAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "investment_accounts"

    financial_account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("financial_accounts.id"))
    provider: Mapped[str] = mapped_column(String(20), default="TOSS")
    provider_account_id: Mapped[str] = mapped_column(String(128), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    currency: Mapped[str] = mapped_column(String(3), default="KRW")
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SecurityMaster(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "security_master"
    __table_args__ = (UniqueConstraint("symbol", "market", name="uq_security_symbol_market"),)

    symbol: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    market: Mapped[str] = mapped_column(String(40))
    security_type: Mapped[str] = mapped_column(String(40), default="UNKNOWN")
    currency: Mapped[str] = mapped_column(String(3))


class InvestmentPosition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "investment_positions"
    __table_args__ = (UniqueConstraint("account_id", "symbol", name="uq_position_account_symbol"),)

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("investment_accounts.id"))
    symbol: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    market: Mapped[str] = mapped_column(String(40))
    security_type: Mapped[str] = mapped_column(String(40), default="UNKNOWN")
    currency: Mapped[str] = mapped_column(String(3))
    quantity: Mapped[Decimal] = mapped_column(money, default=0)
    average_price: Mapped[Decimal] = mapped_column(money, default=0)
    cost_basis: Mapped[Decimal] = mapped_column(money, default=0)
    current_price: Mapped[Decimal] = mapped_column(money, default=0)
    market_value_native: Mapped[Decimal] = mapped_column(money, default=0)
    market_value_krw: Mapped[Decimal] = mapped_column(money, default=0)
    unrealized_pnl_native: Mapped[Decimal] = mapped_column(money, default=0)
    unrealized_pnl_krw: Mapped[Decimal] = mapped_column(money, default=0)
    return_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ExchangeRate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("base_currency", "quote_currency", "quoted_at", name="uq_exchange_quote"),)

    base_currency: Mapped[str] = mapped_column(String(3))
    quote_currency: Mapped[str] = mapped_column(String(3))
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    provider: Mapped[str] = mapped_column(String(30), default="TOSS")
    quoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
