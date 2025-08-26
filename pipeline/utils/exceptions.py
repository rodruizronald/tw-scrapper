class PipelineError(Exception):
    """Base exception for all pipeline operations."""

    def __init__(self, message: str, company_name: str | None = None):
        self.company_name = company_name
        super().__init__(message)


class CompanyProcessingError(PipelineError):
    """Error processing a specific company."""

    def __init__(
        self, company_name: str, original_error: Exception, stage: str = "unknown"
    ):
        self.original_error = original_error
        self.stage = stage
        message = f"Failed to process company '{company_name}' in stage '{stage}': {original_error}"
        super().__init__(message, company_name)


class ConfigurationError(PipelineError):
    """Error in pipeline configuration."""

    def __init__(self, message: str, config_field: str | None = None):
        self.config_field = config_field
        if config_field:
            message = f"Configuration error in '{config_field}': {message}"
        super().__init__(message)


class HTMLExtractionError(PipelineError):
    """Error extracting HTML content from a webpage."""

    def __init__(self, url: str, message: str, company_name: str | None = None):
        self.url = url
        full_message = f"Failed to extract HTML from '{url}': {message}"
        super().__init__(full_message, company_name)


class OpenAIProcessingError(PipelineError):
    """Error processing content with OpenAI API."""

    def __init__(
        self,
        message: str,
        company_name: str | None = None,
        response_text: str | None = None,
    ):
        self.response_text = response_text
        super().__init__(f"OpenAI processing failed: {message}", company_name)


class FileOperationError(PipelineError):
    """Error performing file operations."""

    def __init__(
        self,
        operation: str,
        file_path: str,
        message: str,
        company_name: str | None = None,
    ):
        self.operation = operation
        self.file_path = file_path
        full_message = (
            f"File operation '{operation}' failed for '{file_path}': {message}"
        )
        super().__init__(full_message, company_name)


class ValidationError(PipelineError):
    """Error validating data or configuration."""

    def __init__(self, field: str, value: str, message: str):
        self.field = field
        self.value = value
        full_message = (
            f"Validation failed for field '{field}' with value '{value}': {message}"
        )
        super().__init__(full_message)
