from app.text_utils import strip_find_job_prefix


def test_strip_find_job_prefix():
    assert strip_find_job_prefix("Tìm việc Luật") == "Luật"
    assert strip_find_job_prefix("Tìm việc AI Engineer") == "AI Engineer"
    assert strip_find_job_prefix("Xin chào") == "Xin chào"
