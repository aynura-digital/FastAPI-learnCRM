from datetime import datetime

from pydantic import BaseModel


class SyncLogResponse(BaseModel):
    id: str
    direction: str
    entity_type: str
    entity_id: str | None = None
    action: str
    status: str
    http_status_code: int | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
