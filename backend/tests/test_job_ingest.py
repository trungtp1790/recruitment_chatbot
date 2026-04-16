from app.job_parse import parse_salary_vn, parse_topcv_listing

_TOPCV_SNIPPET = """
<div class="job-item-search-result" data-job-id="999001">
  <div class="body">
    <div class="title-block">
      <h3 class="title">
        <a href="https://www.topcv.vn/viec-lam/ky-su-ai/999001.html?x=1">
          <span>Kỹ sư AI thử nghiệm</span>
        </a>
      </h3>
      <a class="company"><span class="company-name">Công ty Test</span></a>
      <label class="title-salary">20 - 35 triệu</label>
    </div>
  </div>
  <div class="info">
    <label class="address"><span class="city-text">Hà Nội</span></label>
  </div>
  <div class="tag"><a class="item-tag">Machine Learning</a></div>
</div>
"""


def test_parse_topcv_snippet():
    jobs = parse_topcv_listing(_TOPCV_SNIPPET, limit=10)
    assert len(jobs) == 1
    j = jobs[0]
    assert j.id == "topcv-999001"
    assert "AI" in j.title or "ai" in j.title.lower()
    assert j.company == "Công ty Test"
    assert j.location == "Hà Nội"
    assert j.source == "topcv"
    assert j.apply_url == "https://www.topcv.vn/viec-lam/ky-su-ai/999001.html"
    assert j.industry == "Công nghệ thông tin / AI"


def test_parse_salary_range():
    assert parse_salary_vn("12 - 15 triệu") == (12_000_000, 15_000_000)
