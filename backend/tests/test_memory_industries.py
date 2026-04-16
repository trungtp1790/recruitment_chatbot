from app.memory_service import resolve_industries_for_turn


def test_new_job_query_replaces_not_append():
    assert resolve_industries_for_turn("Tìm việc AI Engineer") == ["Công nghệ thông tin / AI"]
    assert resolve_industries_for_turn("Tìm việc Luật") == ["Luật"]
    assert resolve_industries_for_turn("Tìm việc Công nghệ thông tin") == ["Công nghệ thông tin / AI"]


def test_continuation_does_not_change_industry_slot_signal():
    assert resolve_industries_for_turn("lương từ 15 triệu") is None
    assert resolve_industries_for_turn("ở Hà Nội") is None


def test_law_keywords():
    assert "Luật" in (resolve_industries_for_turn("Tìm việc pháp lý") or [])
