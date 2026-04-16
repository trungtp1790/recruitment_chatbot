from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class JobItem(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salary_min: int | None = None
    salary_max: int | None = None
    apply_url: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    jobs: list[JobItem] = []
    intent: str
    memory_updated: dict = {}


class MemorySlot(BaseModel):
    industries: list[str] = []
    locations: list[str] = []
    salary_min: int | None = None
