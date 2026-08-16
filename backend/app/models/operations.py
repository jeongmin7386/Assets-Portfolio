from datetime import date, datetime
from decimal import Decimal
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


money = Numeric(20, 4)


class AssetSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "asset_snapshots"

    snapshot_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    manual_assets_value: Mapped[Decimal] = mapped_column(money, default=0)
    cash_value: Mapped[Decimal] = mapped_column(money, default=0)
    savings_value: Mapped[Decimal] = mapped_column(money, default=0)
    investment_value: Mapped[Decimal] = mapped_column(money, default=0)
    gold_value: Mapped[Decimal] = mapped_column(money, default=0)
    deposit_value: Mapped[Decimal] = mapped_column(money, default=0)
    other_assets_value: Mapped[Decimal] = mapped_column(money, default=0)
    total_assets: Mapped[Decimal] = mapped_column(money, default=0)
    total_debts: Mapped[Decimal] = mapped_column(money, default=0)
    net_worth: Mapped[Decimal] = mapped_column(money, default=0)


class AssetSnapshotItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_snapshot_items"
    __table_args__ = (UniqueConstraint("snapshot_id", "source_type", "source_id", name="uq_snapshot_source"),)

    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asset_snapshots.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(30))
    source_id: Mapped[str] = mapped_column(String(128))
    asset_class: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    value_krw: Mapped[Decimal] = mapped_column(money)


class SyncRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sync_runs"

    provider: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)


class ProviderCache(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_cache"

    provider: Mapped[str] = mapped_column(String(30))
    cache_key: Mapped[str] = mapped_column(String(200), unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
