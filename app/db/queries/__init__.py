"""Package chứa các module truy vấn SQL thuần (Raw SQL) sử dụng asyncpg."""
from app.db.queries.contact_queries import (
     find_contact,
     list_contacts,
     get_contact_by_id,
     create_contact,
     soft_delete_contact,
)
from app.db.queries.workflow_queries import (
     create_run,
     update_run_status,
     sync_run_state,
     get_run_by_session_id,
     list_runs_by_user,
)
from app.db.queries.action_queries import (
     batch_insert_action_items,
     update_action_status,
     list_action_items_by_user,
     get_action_item_by_id,
)
from app.db.queries.file_queries import (
     create_input_file,
     batch_create_input_files,
     list_files_by_run,
     get_file_by_id,
)
from app.db.queries.approval_queries import (
     create_approval_request,
     create_approval_for_step,
     decide_approval,
     list_pending_approvals,
     get_approval_by_id,
)

__all__ = [
     # Contact
     "find_contact",
     "list_contacts",
     "get_contact_by_id",
     "create_contact",
     "soft_delete_contact",
     # Workflow
     "create_run",
     "update_run_status",
     "sync_run_state",
     "get_run_by_session_id",
     "list_runs_by_user",
     # Action Items
     "batch_insert_action_items",
     "update_action_status",
     "list_action_items_by_user",
     "get_action_item_by_id",
     # Input Files
     "create_input_file",
     "batch_create_input_files",
     "list_files_by_run",
     "get_file_by_id",
     # Approval Requests
     "create_approval_request",
     "create_approval_for_step",
     "decide_approval",
     "list_pending_approvals",
     "get_approval_by_id",
]
