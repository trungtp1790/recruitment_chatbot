from app.location_slot import (
    resolve_locations_for_turn,
    should_clear_location_for_new_job_query,
)


def test_location_replace_hcm_then_hanoi():
    assert resolve_locations_for_turn("AI Engineer ở Hồ Chí Minh") == ["Hồ Chí Minh"]
    assert resolve_locations_for_turn("AI Engineer ở Hà Nội") == ["Hà Nội"]


def test_gia_lai_unknown_city():
    assert resolve_locations_for_turn("AI Engineer ở Gia Lai") == ["Gia Lai"]


def test_no_location_in_message_returns_none():
    assert resolve_locations_for_turn("Tôi muốn tìm việc AI") is None


def test_tai_sao_alone_does_not_invent_place():
    assert resolve_locations_for_turn("Tại sao không có việc") is None


def test_gia_lai_after_tai_sao_in_same_sentence():
    assert resolve_locations_for_turn("Tại sao không có việc ở Gia Lai") == ["Gia Lai"]


def test_salary_boundary_strips_place():
    r = resolve_locations_for_turn("AI ở Hà Nội, lương 10 triệu")
    assert r == ["Hà Nội"]


def test_new_job_query_clears_stale_location_policy():
    assert should_clear_location_for_new_job_query("Tìm việc AI Engineer") is True
    assert should_clear_location_for_new_job_query("lương 15 triệu") is False
    assert should_clear_location_for_new_job_query("ở Hà Nội") is False


def test_nationwide_explicit_returns_empty_list():
    assert resolve_locations_for_turn("Tìm việc AI toàn quốc") == []
