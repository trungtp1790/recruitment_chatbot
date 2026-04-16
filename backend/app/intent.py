"""Phân loại intent đơn giản (rule-based) — dễ đọc khi học, có thể thay bằng classifier/LLM sau."""

from .text_utils import normalize_text


def detect_intent(message: str) -> str:
    lowered = normalize_text(message)
    if "ban la ai" in lowered or "ban la gi" in lowered:
        return "bot_identity"
    if any(word in lowered for word in ["thoi tiet", "bong da", "am nhac", "nau an"]):
        return "off_topic"
    return "find_job"


def should_update_memory(intent: str) -> bool:
    """Chỉ cập nhật slot khi người dùng đang tìm việc — tránh ghi nhận địa điểm từ câu off-topic."""
    return intent == "find_job"
