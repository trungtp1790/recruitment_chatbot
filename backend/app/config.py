from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_file_paths() -> tuple[str, ...] | None:
    """Ưu tiên .env ở root repo (chạy từ thư mục backend vẫn đọc được), sau đó .env ở cwd nếu khác."""
    paths: list[Path] = []
    repo_env = _REPO_ROOT / ".env"
    if repo_env.is_file():
        paths.append(repo_env)
    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file() and cwd_env.resolve() != repo_env.resolve():
        paths.append(cwd_env)
    return tuple(str(p) for p in paths) if paths else None


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    allowed_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://chatbot:chatbot_pass@postgres:5432/recruitment_db"
    redis_url: str = "redis://redis:6379/0"

    use_mock_llm: bool = True
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    # Chiến lược xử lý câu ngoài phạm vi tuyển dụng:
    # - "guardrail": rào lại về domain tuyển dụng (Option A)
    # - "open": vẫn trả lời bình thường theo nội dung câu hỏi (Option B)
    out_of_scope_mode: str = "guardrail"

    # Đồng bộ job từ web (TopCV có SSR; ITviec/LinkedIn xem job_ingest + README)
    sync_jobs_secret: str | None = None
    crawl_topcv_enabled: bool = True
    crawl_topcv_max_jobs: int = 40
    topcv_jobs_list_url: str = "https://www.topcv.vn/tim-viec-lam-moi-nhat"
    crawl_user_agent: str = ""

    model_config = SettingsConfigDict(
        env_file=_env_file_paths(),
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
