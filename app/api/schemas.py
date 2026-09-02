from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


QuestionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=1000)]
PhoneName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]


class AskRequest(BaseModel):
    question: QuestionText


class AskResponse(BaseModel):
    question: str
    answer: str


class ReviewRequest(BaseModel):
    phone_name: PhoneName


class ReviewResponse(BaseModel):
    phone_name: str
    review: str


class PhoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    gsmarena_url: str
    release_year: int | None = None
    display_size_in: float | None = None
    display_type: str | None = None
    display_resolution: str | None = None
    chipset: str | None = None
    cpu: str | None = None
    gpu: str | None = None
    os: str | None = None
    ram_gb: int | None = None
    storage_gb: int | None = None
    rear_camera_summary: str | None = None
    front_camera_mp: float | None = None
    battery_capacity_mah: int | None = None
    battery_active_use_hours: float | None = None
    battery_endurance_hours: int | None = None
    charging_speed_w: int | None = None
    body_weight_g: float | None = None
    price_usd: float | None = None
    price_summary: str | None = None

    @classmethod
    def from_phone(cls, phone) -> "PhoneOut":
        """Phone's structured spec fields live on the related Specification row,
        not on Phone itself - flatten the two before validating."""
        spec = phone.specification
        return cls(
            name=phone.name,
            gsmarena_url=phone.gsmarena_url,
            release_year=phone.release_year,
            display_size_in=spec.display_size_in if spec else None,
            display_type=spec.display_type if spec else None,
            display_resolution=spec.display_resolution if spec else None,
            chipset=spec.chipset if spec else None,
            cpu=spec.cpu if spec else None,
            gpu=spec.gpu if spec else None,
            os=spec.os if spec else None,
            ram_gb=spec.ram_gb if spec else None,
            storage_gb=spec.storage_gb if spec else None,
            rear_camera_summary=spec.rear_camera_summary if spec else None,
            front_camera_mp=spec.front_camera_mp if spec else None,
            battery_capacity_mah=spec.battery_capacity_mah if spec else None,
            battery_active_use_hours=spec.battery_active_use_hours if spec else None,
            battery_endurance_hours=spec.battery_endurance_hours if spec else None,
            charging_speed_w=spec.charging_speed_w if spec else None,
            body_weight_g=spec.body_weight_g if spec else None,
            price_usd=spec.price_usd if spec else None,
            price_summary=spec.price_summary if spec else None,
        )
