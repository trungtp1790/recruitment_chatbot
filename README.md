# Recruitment Chatbot (Vietnamese)

Chatbot hỗ trợ tuyển dụng bằng tiếng Việt.

MVP hiện tại tập trung vào luồng thực thi được cho Fresher AI Engineer:
`Next.js UI -> FastAPI -> Intent + Session Memory (Redis) -> Job Search (PostgreSQL) -> Gemini reply`.

Repo này ưu tiên tính trung thực khi demo xin việc: phần nào đã chạy được thì mô tả rõ, phần nào chưa có thì ghi thành roadmap.

## Demo nhanh

- Frontend: [http://localhost:3000](http://localhost:3000)
- Swagger API: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: `GET /health`

## Bài toán giải quyết

- User chat tự nhiên để tìm việc theo ngành, địa điểm, mức lương.
- Bot nhận diện intent cơ bản và lưu ngữ cảnh theo `session_id` (long-term memory theo phiên).
- LLM chỉ dùng để diễn đạt câu trả lời; logic lọc job vẫn chạy bằng SQL để dễ kiểm soát.

## Hành vi hội thoại theo mô tả dự án

### 1) Chat mở đầu

- Hiện tại UI chưa tự đẩy greeting message từ bot.
- Người dùng có thể bắt đầu bằng các câu như:
  - `"Tôi có thể giúp được gì cho bạn?"`
  - `"Chúng ta nên bắt đầu từ đâu?"`
  - `"Tôi muốn tìm việc"`

### 2) Chat bình thường (ngoài tuyển dụng)

MVP đang dùng **Option A**:
- Nếu user hỏi ngoài phạm vi (thời tiết, bóng đá, âm nhạc...), bot rào lại:
  - `"Mình là chatbot tuyển dụng, nên chỉ hỗ trợ tìm việc..."`

**Option B** (trả lời bình thường ngoài tuyển dụng) chưa bật trong code hiện tại, để ở roadmap.

### 3) Chat tuyển dụng

- User hỏi job DS/AI -> bot tìm job liên quan DS/AI.
- User nói tiếp `"ở HCM"` -> bot vẫn hiểu đang theo ngữ cảnh job DS/AI trước đó (memory theo phiên Redis).
- User hỏi `"Bạn là ai?"` -> bot trả lời dạng giới thiệu chatbot tuyển dụng.

## Tech stack

- **Backend:** FastAPI, asyncpg, Redis, httpx, BeautifulSoup, Gemini API
- **Frontend:** Next.js App Router
- **Data:** PostgreSQL (`jobs` table, có cột `embedding` để mở rộng vector search)
- **Infra local:** Docker Compose

## Kiến trúc

```text
Browser (Next.js)
   -> POST /api/chat (FastAPI)
      -> intent + slot memory (Redis)
      -> query jobs (PostgreSQL)
      -> generate response (Gemini / mock fallback)
```

## Project structure

```text
recruitment_chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── intent.py
│   │   ├── memory_service.py
│   │   ├── job_service.py
│   │   ├── llm_service.py
│   │   ├── job_ingest.py
│   │   └── ...
│   ├── tests/
│   └── requirements.txt
├── frontend/app/
├── infra/postgres/init.sql
├── docker-compose.yml
├── .env.example
└── README.md
```

## Run with Docker (recommended)

```bash
copy .env.example .env
docker compose up --build
```

Trong `.env`:
- điền `GEMINI_API_KEY` để dùng model thật, hoặc
- đặt `USE_MOCK_LLM=true` để demo offline.

Nếu dữ liệu Postgres cũ làm sai seed:

```bash
docker compose down -v
docker compose up --build
```

## Local development (không dùng Docker)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Mở terminal khác:

```bash
cd frontend
npm install
npm run dev
```

## Đồng bộ job từ web

Nguồn đang hỗ trợ ổn định trong repo: **TopCV**.

```bash
cd backend
python -m app.job_ingest
```

Hoặc dùng API admin:

```http
POST /api/admin/jobs/sync
X-Sync-Secret: <SYNC_JOBS_SECRET>
```

Ghi chú thực tế:
- ITviec/LinkedIn chưa bật ingest tự động trong bản này (Cloudflare/ToS/API constraints).
- TopCV có thể trả `HTTP 520` tùy IP/rate-limit; đã có retry và browser-like headers nhưng vẫn có thể fail.

## API chính (MVP)

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Kiểm tra trạng thái API, Postgres, Redis |
| `POST` | `/api/chat` | Chat và trả jobs gợi ý |
| `GET` | `/api/jobs/search` | Search trực tiếp theo query |
| `POST` | `/api/admin/jobs/sync` | Ingest jobs vào DB |

## Quick test flow (để demo recruiter)

1. Gửi: `Tôi muốn tìm việc DS/AI`
2. Gửi tiếp: `Ở HCM`
3. Gửi tiếp: `Lương từ 20 triệu`
4. Gửi: `Bạn là ai?`
5. Gửi câu ngoài phạm vi: `Thời tiết hôm nay thế nào?`
6. Kiểm tra `GET /health` trong Swagger

Kỳ vọng:
- intent chuyển đúng giữa `find_job`, `bot_identity`, `off_topic`
- memory giữ được context ngành + địa điểm + lương theo phiên chat
- câu ngoài phạm vi không làm bẩn slot tìm việc
- trả lời dùng Gemini khi có key, fallback mock khi không có key

## Hạn chế hiện tại

- Intent hiện là rule-based, chưa có confidence scoring.
- UI chưa có greeting bot tự động khi mở màn hình chat.
- Chưa có mode cấu hình để chọn giữa:
  - Option A: rào lại domain tuyển dụng (đang có)
  - Option B: vẫn trả lời bình thường ngoài domain (chưa có)
- Chưa có auth, rate limit, tracing, và dashboard monitoring.
- Chưa có CI/CD pipeline hoàn chỉnh.
- Search hiện là SQL + keyword + slot memory; chưa bật RAG vector retrieval thực sự.
- Chưa dùng LangGraph/graph orchestration để xử lý timeout hoặc branching flow.

## Roadmap ngắn hạn

- [ ] Thêm greeting mặc định khi mở chat: `"Tôi có thể giúp được gì cho bạn?"`
- [ ] Thêm config `OUT_OF_SCOPE_MODE` để chọn Option A/Option B cho câu hỏi ngoài tuyển dụng
- [ ] Bổ sung eval dataset cho tiếng Việt (intent + retrieval quality)
- [ ] Thêm observability (structured logs + request id + latency metrics)
- [ ] Bật RAG vector search bằng pgvector (đã có cột `embedding` trong schema)
- [ ] Nếu response retrieval chậm: thêm timeout + fallback flow (có thể triển khai bằng graph orchestration)
- [ ] Hoàn thiện CI (lint, test, build) trước khi public production demo

## Những gì mình học được từ project này

- Không nên để LLM quyết định toàn bộ business logic; nên tách phần filter/search thành deterministic layer.
- Session memory theo phiên giúp bot hiểu câu follow-up kiểu `"ở HCM"` hoặc `"lương từ 20 triệu"`.
- Data ingestion thực tế bị ảnh hưởng lớn bởi nguồn dữ liệu và anti-bot, không chỉ là code.

## Environment variables

Xem `.env.example` để biết các biến chính:
`DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`, `USE_MOCK_LLM`, `ALLOWED_ORIGINS`, `SYNC_JOBS_SECRET`, `CRAWL_TOPCV_*`, `TOPCV_JOBS_LIST_URL`.

## License

MIT
