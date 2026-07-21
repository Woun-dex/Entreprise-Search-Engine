from typing import Any
from pydantic import BaseModel, Field

class DeadLetterPayload(BaseModel):
    original_topic: str | None = Field(default=None, description="The topic the original message was consumed from, if known.")
    original_message: Any = Field(description="The original unparsed message or partially parsed payload.")
    error_reason: str = Field(description="The exception string or reason why processing failed.")
    worker_name: str = Field(description="The name of the worker that failed to process the message.")
