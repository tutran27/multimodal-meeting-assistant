from functools import lru_cache

from app.orchestration.workflow import Workflow
from app.services.storage_service import StorageService


@lru_cache
def get_workflow() -> Workflow:
    return Workflow()


@lru_cache
def get_storage_service() -> StorageService:
    return StorageService()


if __name__ == "__main__":
    print(type(get_workflow()).__name__)
    print(type(get_storage_service()).__name__)