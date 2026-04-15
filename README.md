# Recruitment Chatbot

Chatbot hỗ trợ tuyển dụng bằng tiếng Việt, xây dựng theo hướng MVP để demo end-to-end cho portfolio.

## Overview

Ứng dụng cho phép người dùng trò chuyện để tìm việc theo ngành, địa điểm và mức lương.  
Hệ thống dùng intent rule-based + session memory (Redis) để giữ ngữ cảnh hội thoại, sau đó truy vấn job từ PostgreSQL và tạo phản hồi bằng Gemini (hoặc mock fallback).

Luồng chính:

```text
Next.js UI -> FastAPI -> Intent + Memory (Redis) -> Job Search (PostgreSQL) -> Gemini Response
```

## Features

- Chat tìm việc theo ngôn ngữ tự nhiên tiếng Việt
- Greeting tự động khi mở chat: "Tôi có thể giúp được gì cho bạn? Chúng ta nên bắt đầu từ đâu?"
- Nhận diện intent cơ bản: `find_job`, `off_topic`, `bot_identity`
- Lưu ngữ cảnh theo phiên chat (`session_id`) gồm ngành, địa điểm, lương tối thiểu
- Hỗ trợ câu hỏi nối tiếp kiểu: "Tìm việc DS/AI" -> "ở HCM" -> "lương từ 20 triệu"
- Tích hợp Gemini, có fallback sang mock reply khi thiếu API key
- Cấu hình xử lý off-topic qua `OUT_OF_SCOPE_MODE`:
  - `guardrail` (Option A): rào lại domain tuyển dụng
  - `open` (Option B): vẫn trả lời bình thường câu ngoài tuyển dụng
- Đồng bộ dữ liệu job từ TopCV vào PostgreSQL

## Conversation Behavior (Current MVP)

- **Tìm việc:** bot tìm job theo intent + context trong memory
- **Ngoài phạm vi tuyển dụng:** chọn bằng `OUT_OF_SCOPE_MODE`
  - `guardrail`: rào lại theo domain tuyển dụng
  - `open`: vẫn trả lời bình thường câu ngoài tuyển dụng
- **Câu hỏi "Bạn là ai?":** bot giới thiệu là chatbot hỗ trợ tuyển dụng

## Tech Stack

- **Frontend:** Next.js (App Router)
- **Backend:** FastAPI, asyncpg, Redis, httpx, BeautifulSoup
- **LLM:** Google Gemini API (`google-generativeai`)
- **Database:** PostgreSQL + pgvector image
- **Infra local:** Docker Compose

## Project Structure

```text
recruitment_chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── intent.py
│   │   ├── memory_service.py
│   │   ├── location_slot.py
│   │   ├── job_service.py
│   │   ├── llm_service.py
│   │   └── job_ingest.py
│   ├── tests/
│   └── requirements.txt
├── frontend/app/
├── infra/postgres/init.sql
├── docker-compose.yml
├── .env.example
└── README.md
```

## Getting Started

### 1) Run with Docker (recommended)

```bash
copy .env.example .env
docker compose up --build
```

Services:
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: `GET /health`

Trong `.env`:
- điền `GEMINI_API_KEY` để dùng Gemini thật, hoặc
- đặt `USE_MOCK_LLM=true` để chạy offline.

Nếu cần reset seed data:

```bash
docker compose down -v
docker compose up --build
```

### 2) Run locally (without Docker)

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend (terminal khác):

```bash
cd frontend
npm install
npm run dev
```

## Data Sync (TopCV)

Chạy ingest script:

```bash
cd backend
python -m app.job_ingest
```

Hoặc gọi API admin:

```http
POST /api/admin/jobs/sync
X-Sync-Secret: <SYNC_JOBS_SECRET>
```

Ghi chú:
- ITviec/LinkedIn chưa bật ingest tự động trong phiên bản này.
- TopCV có thể gặp `HTTP 520` tùy IP/rate-limit.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Kiểm tra trạng thái API, Postgres, Redis |
| `POST` | `/api/chat` | Chat và trả phản hồi + danh sách job gợi ý |
| `GET` | `/api/jobs/search` | Tìm job trực tiếp theo query |
| `POST` | `/api/admin/jobs/sync` | Đồng bộ job từ web vào DB |

## Demo Script

1. `Tôi muốn tìm việc DS/AI`
2. `Ở HCM`
3. `Lương từ 20 triệu`
4. `Bạn là ai?`
5. `Thời tiết hôm nay thế nào?`

Kỳ vọng:
- Intent chuyển đúng giữa `find_job`, `bot_identity`, `off_topic`
- Memory giữ được ngữ cảnh ngành/địa điểm/lương trong cùng session
- Câu off-topic không làm bẩn memory tìm việc

## Limitations

- Intent đang là rule-based, chưa có confidence scoring
- Chưa có auth/rate-limit/observability đầy đủ
- Chưa có CI/CD pipeline hoàn chỉnh
- Chưa bật RAG vector retrieval thực tế (mới ở mức SQL + keyword + memory)
- Chưa dùng graph orchestration cho timeout/fallback

## Roadmap

- [ ] Thêm greeting mặc định khi mở chat
- [ ] Bổ sung eval dataset cho tiếng Việt (intent + retrieval)
- [ ] Bật vector search với pgvector cho query mơ hồ
- [ ] Bổ sung timeout/fallback flow cho nhánh retrieval chậm
- [ ] Hoàn thiện CI (lint, test, build)

## Environment Variables

Xem `.env.example` để cấu hình:
`DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `USE_MOCK_LLM`, `OUT_OF_SCOPE_MODE`, `ALLOWED_ORIGINS`, `SYNC_JOBS_SECRET`, `CRAWL_TOPCV_*`, `TOPCV_JOBS_LIST_URL`.

## License

MIT
