# Crawler (Scrapy — tham khảo)

Thư mục này giữ **spider mẫu** (`itviec`, `topcv`, `linkedin`) cho hướng học Scrapy.

**Luồng ingest vào Postgres dùng trong project:** `backend/app/job_ingest.py` + `job_parse.py` (httpx + BeautifulSoup, upsert qua asyncpg). Chạy:

```bash
cd backend
python -m app.job_ingest
```

hoặc `POST /api/admin/jobs/sync` — xem README gốc repo.

## Chạy spider xuất JSON (không ghi DB)

```bash
cd backend
scrapy runspider crawler/spiders/topcv.py -s FEEDS='output/topcv.json'
scrapy runspider crawler/spiders/itviec.py -s FEEDS='output/itviec.json'
scrapy runspider crawler/spiders/linkedin.py -s FEEDS='output/linkedin.json'
```

## Lưu ý

- Selector trong spider có thể lỗi thời so với HTML thật; parser TopCV trong `job_parse.py` được căn theo trang SSR hiện tại.
- Luôn tuân thủ **robots.txt**, điều khoản site và pháp luật. ITviec thường yêu cầu vượt Cloudflare; LinkedIn hạn chế crawl công khai.
