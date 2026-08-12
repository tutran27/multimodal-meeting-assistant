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
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    timezone: str = "Asia/Ho_Chi_Minh"

    # Storage (Đường dẫn trực tiếp)
    upload_dir: Path = Path("data/inputs")
    output_dir: Path = Path("outputs")
    temp_dir: Path = Path("data/temp")
    contacts_file: Path = Path("data/contacts.json")
    max_upload_size_mb: int = 100
    allowed_audio_extensions: list[str] = Field(default_factory=lambda: [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"])
    allowed_image_extensions: list[str] = Field(default_factory=lambda: [".jpg", ".jpeg", ".png", ".webp"])
    allowed_script_extensions: list[str] = Field(default_factory=lambda: [".txt", ".md", ".docx", ".pdf"])
    
    # Database
    database_url: str = "sqlite:///./data/app.db"
    
    # Groq LLM and STT
    groq_api_key: str | None = None
    groq_llm_model: str = "openai/gpt-oss-20b"
    groq_stt_model: str = "whisper-large-v3-turbo"
    
    # OpenRouter LLM
    openrouter_api_key: str | None = None
    openrouter_llm_model: str = "qwen/qwen-2.5-72b-instruct"
    
    llm_temperature: float = 0.0
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
    search_provider: Literal["duckduckgo", "tavily"] = "tavily"
    search_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    search_max_results: int = 5
    
    # Google
    google_enabled: bool = False
    google_client_secret_file: Path = Path("credentials/client_secret.json")
    google_token_file: Path = Path("credentials/token.json")
    google_calendar_id: str = "primary"
    default_boss_email: str | None = None
    
    # PDF
    report_font_path: Path | None = None
    pdf_default_title: str = "Meeting Report"
    
    # Agent workflow
    max_plan_steps: int = 8
    max_tool_retries: int = 2
    max_reflection_rounds: int = 2
    max_replan_rounds: int = 1
    enable_parallel_execution: bool = True

    # Safety
    require_approval_for_calendar_write: bool = True
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
