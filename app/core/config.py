import os
from functools import lru_cache
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import torch 

# Load environment variables from .env file into os.environ
load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Multi-modal Smart Personal Assistant"
    app_env: Literal["development", "testing", "production"] = (
        os.getenv("APP_ENV") or os.getenv("ENV") or "development"  # type: ignore[assignment]
    )
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    timezone: str = "Asia/Ho_Chi_Minh"

    # Storage (Đường dẫn trực tiếp)
    upload_dir: Path = Path("data/inputs")
    output_dir: Path = Path("outputs")
    temp_dir: Path = Path("data/temp")
    max_upload_size_mb: int = 100
    allowed_audio_extensions: list[str] = [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"]
    allowed_image_extensions: list[str] = [".jpg", ".jpeg", ".png", ".webp"]
    allowed_script_extensions: list[str] = [".txt", ".md", ".docx", ".pdf"]
    
    # Database (PostgreSQL / Supabase asyncpg)
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/postgres",
        validation_alias="DATABASE_URL",
    )
    db_pool_min_size: int = Field(default=2, validation_alias="DB_POOL_MIN_SIZE")
    db_pool_max_size: int = Field(default=10, validation_alias="DB_POOL_MAX_SIZE")
    db_pool_timeout: int = Field(default=30, validation_alias="DB_POOL_TIMEOUT")

    # Supabase (Auth & Storage)
    supabase_url: str | None = Field(default=None, validation_alias="SUPABASE_URL")
    supabase_anon_key: str | None = Field(default=None, validation_alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str | None = Field(default=None, validation_alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: str | None = Field(default=None, validation_alias="SUPABASE_JWT_SECRET")
    supabase_storage_bucket_inputs: str = Field(
        default="meeting-inputs", validation_alias="SUPABASE_STORAGE_BUCKET_INPUTS"
    )
    supabase_storage_bucket_reports: str = Field(
        default="meeting-reports", validation_alias="SUPABASE_STORAGE_BUCKET_REPORTS"
    )
    
    # Groq LLM and STT
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_llm_model: str = os.getenv("GROQ_LLM_MODEL", "gpt-oss-20b")
    groq_stt_model: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
    
    # OpenRouter LLM
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_llm_model: str = os.getenv("OPENROUTER_LLM_MODEL", "qwen/qwen-2.5-72b-instruct")
    
    # Hugging Face
    hf_token: str | None = os.getenv("HF_TOKEN")
    
    llm_temperature: float = 0.0
    llm_max_tokens: int | None = 8192
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2
    stt_language: str = "vi"
    
    # PaddleOCR
    ocr_language: str = "vi"
    ocr_device: str = "gpu" if torch.cuda.is_available() else "cpu"
    ocr_rec_model_repo: str = "tieubaoca/pp-ocrv6-medium-rec-vietnamese"
    ocr_use_doc_orientation_classify: bool = True
    ocr_use_doc_unwarping: bool = True
    ocr_use_textline_orientation: bool = True
    ocr_version: str = "PP-OCRv3"
    
    # Web Search
    search_provider: Literal["duckduckgo", "tavily"] = (
        os.getenv("SEARCH_PROVIDER", "tavily")  # type: ignore[assignment]
    )
    search_api_key: str | None = os.getenv("TAVILY_API_KEY")
    search_max_results: int = 5
    
    # Google
    google_enabled: bool = os.getenv("GOOGLE_ENABLED", "true").lower() == "true"
    google_client_secret_file: Path = Path(os.getenv("GOOGLE_CLIENT_SECRET_PATH", "credentials/credentials.json"))
    google_token_file: Path = Path(os.getenv("GOOGLE_TOKEN_PATH", "credentials/token_calendar.json"))
    google_calendar_id: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    default_boss_email: str = os.getenv("DEFAULT_BOSS_EMAIL", "boss@example.com")
    
    # PDF 
    report_font_path: Path | None = Path("assets/fonts/DejaVuSans.ttf")
    pdf_default_title: str = "Meeting Report"
    
    # Agent workflow
    max_plan_steps: int = 8
    max_tool_retries: int = 2
    max_reflection_rounds: int = 2
    max_replan_rounds: int = 1
    enable_parallel_execution: bool = True

    # Safety
    require_approval_for_calendar_write: bool = False
    enable_email_send: bool = False

    # Testing
    mock_mode: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_dir: Path = Path("logs")
    
    # LangSmith
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "smart-personal-assistant"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def create_directories(self) -> None:
        for directory in [self.upload_dir, self.output_dir, self.temp_dir, self.log_dir]:
            directory.mkdir(parents=True, exist_ok=True)

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.create_directories()
    return settings

settings = get_settings()

if __name__ == "__main__":
    print("App:", settings.app_name)
    print("Output dir:", settings.output_dir)
    print("Upload dir:", settings.upload_dir)
    print("Temp dir:", settings.temp_dir)
    print("Log dir:", settings.log_dir)
