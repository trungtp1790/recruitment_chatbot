"""
Đồng bộ tin tuyển dụng từ web vào Postgres (upsert theo source + source_id).

- TopCV: HTML danh sách có SSR → parse được bằng httpx + BeautifulSoup (xem job_parse.py).
- ITviec: thường bị Cloudflare chặn bot → mặc định bỏ qua, trả ghi chú trong response.
- LinkedIn: không hỗ trợ crawl công khai trong repo này (điều khoản + đăng nhập) → bỏ qua.

Chạy tay:  python -m app.job_ingest
API:       POST /api/admin/jobs/sync  (header X-Sync-Secret nếu cấu hình SYNC_JOBS_SECRET)
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

import asyncpg
import httpx

from .config import settings
from .db import _normalize_asyncpg_dsn
from .job_parse import IngestedJob, parse_topcv_listing

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _topcv_browser_headers(user_agent: str) -> dict[str, str]:
    """Header gần giống Chrome — giảm khả năng TopCV/Cloudflare trả 520 cho client tối giản."""
    return {
        "User-Agent": user_agent,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }


_RETRYABLE_STATUS = frozenset({429, 502, 503, 520, 521, 522, 524})


async def fetch_topcv_jobs(client: httpx.AsyncClient, url: str, limit: int) -> list[IngestedJob]:
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            # Warm-up: một số WAF cần cookie / phiên từ trang chủ trước khi cho list.
            if attempt == 0:
                w = await client.get("https://www.topcv.vn/", timeout=25.0)
                if w.status_code >= 400:
                    logger.debug("TopCV warm-up HTTP %s", w.status_code)
            list_headers = {
                "Referer": "https://www.topcv.vn/",
                "Sec-Fetch-Site": "same-origin",
            }
            r = await client.get(url, headers=list_headers, timeout=45.0)
            if r.status_code in _RETRYABLE_STATUS:
                raise httpx.HTTPStatusError(
                    f"retryable {r.status_code}", request=r.request, response=r
                )
            r.raise_for_status()
            return parse_topcv_listing(r.text, limit=limit)
        except (httpx.HTTPStatusError, httpx.TransportError) as e:
            last_exc = e
            if attempt < 2:
                wait = 2.0 * (attempt + 1)
                logger.warning(
                    "TopCV fetch lần %s lỗi (%s), chờ %ss rồi thử lại...",
                    attempt + 1,
                    e,
                    wait,
                )
                await asyncio.sleep(wait)
            else:
                break
    assert last_exc is not None
    raise last_exc


async def probe_itviec(client: httpx.AsyncClient) -> str:
    """Kiểm tra nhanh — nếu bị Cloudflare thì không parse được."""
    try:
        r = await client.get("https://itviec.com/it-jobs", timeout=25.0)
        body = r.text[:2000].lower()
        if "just a moment" in body or "cf-chl" in body or r.status_code >= 400:
            return (
                "ITviec trả về thử thách Cloudflare hoặc HTTP lỗi — cần trình duyệt thật "
                "(Playwright + tuân thủ robots/ToS) hoặc nguồn dữ liệu được phép."
            )
        return "Trang ITviec không ở dạng parse đơn giản trong build này; hãy bổ sung spider Playwright riêng nếu được phép."
    except Exception as e:
        return f"Không tải được ITviec: {e!s}"


UPSERT_SQL = """
INSERT INTO jobs (
    id, title, company, location, industry, salary_min, salary_max,
    description, apply_url, source, source_id, is_active, posted_at, updated_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, TRUE, NOW(), NOW()
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    company = EXCLUDED.company,
    location = EXCLUDED.location,
    industry = EXCLUDED.industry,
    salary_min = EXCLUDED.salary_min,
    salary_max = EXCLUDED.salary_max,
    description = EXCLUDED.description,
    apply_url = EXCLUDED.apply_url,
    source = EXCLUDED.source,
    source_id = EXCLUDED.source_id,
    is_active = TRUE,
    updated_at = NOW()
"""


async def upsert_jobs(pool: asyncpg.Pool, jobs: list[IngestedJob]) -> int:
    if not jobs:
        return 0
    async with pool.acquire() as conn:
        for j in jobs:
            await conn.execute(
                UPSERT_SQL,
                j.id,
                j.title,
                j.company,
                j.location,
                j.industry,
                j.salary_min,
                j.salary_max,
                j.description,
                j.apply_url,
                j.source,
                j.source_id,
            )
    return len(jobs)


async def sync_jobs_from_web(pg_pool: asyncpg.Pool | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "topcv": 0,
        "itviec": 0,
        "linkedin": 0,
        "notes": [],
    }
    ua = settings.crawl_user_agent or DEFAULT_UA
    headers = _topcv_browser_headers(ua)
    limits = httpx.Limits(max_connections=5)
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, limits=limits) as client:
        if settings.crawl_topcv_enabled:
            created_pool: asyncpg.Pool | None = None
            jobs: list[IngestedJob] | None = None
            try:
                jobs = await fetch_topcv_jobs(
                    client, settings.topcv_jobs_list_url, settings.crawl_topcv_max_jobs
                )
            except Exception as e:
                logger.warning(
                    "TopCV tải trang thất bại: %s",
                    e,
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )
                hint = ""
                if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                    if e.response.status_code in (520, 521, 522, 524):
                        hint = (
                            " TopCV/Cloudflare có thể chặn IP hoặc yêu cầu trình duyệt thật "
                            "(VPN/mạng khác, hoặc sync trong Docker; xem README)."
                        )
                result["notes"].append(f"topcv (tải web): {e!s}.{hint}")

            if jobs is not None:
                try:
                    pool = pg_pool
                    if pool is None:
                        created_pool = await asyncpg.create_pool(
                            _normalize_asyncpg_dsn(settings.database_url), min_size=1, max_size=3
                        )
                        pool = created_pool
                    result["topcv"] = await upsert_jobs(pool, jobs)
                    logger.info("TopCV ingest: %s jobs", result["topcv"])
                except Exception as e:
                    logger.warning(
                        "TopCV ghi Postgres thất bại: %s",
                        e,
                        exc_info=logger.isEnabledFor(logging.DEBUG),
                    )
                    db_hint = ""
                    _eno = getattr(e, "errno", None)
                    _wno = getattr(e, "winerror", None)
                    if isinstance(e, OSError) and (_eno == 11001 or _wno == 11001):
                        db_hint = (
                            " Trên Windows, lỗi này thường do host trong DATABASE_URL không resolve "
                            "(vd. «postgres» chỉ có trong mạng Docker). Chạy ingest trên máy host: "
                            "dùng localhost và cổng map, vd. postgresql+asyncpg://...@127.0.0.1:5432/..."
                        )
                    elif "getaddrinfo" in str(e).lower() or "name or service not known" in str(e).lower():
                        db_hint = (
                            " Kiểm tra DATABASE_URL: hostname phải resolve được từ máy đang chạy "
                            "(localhost/127.0.0.1 khi Postgres chạy local hoặc port-forward)."
                        )
                    elif isinstance(e, ConnectionRefusedError) or _wno == 1225:
                        db_hint = (
                            " Postgres không lắng nghe tại địa chỉ trong DATABASE_URL — "
                            "bật DB (vd. docker compose up -d postgres) và map cổng 5432."
                        )
                    result["notes"].append(
                        f"topcv (ghi DB): đã parse {len(jobs)} tin nhưng upsert thất bại: {e!s}.{db_hint}"
                    )
                finally:
                    if created_pool is not None:
                        await created_pool.close()
        else:
            result["notes"].append("topcv: tắt (CRAWL_TOPCV_ENABLED=false)")

        note_it = await probe_itviec(client)
        result["notes"].append(f"itviec: {note_it}")
        result["notes"].append(
            "linkedin: không crawl — dùng LinkedIn Jobs API (đối tác) hoặc xuất thủ công hợp lệ."
        )
    return result


async def main_async() -> None:
    logging.basicConfig(level=logging.INFO)
    out = await sync_jobs_from_web()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    print(out)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
