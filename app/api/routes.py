from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_storage_service, get_workflow
from app.orchestration.workflow import Workflow
from app.services.storage_service import StorageService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/run")
async def run_workflow(
    instruction: str = Form(...),
    script_text: str | None = Form(default=None),
    audio_file: UploadFile = File(default=None),
    image_file: UploadFile = File(default=None),
    script_file: UploadFile = File(default=None),
    workflow: Workflow = Depends(get_workflow),
    storage: StorageService = Depends(get_storage_service),
) -> dict:
    saved_paths: dict[str, Path | None] = {"audio": None, "image": None, "script": None}

    if audio_file and audio_file.filename and audio_file.filename.strip():
        saved_paths["audio"] = storage.save_upload(audio_file, "audio")
    if image_file and image_file.filename and image_file.filename.strip():
        saved_paths["image"] = storage.save_upload(image_file, "image")
    if script_file and script_file.filename and script_file.filename.strip():
        saved_paths["script"] = storage.save_upload(script_file, "script")

    # Bỏ qua script_text nếu là placeholder mặc định "string" từ Swagger UI
    clean_script_text = script_text.strip() if script_text else None
    if clean_script_text == "string":
        clean_script_text = None

    state = await workflow.run(
        user_request=instruction,
        audio_path=str(saved_paths["audio"]) if saved_paths["audio"] else None,
        image_path=str(saved_paths["image"]) if saved_paths["image"] else None,
        script_path=str(saved_paths["script"]) if saved_paths["script"] else None,
        script_text=clean_script_text,
    )

    return state.model_dump(mode="json")


@router.get("/health")
async def workflow_health() -> dict:
    return {"status": "ok", "component": "workflow"}


if __name__ == "__main__":
    print("Routes:", [route.path for route in router.routes])