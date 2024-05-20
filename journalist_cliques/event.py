from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    id: str = Field(..., description="Unique identifier of the event")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the event"
    )
    type: str = Field(..., description="Type of the event")
    data: dict = Field(default_factory=dict, description="Data of the event")
