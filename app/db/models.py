from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Phone(Base):
    __tablename__ = "phones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    gsmarena_url: Mapped[str] = mapped_column(String(300))
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    specification: Mapped["Specification"] = relationship(
        back_populates="phone", uselist=False, cascade="all, delete-orphan"
    )


class Specification(Base):
    __tablename__ = "specifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_id: Mapped[int] = mapped_column(ForeignKey("phones.id"), unique=True)

    # Structured, queryable columns (drive SQL-based "best/worst X" answers)
    display_size_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    display_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    display_resolution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    chipset: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cpu: Mapped[str | None] = mapped_column(String(300), nullable=True)
    gpu: Mapped[str | None] = mapped_column(String(200), nullable=True)
    os: Mapped[str | None] = mapped_column(String(150), nullable=True)
    ram_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rear_camera_mp: Mapped[float | None] = mapped_column(Float, nullable=True)
    rear_camera_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    front_camera_mp: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_capacity_mah: Mapped[int | None] = mapped_column(Integer, nullable=True)
    battery_active_use_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_endurance_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    charging_speed_w: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_weight_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Full-fidelity columns (feed the RAG document / CrewAI tool)
    raw_specs_json: Mapped[dict] = mapped_column(JSONB)
    raw_text: Mapped[str] = mapped_column(Text)

    phone: Mapped["Phone"] = relationship(back_populates="specification")
