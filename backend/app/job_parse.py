"""Parse HTML TopCV → cấu trúc job (không I/O, không asyncpg)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from .text_utils import normalize_text


@dataclass
class IngestedJob:
    id: str
    title: str
    company: str
    location: str | None
    industry: str
    salary_min: int | None
    salary_max: int | None
    description: str
    apply_url: str
    source: str
    source_id: str


def parse_salary_vn(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return None, None
    low = normalize_text(text)
    if "thoa thuan" in low or "negotiate" in low:
        return None, None
    nums = re.findall(r"(\d+(?:[.,]\d+)?)", text)
    vals: list[int] = []
    for n in nums[:4]:
        try:
            v = float(n.replace(",", "."))
            if v < 1000:
                v *= 1_000_000
            vals.append(int(v))
        except ValueError:
            continue
    if len(vals) >= 2:
        return min(vals[0], vals[1]), max(vals[0], vals[1])
    if len(vals) == 1:
        return vals[0], vals[0]
    return None, None


def infer_industry_from_text(title: str, tag_texts: list[str]) -> str:
    blob = normalize_text(f"{title} {' '.join(tag_texts)}")
    padded = f" {blob} "
    tech = (
        "machine learning" in blob
        or "tri tue nhan tao" in blob
        or "data scientist" in blob
        or "mlops" in blob
        or "developer" in blob
        or "lap trinh" in blob
        or "cntt" in blob
        or "backend" in blob
        or "frontend" in blob
        or "devops" in blob
        or "engineer" in blob
        or " ai " in padded
    )
    if tech:
        return "Công nghệ thông tin / AI"
    if "ke toan" in blob or "accounting" in blob:
        return "Kế toán"
    if "marketing" in blob or "seo" in blob or "quang cao" in blob:
        return "Marketing"
    return "Tổng hợp"


def parse_topcv_listing(html: str, limit: int) -> list[IngestedJob]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[IngestedJob] = []
    for card in soup.select("div.job-item-search-result[data-job-id]"):
        if len(out) >= limit:
            break
        sid = card.get("data-job-id")
        if not sid:
            continue
        link = card.select_one("h3.title a[href*='viec-lam']")
        if not link or not link.get("href"):
            continue
        href = str(link["href"]).split("&")[0].split("?")[0]
        if not href.startswith("http"):
            href = "https://www.topcv.vn" + href
        title = link.get_text(strip=True) or (link.get("title") or "").strip()
        company_el = card.select_one("span.company-name")
        company = company_el.get_text(strip=True) if company_el else "—"
        city_el = card.select_one("span.city-text")
        location = city_el.get_text(strip=True) if city_el else None
        sal_el = card.select_one("label.title-salary") or card.select_one("label.salary span")
        salary_text = sal_el.get_text(strip=True) if sal_el else None
        smin, smax = parse_salary_vn(salary_text)
        tags = [a.get_text(strip=True) for a in card.select("div.tag a.item-tag") if a.get_text(strip=True)]
        industry = infer_industry_from_text(title, tags)
        desc = f"{title} · {company}"[:500]
        out.append(
            IngestedJob(
                id=f"topcv-{sid}",
                title=title,
                company=company,
                location=location,
                industry=industry,
                salary_min=smin,
                salary_max=smax,
                description=desc,
                apply_url=href,
                source="topcv",
                source_id=str(sid),
            )
        )
    return out
