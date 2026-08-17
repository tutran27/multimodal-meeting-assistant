from enum import StrEnum

class SourceType(StrEnum):
    AUDIO = "audio"
    IMAGE = "image"
    MEETING_SCRIPT = "meeting_script"
    CALENDAR = "calendar"
    WEB = "web"
    INTERNAL = "internal"

class ScriptType(StrEnum):
    ACTUAL_TRANSCRIPT = "actual_transcript"
    MEETING_MINUTES = "meeting_minutes"
    PREPARED_AGENDA = "prepared_agenda"
    UNKNOWN = "unknown"

class WorkflowStatus(StrEnum):
    CREATED = "created"
    EXTRACTING = "extracting"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"

class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class RiskLevel(StrEnum):
    READ = "read"
    REVERSIBLE_WRITE = "reversible_write"
    EXTERNAL_WRITE = "external_write"

class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    CONFLICTED = "conflicted"

ALLOWED_PLAN_TOOLS = {
    "calendar_freebusy", 
    "calendar_create_event", 
    "web_search", 
    "pdf_generator", 
    "email_create_draft"
    }

EVIDENCE_PREFIXES = {
    SourceType.AUDIO: "AUDIO",
    SourceType.IMAGE: "IMAGE",
    SourceType.MEETING_SCRIPT: "SCRIPT",
    SourceType.CALENDAR: "CALENDAR",
    SourceType.WEB: "WEB",
    SourceType.INTERNAL: "INTERNAL",
}

if __name__ == "__main__":
    print("Allowed tools:", sorted(ALLOWED_PLAN_TOOLS))
    print("Script type:", ScriptType.PREPARED_AGENDA)