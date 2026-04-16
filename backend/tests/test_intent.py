from app.intent import detect_intent, should_update_memory


def test_detect_find_job():
    assert detect_intent("Tìm việc kế toán Hà Nội") == "find_job"


def test_detect_off_topic():
    assert detect_intent("Thời tiết hôm nay thế nào?") == "off_topic"


def test_detect_bot_identity():
    assert detect_intent("Bạn là ai?") == "bot_identity"
    assert detect_intent("Ban la gi vay") == "bot_identity"


def test_should_update_memory():
    assert should_update_memory("find_job") is True
    assert should_update_memory("off_topic") is False
    assert should_update_memory("bot_identity") is False
