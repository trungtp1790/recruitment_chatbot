import re
import unicodedata

_FIND_JOB_PREFIX_RE = re.compile(
    r"^\s*(tìm\s+việc|tìm\s+kiếm|tìm\s+job|kiếm\s+việc|việc\s+làm|"
    r"cần\s+tìm|muốn\s+tìm|đang\s+tìm|ứng\s+tuyển|xin\s+việc)\s*[,:]?\s*",
    re.IGNORECASE | re.UNICODE,
)


def strip_find_job_prefix(message: str) -> str:
    """Bỏ cụm mở đầu kiểu «Tìm việc» để ILIKE title/industry khớp phần còn lại."""
    s = _FIND_JOB_PREFIX_RE.sub("", message.strip(), count=1).strip()
    return s if s else message.strip()


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text
