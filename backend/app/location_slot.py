"""Trích và chuẩn hóa địa điểm theo từng lượt chat (không phụ thuộc Redis)."""

import re

from .text_utils import normalize_text

# (từ khóa đã chuẩn hóa không dấu, chữ thường) -> tên hiển thị khớp cột location trong DB
_LOCATION_ALIASES: list[tuple[list[str], str]] = [
    (["ha noi", "hanoi"], "Hà Nội"),
    (
        ["hcm", "tp hcm", "ho chi minh", "tphcm", "sai gon", "saigon", "tp ho chi minh"],
        "Hồ Chí Minh",
    ),
    (["da nang", "danang"], "Đà Nẵng"),
    (["gia lai", "pleiku"], "Gia Lai"),
    (["can tho"], "Cần Thơ"),
    (["hai phong"], "Hải Phòng"),
]


def _canonical_place_name(place_fragment: str) -> str:
    """Ánh xạ cụm địa danh người dùng về tên chuẩn trong DB (nếu nhận ra)."""
    n = normalize_text(place_fragment.strip())
    if not n:
        return place_fragment.strip()
    for aliases, canonical in _LOCATION_ALIASES:
        for a in aliases:
            na = normalize_text(a)
            if n == na or (len(na) >= 3 and na in n) or (len(n) >= 3 and n in na):
                return canonical
    return " ".join(place_fragment.split())


def resolve_locations_for_turn(message: str) -> list[str] | None:
    """
    Trích địa điểm **trong lượt hội thoại này**.
    - None: không có tín hiệu địa điểm trong câu (memory có thể xóa địa điểm nếu là câu “tìm việc” mới).
    - []: user muốn bỏ lọc địa điểm (toàn quốc / mọi nơi).
    - [..]: thay thế slot.locations bằng danh sách này.
    """
    lowered = normalize_text(message)
    if any(
        m in lowered
        for m in (
            "toan quoc",
            "moi noi",
            "ca nuoc",
            "khong can dia diem",
            "bat ky dau",
            "o dau cung duoc",
        )
    ):
        return []
    found: list[str] = []
    for aliases, canonical in _LOCATION_ALIASES:
        if any(normalize_text(a) in lowered for a in aliases):
            if canonical not in found:
                found.append(canonical)
    if found:
        return found

    m = re.search(
        r"(?:ở|tại)\s+(?!sao\b)(.+?)(?=\s*[,:;]?\s*(?:lương|mức|salary)\b|$)",
        message,
        flags=re.IGNORECASE | re.UNICODE,
    )
    if m:
        raw = m.group(1).strip()
        if raw:
            return [_canonical_place_name(raw)]
    return None


# Cụm gợi ý "đang mở một truy vấn tìm việc mới" (đã chuẩn hóa không dấu)
_NEW_JOB_QUERY_MARKERS: tuple[str, ...] = (
    "tim viec",
    "tim kiem",
    "tim job",
    "kiem viec",
    "tuyen dung",
    "viec lam",
    "can tim",
    "muon tim",
    "dang tim",
    "ung tuyen",
    "xin viec",
)


def is_new_job_query(message: str) -> bool:
    """Câu mở truy vấn tìm việc mới — dùng để reset địa điểm / ngành cũ trong slot."""
    lowered = normalize_text(message)
    return any(m in lowered for m in _NEW_JOB_QUERY_MARKERS)


def should_clear_location_for_new_job_query(message: str) -> bool:
    """
    User nói câu kiểu "tìm việc ..." nhưng không nêu thành phố → bỏ địa điểm cũ trong slot,
    tránh kẹt filter (ví dụ vẫn Đà Nẵng sau khi hỏi chung "Tìm việc AI Engineer").

    Chỉ gọi khi `resolve_locations_for_turn` đã trả về None (không trích được địa điểm trong câu).
    """
    return is_new_job_query(message)
