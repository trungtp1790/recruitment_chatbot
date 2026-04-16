import asyncio

import google.generativeai as genai

from .config import settings
from .schemas import JobItem, MemorySlot


def _off_topic_mode() -> str:
    mode = (settings.out_of_scope_mode or "guardrail").strip().lower()
    return mode if mode in {"guardrail", "open"} else "guardrail"


def build_mock_reply(
    message: str, jobs: list[JobItem], slot: MemorySlot, intent: str
) -> str:
    if intent == "off_topic":
        if _off_topic_mode() == "open":
            return (
                "Mình ghi nhận câu hỏi ngoài chủ đề tuyển dụng. "
                "Trong chế độ open, mình vẫn hỗ trợ trả lời ngắn gọn các câu hỏi chung."
            )
        return (
            "Mình là chatbot tuyển dụng, nên chỉ hỗ trợ tìm việc (vị trí, địa điểm, mức lương). "
            "Bạn đang quan tâm loại công việc nào?"
        )
    if intent == "bot_identity":
        return (
            "Tôi là Recruitment Chatbot — trợ lý gợi ý việc làm tiếng Việt, "
            "kết hợp bộ nhớ phiên (Redis), dữ liệu Postgres và LLM (Gemini hoặc chế độ demo)."
        )
    if not jobs:
        hints: list[str] = []
        if slot.industries:
            hints.append("ngành " + ", ".join(slot.industries))
        if slot.locations:
            hints.append("tại " + ", ".join(slot.locations))
        if slot.salary_min:
            hints.append(f"lương từ {slot.salary_min:,.0f} VND".replace(",", "."))
        ctx = f" ({'; '.join(hints)})" if hints else ""
        return (
            "Mình chưa tìm thấy tin nào khớp bộ lọc"
            + ctx
            + ". Thử nới điều kiện (bỏ địa điểm, đổi thành phố khác) hoặc kiểm tra dữ liệu mẫu trong database."
        )
    first = jobs[0]
    location = ", ".join(slot.locations) if slot.locations else "toàn quốc"
    return (
        f"Mình tìm thấy {len(jobs)} công việc phù hợp tại {location}. "
        f"Gợi ý đầu tiên: {first.title} tại {first.company}."
    )


async def generate_reply(
    message: str, jobs: list[JobItem], slot: MemorySlot, intent: str
) -> str:
    if settings.use_mock_llm or not settings.gemini_api_key:
        return build_mock_reply(message, jobs, slot, intent)

    def _call_gemini() -> str:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        jobs_text = "\n".join(
            f"- {job.title} | {job.company} | {job.location} | {job.salary_min or 0}-{job.salary_max or 0} VND"
            for job in jobs[:5]
        )
        off_topic_hint = (
            "Intent: off_topic — lịch sự từ chối, gợi ý quay lại tìm việc. Không bịa thông tin ngoài lĩnh vực."
            if _off_topic_mode() == "guardrail"
            else (
                "Intent: off_topic — hệ thống đang ở mode open, hãy trả lời bình thường câu hỏi ngoài tuyển dụng, "
                "ngắn gọn, hữu ích, không bịa dữ kiện."
            )
        )
        intent_hint = {
            "off_topic": off_topic_hint,
            "bot_identity": "Intent: bot_identity — giới thiệu ngắn bạn là chatbot tuyển dụng, không liệt kê job.",
            "find_job": "Intent: find_job — tóm tắt job phù hợp hoặc gợi ý điều chỉnh bộ lọc.",
        }.get(intent, "Intent: find_job")
        prompt = f"""
Bạn là trợ lý tuyển dụng. Trả lời bằng tiếng Việt tự nhiên, ngắn gọn, rõ ràng.
{intent_hint}
Tin nhắn người dùng: {message}
Ngữ cảnh đã lưu: industries={slot.industries}, locations={slot.locations}, salary_min={slot.salary_min}
Danh sách việc làm gợi ý:
{jobs_text if jobs_text else "- Không có job phù hợp"}
"""
        response = model.generate_content(prompt)
        return (response.text or "").strip()

    try:
        text = await asyncio.to_thread(_call_gemini)
        return text if text else build_mock_reply(message, jobs, slot, intent)
    except Exception:
        return build_mock_reply(message, jobs, slot, intent)
