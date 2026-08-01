from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    ollama_temperature: float = 0.2
    ollama_num_predict: int = 800
    # Only relevant for reasoning/hybrid-thinking models (e.g. qwen3) — plain
    # instruct models like the default reject the "think" field outright
    # (Ollama returns 400 "does not support thinking"), so this must stay
    # False unless you actually switch to a reasoning model. If you do:
    # explicitly disabling thinking on such models to save time was observed
    # to make them rush and produce incorrect/unsafe allergy assessments
    # (reasoning leaking into the JSON string fields instead of being
    # cleanly suppressed) — set this True and raise OLLAMA_NUM_PREDICT
    # instead (correct but slow, ~30-60s/request).
    ollama_think: bool = False
    ollama_keep_alive: str = "30m"
    ollama_request_timeout: float = 60.0

    chroma_persist_dir: str = "./data/chroma"
    documents_registry_path: str = "./data/documents.json"

    chunk_size: int = 800
    chunk_overlap: int = 120
    default_top_k: int = 5

    cache_ttl_seconds: int = 300
    cache_max_size: int = 512

    max_upload_bytes: int = 20 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
