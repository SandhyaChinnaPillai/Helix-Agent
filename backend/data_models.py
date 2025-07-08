from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageType(Enum):
    INITIAL_OUTREACH = "initial_outreach"
    FOLLOW_UP = "follow_up"
    MEETING_REQUEST = "meeting_request"
    THANK_YOU = "thank_you"
    REJECTION_HANDLING = "rejection_handling"
    VALUE_ADD = "value_add"
    FINAL_FOLLOW_UP = "final_follow_up"
    OFFER = "offer"


class EditType(Enum):
    ADD = "Add"
    EDIT = "Edit"


@dataclass
class OutreachMessage:
    id: str
    type: str
    subject: str
    content: str
    timing: str  # e.g., "immediately", "3 days after", "1 week after"
    order: int


@dataclass
class UserInfo:
    id: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    industry: Optional[str] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None
    additional_context: Optional[str] = None


@dataclass
class ConversationState:
    session_id: str
    user_info: UserInfo
    message_sequence: List[OutreachMessage]
    conversation_history: List[Dict[str, Any]]
    current_phase: str  # "gathering_info", "generating_sequence", "editing_sequence", "approve_sequence", "finalizing_sequence"


class LLMOutReachMessage(BaseModel):
    type: MessageType
    subject: str = Field(description="Subject line of the message")
    content: str = Field(description="Content of the message")
    timing: str = Field(
        description="Timing of the message in relation to the outreach sequence e.g., immediately, 3 days after, 1 week after"
    )


class LLMOutReachMessages(BaseModel):
    messages: List[LLMOutReachMessage]


USER_FRIENDLY_TOOL_CALL = {
    "generate_sequence": "Generating a message sequence .....",
    "edit_sequence": "Editing sequence messages .....",
    "add_to_sequence": "Editing sequence messages .....",
    "delete_sequence": "Editing sequence messages .....",
    "finalize_sequence": "Finalizing the outreach sequence .....",
}
