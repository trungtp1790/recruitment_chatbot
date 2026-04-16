import json

from redis.asyncio import Redis

from .location_slot import (
    is_new_job_query,
    resolve_locations_for_turn,
    should_clear_location_for_new_job_query,
)
from .schemas import MemorySlot
from .text_utils import normalize_text


def _extract_salary_min(message: str) -> int | None:
    normalized = normalize_text(message)
    digits = "".join(ch if ch.isdigit() else " " for ch in normalized).split()
    if not digits:
        return None
    value = int(digits[0])
    # Heuristic: "15 triệu" -> 15000000
    if "trieu" in normalized and value < 1000:
        value *= 1_000_000
    return value


def _contains_any(message: str, words: list[str]) -> bool:
    lowered = normalize_text(message)
    return any(normalize_text(w) in lowered for w in words)


def resolve_industries_for_turn(message: str) -> list[str] | None:
    """
    Chỉ khi câu là truy vấn tìm việc mới: trả về danh sách ngành suy ra từ **lượt này** (thay thế slot).
    None = không đổi slot.industries (câu tiếp nối, chỉ lương/địa điểm, ...).
    """
    if not is_new_job_query(message):
        return None
    lowered = normalize_text(message)
    out: list[str] = []

    if _contains_any(
        lowered,
        [
            "luat",
            "luat su",
            "phap ly",
            "phap luat",
            "legal",
            "lawyer",
            "tu van luat",
            "cong chung",
        ],
    ):
        if "Luật" not in out:
            out.append("Luật")

    if _contains_any(lowered, ["ke toan", "accounting"]):
        if "Kế toán" not in out:
            out.append("Kế toán")

    padded = f" {lowered} "
    if (
        " ai " in padded
        or _contains_any(
            lowered,
            [
                "tri tue nhan tao",
                "machine learning",
                "hoc may",
                "cntt",
                "cong nghe thong tin",
                "ky su phan mem",
                "developer",
                "lap trinh",
                "data scientist",
                "mlops",
                "backend",
                "frontend",
                "devops",
            ],
        )
        or _contains_any(lowered, ["engineer"])
    ):
        tag = "Công nghệ thông tin / AI"
        if tag not in out:
            out.append(tag)

    if _contains_any(lowered, ["marketing", "tiep thi", "tiếp thị"]):
        if "Marketing" not in out:
            out.append("Marketing")

    return out


async def load_slot(redis: Redis, session_id: str) -> MemorySlot:
    raw = await redis.get(f"session:{session_id}:slot")
    if not raw:
        return MemorySlot()
    return MemorySlot.model_validate_json(raw)


async def update_slot(redis: Redis, session_id: str, message: str, ttl_seconds: int = 3600) -> MemorySlot:
    slot = await load_slot(redis, session_id)
    lowered = normalize_text(message)

    new_inds = resolve_industries_for_turn(message)
    if new_inds is not None:
        slot.industries = new_inds

    if is_new_job_query(message) and not _contains_any(
        lowered,
        ["luong", "salary", "muc thu nhap", "thu nhap"],
    ):
        slot.salary_min = None

    new_locs = resolve_locations_for_turn(message)
    if new_locs is not None:
        slot.locations = new_locs
    elif should_clear_location_for_new_job_query(message):
        slot.locations = []

    salary_min = _extract_salary_min(message)
    if salary_min and _contains_any(lowered, ["luong", "salary", "muc thu nhap"]):
        slot.salary_min = salary_min

    await redis.set(f"session:{session_id}:slot", slot.model_dump_json(), ex=ttl_seconds)
    return slot


def slot_to_context(slot: MemorySlot) -> str:
    payload = slot.model_dump()
    return json.dumps(payload, ensure_ascii=False)
