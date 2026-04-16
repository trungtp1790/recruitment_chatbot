import asyncpg

from .schemas import JobItem, MemorySlot
from .text_utils import strip_find_job_prefix


async def search_jobs(pool: asyncpg.Pool, query: str, slot: MemorySlot, limit: int = 10) -> list[JobItem]:
    sql = """
        SELECT id, title, company, location, salary_min, salary_max, apply_url
        FROM jobs
        WHERE is_active = TRUE
          AND ($2::text[] IS NULL OR location = ANY($2))
          AND ($3::bigint IS NULL OR salary_max >= $3)
          AND (
            $5::text[] IS NULL
            OR EXISTS (
              SELECT 1
              FROM unnest($5::text[]) AS kw(phrase)
              WHERE jobs.industry ILIKE '%' || kw.phrase || '%'
                 OR jobs.title ILIKE '%' || kw.phrase || '%'
                 OR COALESCE(jobs.description, '') ILIKE '%' || kw.phrase || '%'
            )
          )
          AND (
            $1::text = ''
            OR title ILIKE ('%' || $1 || '%')
            OR industry ILIKE ('%' || $1 || '%')
            OR $5::text[] IS NOT NULL
          )
        ORDER BY posted_at DESC NULLS LAST, created_at DESC
        LIMIT $4
    """

    locations = slot.locations if slot.locations else None
    industries = slot.industries if slot.industries else None
    q = strip_find_job_prefix(query).strip() or query.strip()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, q, locations, slot.salary_min, limit, industries)

    return [
        JobItem(
            id=row["id"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            salary_min=row["salary_min"],
            salary_max=row["salary_max"],
            apply_url=row["apply_url"],
        )
        for row in rows
    ]
