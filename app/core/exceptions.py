class AppError(Exception):
    """Base exception for this project."""

class ConfigurationError(AppError): 
    pass

class ToolExecutionError(AppError): 
    pass

class PlanValidationError(AppError): 
    pass

class ApprovalRequiredError(AppError): 
    pass

if __name__ == "__main__":
    try:
        raise ToolExecutionError("Demo error")
    except AppError as exc:
        print(type(exc).__name__, str(exc))