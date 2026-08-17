from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_storage_service, get_workflow
from app.orchestration.workflow import Workflow
from app.services.storage_service import StorageService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/run")
async def run_workflow(
    instruction: str = Form(...),
    script_text: str | None = Form(None),
    audio_file: UploadFile | None = File(None),
    image_file: UploadFile | None = File(None),
    script_file: UploadFile | None = File(None),
    workflow: Workflow = Depends(get_workflow),
    storage: StorageService = Depends(get_storage_service),
) -> dict:
    saved_paths: dict[str, Path | None] = {"audio": None, "image": None, "script": None}

    if audio_file:
        saved_paths["audio"] = storage.save_upload(audio_file, "audio")
    if image_file:
        saved_paths["image"] = storage.save_upload(image_file, "image")
    if script_file:
        saved_paths["script"] = storage.save_upload(script_file, "script")

    state = await workflow.run(
        user_request=instruction,
        audio_path=str(saved_paths["audio"]) if saved_paths["audio"] else None,
        image_path=str(saved_paths["image"]) if saved_paths["image"] else None,
        script_path=str(saved_paths["script"]) if saved_paths["script"] else None,
        script_text=script_text,
    )

    return state.model_dump(mode="json")


@router.get("/health")
async def workflow_health() -> dict:
    return {"status": "ok", "component": "workflow"}


if __name__ == "__main__":
    print("Routes:", [route.path for route in router.routes])