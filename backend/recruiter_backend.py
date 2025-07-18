from data_models import (
    EditType,
    LLMOutReachMessages,
    MessageType,
    USER_FRIENDLY_TOOL_CALL,
    OutreachMessage,
    UserInfo,
    ConversationState,
)
from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import uuid
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import openai
from openai import OpenAI
from dataclasses import asdict
import instructor

load_dotenv()  # Load environment variables from .env file
# import eventlet
# eventlet.monkey_patch()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

client = instructor.from_openai(
    OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )
)
openai.api_key = os.getenv("OPENAI_API_KEY")


# =============================================================================
# Socket Management
# =============================================================================

"""
    Manages WebSocket communication for real-time updates in the outreach messaging system.
    
    This class provides functionality to emit various types of messages to connected clients
    via Socket.IO, including sequence updates, chat messages, and tool call notifications.
    All emissions are sent to specific rooms based on session IDs for targeted communication.
    
    Attributes:
        socketio: The Socket.IO server instance used for WebSocket communication.
    """


class SocketManager:
    def __init__(self, socketio):
        self.socketio = socketio

    def emit_sequence_update(self, session_id: str, sequence: List[OutreachMessage]):
        """Emit sequence update to client"""
        self.socketio.emit(
            "sequence_updated",
            {"session_id": session_id, "sequence": [asdict(msg) for msg in sequence]},
            room=session_id,
        )
        self.socketio.sleep(0)  # Ensure the emit is flushed immediately

    def emit_chat_message(self, session_id: str, message: str, role: str):
        """Emit chat message to client"""
        self.socketio.emit(
            "chat_message",
            {"session_id": session_id, "message": message, "role": role},
            room=session_id,
        )
        self.socketio.sleep(0)  # Ensure the emit is flushed immediately

    def emit_tool_call(self, session_id: str, message: str):
        """Emit tool call notification to client"""
        self.socketio.emit(
            "tool_call",
            {"session_id": session_id, "message": message},
            room=session_id,
        )
        self.socketio.sleep(0)  # Ensure the emit is flushed immediately


# =============================================================================
# State Management
# =============================================================================

"""
Manages conversation sessions and their associated states in the outreach messaging system.
This class provides functionality to create, retrieve, and update session data, including 
user information and conversation history. It also handles persistence to a SQLite database.

Attributes:
    sessions (Dict[str, ConversationState]): Dictionary mapping session IDs to their 
        corresponding ConversationState objects.
"""


class StateManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationState] = {}

    def create_session(self, session_id: str) -> ConversationState:
        state = ConversationState(
            session_id=session_id,
            user_info=UserInfo(),
            message_sequence=[],
            conversation_history=[],
            current_phase="gathering_info",
        )
        self.sessions[session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[ConversationState]:
        return self.sessions.get(session_id)

    def update_session_user_info(self, session_id: str, user_info: UserInfo):
        """Updates user information in the session and save to database"""
        if session_id in self.sessions:
            state = self.sessions[session_id]
            state.user_info = user_info

            # save to db - initial save
            import sqlite3

            conn = sqlite3.connect("helix.db")
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS session (
                id TEXT PRIMARY KEY,
                session_context TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
          """
                )

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO session (id, user_id,user_name, session_context) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        user_info.id,
                        user_info.name,
                        json.dumps(asdict(state.user_info)),
                    ),
                )
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Error saving session to database: {e}")
            finally:
                conn.close()

    def add_message_to_history(
        self,
        session_id: str,
        role: str,
        content: str,
        name: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
        tool_call_id: Optional[str] = None,
    ):
        """Adds a message to the conversation history"""
        if session_id in self.sessions:
            message = {
                "role": role,
                "content": content,
            }
            if name:
                message["name"] = name
            if tool_calls:
                message["tool_calls"] = tool_calls
            if tool_call_id:
                message["tool_call_id"] = tool_call_id
            self.sessions[session_id].conversation_history.append(message)


# =============================================================================
# Tool Definitions
# =============================================================================

"""
ToolManager - Agentic Tool Schema & Execution Engine

This class implements the tool layer of HELIX's agentic architecture, providing
the AI agent with a comprehensive set of tools for recruitment workflow management.
Unlike framework-based solutions, this implements custom tool definitions and
execution patterns tailored specifically for recruitment use cases.

Key Agentic Tool Principles:
- Declarative tool schemas that guide LLM decision-making
- Context-aware parameter validation and execution
- Real-time feedback during tool execution
- Stateful tool operations that maintain workflow continuity
- Error handling with graceful degradation

Tool Architecture Pattern:
Schema Definition → Agent Decision → Parameter Validation → Execution → State Update → Feedback
"""


class ToolManager:
    """
    Custom tool management system for agentic recruitment workflows.

    This manager provides the AI agent with a comprehensive toolkit for recruitment
    sequence management, implementing custom tool schemas and execution logic
    without relying on existing agentic frameworks.

    The tool system enables the agent to:
    - Generate personalized outreach sequences
    - Edit existing messages based on natural language instructions
    - Add new messages to sequences intelligently
    - Delete specific messages with proper reordering
    - Finalize sequences with database persistence

    Each tool is designed to work autonomously while maintaining conversation
    context and providing real-time feedback to users.

    Attributes:
        state_manager: Manages session state and conversation persistence
        socket_manager: Provides real-time communication during tool execution
    """

    def __init__(self, state_manager: StateManager, socket_manager: SocketManager):
        self.state_manager = state_manager
        self.socket_manager = socket_manager

    def get_tools_schema(self) -> List[Dict]:
        """
        Returns comprehensive tool schema for LLM decision-making.

        This method defines the complete toolkit available to the AI agent.
        Each tool schema includes:
        - Clear descriptions for autonomous tool selection
        - Parameter definitions with validation rules
        - Required vs optional parameters for flexible execution
        - Context-aware parameter descriptions

        The schema design enables the LLM to make intelligent decisions about
        which tools to use and how to parameterize them based on user intent.

        Returns:
            List[Dict]: OpenAI-compatible tool schema definitions

        Tool Categories:
            - Content Generation: generate_sequence
            - Content Modification: edit_sequence, add_to_sequence
            - Content Management: delete_sequence
            - Workflow Control: finalize_sequence
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_sequence",
                    "description": "Generate a sequence of outreach messages based on user information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company": {
                                "type": "string",
                                "description": "Target company name",
                            },
                            "role": {
                                "type": "string",
                                "description": "Target role/position",
                            },
                            "industry": {
                                "type": "string",
                                "description": "Industry context",
                            },
                            "experience_level": {
                                "type": "string",
                                "description": "Required experience level",
                            },
                            "additional_context": {
                                "type": "string",
                                "description": "Any additional context for personalization",
                            },
                        },
                        "required": ["company", "role"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_sequence",
                    "description": "Edit messages in the outreach sequence based on user instructions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message_identifier": {
                                "type": "string",
                                "description": "Description of the messages to edit",
                            },
                            "edit_instruction": {
                                "type": "string",
                                "description": "Natural language instructions for the edit",
                            },
                            "company": {
                                "type": "string",
                                "description": "Target company name",
                            },
                            "role": {
                                "type": "string",
                                "description": "Target role/position",
                            },
                            "industry": {
                                "type": "string",
                                "description": "Industry context",
                            },
                            "experience_level": {
                                "type": "string",
                                "description": "Required experience level",
                            },
                            "additional_context": {
                                "type": "string",
                                "description": "Any additional context for personalization",
                            },
                        },
                        "required": ["edit_instruction"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "add_to_sequence",
                    "description": "Add messages in the outreach sequence based on user instructions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "add_instruction": {
                                "type": "string",
                                "description": "Natural language instructions for adding a new message to the sequence",
                            },
                            "company": {
                                "type": "string",
                                "description": "Target company name",
                            },
                            "role": {
                                "type": "string",
                                "description": "Target role/position",
                            },
                            "industry": {
                                "type": "string",
                                "description": "Industry context",
                            },
                            "experience_level": {
                                "type": "string",
                                "description": "Required experience level",
                            },
                            "additional_context": {
                                "type": "string",
                                "description": "Any additional context for personalization",
                            },
                        },
                        "required": ["add_instruction"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_sequence",
                    "description": "Delete a specific message from the sequence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message_id": {
                                "type": "string",
                                "description": "Identifier for the message to be deleted",
                            },
                            "message_order": {
                                "type": "integer",
                                "description": "Order of the message in the sequence to be deleted",
                            },
                        },
                        "required": ["message_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "finalize_sequence",
                    "description": "Finalize and save the outreach sequence to the database after confirming users approval.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

    def execute_tool(self, session_id: str, tool_name: str, parameters: Dict) -> Dict:
        """Execute a tool and return the result"""
        session = self.state_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        try:
            if tool_name == "generate_sequence":
                return self._generate_sequence(session, parameters)
            elif tool_name == "edit_sequence":
                return self._edit_sequence(session, "Edit", parameters)
            elif tool_name == "add_to_sequence":
                return self._edit_sequence(session, "Add", parameters)
            elif tool_name == "delete_sequence":
                return self._delete_sequence(session, parameters)
            elif tool_name == "finalize_sequence":
                return self._finalize_sequence(session)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {"error": str(e)}

    def _generate_sequence(self, session: ConversationState, parameters: Dict) -> Dict:
        """
        Generate personalized outreach sequence using AI.

        This tool creates a complete recruitment sequence tailored to the
        specified company, role, and context. It updates session state
        with user information and generates 4-5 progressive messages.

        Generation Process:
        1. Update session with user information
        2. Create AI-generated message sequence
        3. Update session state and phase
        4. Emit real-time update to frontend
        5. Return sequence data

        Args:
            session: Current conversation state
            parameters: Tool parameters including company, role, context

        Returns:
            Dict: Success status and generated sequence data
        """

        # Update user info incase the edit instruction has new values for user info
        session.user_info.company = parameters.get("company")
        session.user_info.role = parameters.get("role")
        session.user_info.industry = parameters.get("industry")
        session.user_info.experience_level = parameters.get("experience_level")
        session.user_info.additional_context = parameters.get("additional_context")

        # Generate message sequence using OpenAI
        sequence = self._create_message_sequence(session.user_info)
        session.message_sequence = sequence
        session.current_phase = "generating_sequence"

        # Emit real-time update
        self.socket_manager.emit_sequence_update(session.session_id, sequence)

        return {
            "success": True,
            "message": json.dumps([asdict(msg) for msg in sequence]),
        }

    def _edit_sequence(
        self, session: ConversationState, edit_type: EditType, parameters: Dict
    ) -> Dict:
        """
        Intelligently edit or add messages to existing sequences.

        This tool handles both editing existing messages and adding new ones
        based on natural language instructions. It maintains context continuity
        and applies AI-powered content modifications.

        Edit Process:
        1. Update user info if new context provided
        2. Apply edit/add instruction using AI
        3. Update session state and phase
        4. Emit real-time update to frontend
        5. Return updated sequence

        Args:
            session: Current conversation state
            edit_type: Type of edit operation (Edit/Add)
            parameters: Tool parameters including instructions and context

        Returns:
            Dict: Success status and updated sequence data
        """
        # Update user info only if the key exists in parameters
        if "company" in parameters:
            session.user_info.company = parameters["company"]
        if "role" in parameters:
            session.user_info.role = parameters["role"]
        if "industry" in parameters:
            session.user_info.industry = parameters["industry"]
        if "experience_level" in parameters:
            session.user_info.experience_level = parameters["experience_level"]
        if "additional_context" in parameters:
            session.user_info.additional_context += parameters["additional_context"]

        # TODO : handle these errors by calling the LLM again with error message
        if edit_type == EditType.EDIT.value:
            edit_instruction = parameters.get("edit_instruction", "")
            message_identifier = parameters.get("message_identifier", "")
            if not edit_instruction:
                return {"error": "Edit instruction is required"}

            sequence = self._apply_edit_instruction(
                session, "Edit", edit_instruction, message_identifier
            )

        elif edit_type == EditType.ADD.value:
            add_instruction = parameters.get("add_instruction", "")
            if not add_instruction:
                return {"error": "Add instruction is required"}

            sequence = self._apply_edit_instruction(session, "Add", add_instruction)

        session.message_sequence = sequence
        session.current_phase = "editing_sequence"

        # Emit real-time update
        self.socket_manager.emit_sequence_update(session.session_id, sequence)

        return {
            "success": True,
            "message": json.dumps([asdict(msg) for msg in sequence]),
        }

    def _delete_sequence(
        self, session: ConversationState, parameters: Dict
    ) -> List[OutreachMessage]:
        """
        Delete specific messages from sequence with intelligent reordering.

        This tool removes messages by ID and automatically reorders the
        remaining sequence to maintain proper flow and numbering.

        Deletion Process:
        1. Identify message by ID
        2. Remove from sequence
        3. Reorder remaining messages
        4. Update session state
        5. Emit real-time update

        Args:
            session: Current conversation state
            parameters: Tool parameters including message_id

        Returns:
            Dict: Success status and updated sequence data
        """

        message_id = parameters["message_id"]
        print(f"Deleting message with ID: {message_id}")

        original_count = len(session.message_sequence)
        session.message_sequence = [
            msg for msg in session.message_sequence if msg.id != message_id
        ]

        if len(session.message_sequence) == original_count:
            return {"error": "Message not found"}

        # Reorder remaining messages
        for i, msg in enumerate(session.message_sequence):
            msg.order = i + 1

        session.current_phase = "editing_sequence"
        # Emit real-time update
        self.socket_manager.emit_sequence_update(
            session.session_id, session.message_sequence
        )

        return {
            "success": True,
            "message": json.dumps([asdict(msg) for msg in session.message_sequence]),
        }

    # TODO: check if it handles when user enters yes. and next line says but want edits
    def _finalize_sequence(self, session: ConversationState) -> Dict:
        """
        Finalize and persist approved sequences to database.

        This tool represents the final step in the recruitment workflow,
        saving the completed sequence to persistent storage for future use.

        Finalization Process:
        1. Update session phase to finalized
        2. Save session metadata to database
        3. Create outreach_message table if needed
        4. Persist all sequence messages
        5. Commit transaction with rollback on error

        Args:
            session: Current conversation state with approved sequence

        Returns:
            Dict: Success status and confirmation message
        """
        session.current_phase = "finalize_sequence"

        import sqlite3

        # Save the final sequence to the database
        conn = sqlite3.connect("helix.db")
        cursor = conn.cursor()
        try:
            print(f"Saving session {session.session_id} to database")
            print(session.user_info)
            cursor.execute(
                """
                INSERT OR REPLACE INTO session (id, user_id, user_name, session_context) 
                VALUES (?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    session.user_info.id,
                    session.user_info.name,
                    json.dumps(asdict(session.user_info)),
                ),
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS outreach_message (    
                id TEXT PRIMARY KEY,    
                session_id TEXT NOT NULL,    
                type TEXT NOT NULL,    
                subject TEXT NOT NULL,    
                content TEXT NOT NULL,    
                timing TEXT NOT NULL,   
                order_no  INTEGER NOT NULL,    
                FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE)"""
            )

            # add sequence messages to the database
            for msg in session.message_sequence:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO outreach_message (id, session_id, type, subject, content, timing, order_no) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        msg.id,
                        session.session_id,
                        msg.type,
                        msg.subject,
                        msg.content,
                        msg.timing,
                        msg.order,
                    ),
                )

            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error saving session to database: {e}")
        finally:
            conn.close()

        return {
            "success": True,
            "message": f"Saved the sequence.",
        }

    def _create_message_sequence(self, user_info: UserInfo) -> List[OutreachMessage]:
        """
        Generate AI-powered outreach sequence with structured output.

        This method creates a complete recruitment sequence using OpenAI
        with structured output validation via the Instructor library.

        Sequence Generation:
        1. Build comprehensive context prompt
        2. Call OpenAI with structured output requirements
        3. Parse and validate response using Instructor
        4. Create OutreachMessage objects with unique IDs
        5. Return ordered sequence or fallback on error

        Args:
            user_info: User context for personalization

        Returns:
            List[OutreachMessage]: Generated sequence of outreach messages
        """

        prompt = f"""
        Create a sequence of 4-5 professional outreach messages for recruiting a {user_info.role} at {user_info.company}.
        Have place holders for candidate name. Use the following information to personalize the messages:
        
        Context:
        - Company: {user_info.company}
        - Role: {user_info.role}
        - Industry: {user_info.industry or 'General'}
        - Experience Level: {user_info.experience_level or 'Mid-level'}
        - Additional Context: {user_info.additional_context or 'N/A'}
        
        Create messages for:
        1. Initial outreach (immediately)
        2. Follow-up (3 days after)
        3. Meeting request (1 weeks after)
        4. Final follow-up (2 weeks after)
        5. Offer (1 month after)"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional recruiter assistant. Create personalized, professional outreach messages.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_model=LLMOutReachMessages,  # Structured output validation
            )

            if not isinstance(response.messages, list):
                logger.error("OpenAI response is not a list of messages")
                return self._create_default_sequence(user_info)

            messages_data = [
                OutreachMessage(
                    id=str(uuid.uuid4()),
                    type=msg.type.value,
                    subject=msg.subject,
                    content=msg.content,
                    timing=msg.timing,
                    order=i + 1,
                )
                for i, msg in enumerate(response.messages)
            ]

            return messages_data

        except Exception as e:
            logger.error(f"Error generating sequence: {str(e)}")
            return self._create_default_sequence(user_info)

    def _create_default_sequence(self, user_info: UserInfo) -> List[OutreachMessage]:
        """Create a default message sequence as fallback"""
        return [
            OutreachMessage(
                id=str(uuid.uuid4()),
                type=MessageType.INITIAL_OUTREACH,
                subject=f"Exciting {user_info.role} Opportunity at {user_info.company}",
                content=f"Hi there! I hope this message finds you well. I'm reaching out about an exciting {user_info.role} opportunity at {user_info.company}...",
                timing="immediately",
                order=1,
            ),
            OutreachMessage(
                id=str(uuid.uuid4()),
                type=MessageType.FOLLOW_UP,
                subject=f"Following up on {user_info.role} role",
                content="I wanted to follow up on my previous message about the opportunity...",
                timing="3 days after",
                order=2,
            ),
        ]

    def _apply_edit_instruction(
        self,
        session: ConversationState,
        edit_type: EditType,
        edit_instruction: str,
        message_identifier: Optional[str] = None,
    ) -> List[OutreachMessage]:
        """Apply an edit instruction to message content using OpenAI"""

        # Prepare user info context
        # Sending these incase the user provided additional context
        user_info = session.user_info
        user_context = f"""
        User Info:
        - Company: {user_info.company or 'Not specified'}
        - Role: {user_info.role or 'Not specified'}
        - Industry: {user_info.industry or 'Not specified'}
        - Experience Level: {user_info.experience_level or 'Not specified'}
        - Additional Context: {user_info.additional_context or 'Not specified'}
        """

        # Prepare the current sequence context
        sequence_context = "\n".join(
            [
                f"{i + 1}. Message Type: {msg.type} Message Subject: {msg.subject} \n{msg.content} \nTiming: {msg.timing}"
                for i, msg in enumerate(session.message_sequence)
            ]
        )

        # Prepare the LLM prompt
        prompt = (
            f"""
        Edit the following sequence of outreach messages based on the given edit instruction. 
        Use the provided user info for context only and make edits if the current messages include stale user context. If asked to edit existing messages identify the messages to edit based on the provided identifier, else edit based on the instruction.

        {user_context}

        Current Message Sequence:
        {sequence_context}

        Edit Instruction:
        {edit_instruction}

        Message Identifier (if any): {message_identifier or 'None'}

        Return the updated sequence of messages in the same format as the original sequence.
        """
            if edit_type == EditType.EDIT.value
            else f"""
        Given a sequence of outreach messages, add a new message to the sequence in the correct order based on the following instruction.
        Use the provided user info for context.

        {user_context}

        Current Message Sequence:
        {sequence_context}

        Add Instruction:
        {edit_instruction}

        Return the updated sequence of messages in the same format as the original sequence.
        """
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional recruiter assistant. Create and Edit personalized, professional outreach messages.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_model=LLMOutReachMessages,
            )

            if not isinstance(response.messages, list):
                logger.error("OpenAI response is not a list of messages")
                return self._create_default_sequence(user_info)

            messages_data = [
                OutreachMessage(
                    id=str(uuid.uuid4()),
                    type=msg.type.value,
                    subject=msg.subject,
                    content=msg.content,
                    timing=msg.timing,
                    order=i + 1,
                )
                for i, msg in enumerate(response.messages)
            ]

            return messages_data

        except Exception as e:
            logger.error(f"Error Editing sequence: {str(e)}")
            return self._create_default_sequence(user_info)


# =============================================================================
# AI Agent
# =============================================================================

"""
RecruiterAgent - Core Agentic AI System

This is the heart of HELIX's agentic architecture, implementing autonomous decision-making
without relying on existing agentic frameworks. 
"""


class RecruiterAgent:
    """
    Core agentic AI system for recruitment assistance.

    This agent autonomously decides between conversational responses and tool execution,
    managing the entire recruitment workflow from information gathering to sequence finalization.

    The agent implements a custom agentic pattern:
    1. Process user input with full conversation context
    2. Let LLM autonomously decide: continue conversation OR execute tools
    3. Handle tool execution with real-time feedback
    4. Maintain session state and conversation continuity
    5. Provide intelligent follow-up responses

    Attributes:
        state_manager: Manages session state and conversation history
        tool_manager: Handles tool schema definition and execution
        socket_manager: Provides real-time communication to frontend
    """

    def __init__(
        self,
        state_manager: StateManager,
        tool_manager: ToolManager,
        socket_manager: SocketManager,
    ):
        self.state_manager = state_manager
        self.tool_manager = tool_manager
        self.socket_manager = socket_manager

    def process_message(self, session_id: str, user_message: str) -> str:
        """
        Main agentic processing loop - the core of autonomous decision-making.

        This method implements the key agentic pattern:
        1. Builds comprehensive conversation context
        2. Presents LLM with both conversation and tool options
        3. Lets LLM autonomously decide the appropriate response type
        4. Handles tool execution with real-time feedback
        5. Maintains conversation flow and state

        Args:
            session_id: Unique identifier for user session
            user_message: Latest user input to process

        Returns:
            str: Agent's response (conversational or tool execution summary)

        Agentic Decision Flow:
            User Input → Context Building → LLM Decision → Tool Execution OR Conversation → Response
        """

        session = self.state_manager.get_session(session_id)
        if not session:
            return "Session not found. Please start a new conversation."

        # Add user message to history
        self.state_manager.add_message_to_history(session_id, "user", user_message)

        # Build conversation context
        messages = self._build_conversation_context(session)
        messages.append({"role": "user", "content": user_message})

        try:
            # Call OpenAI with function calling
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=self.tool_manager.get_tools_schema(),
                tool_choice="auto",
                temperature=0.7,
            )

            response_message = response.choices[0].message

            # Handle tool calls
            if response_message.tool_calls:
                # LLM chose tool execution - handle agentic tool workflow
                return self._handle_tool_calls(session, response_message)
            else:
                # LLM chose conversation - continue chat flow
                assistant_response = response_message.content
                self.state_manager.add_message_to_history(
                    session_id=session_id, role="assistant", content=assistant_response
                )
                return assistant_response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I apologize, but I encountered an error processing your request. Please try again."

    def _build_conversation_context(self, session: ConversationState) -> List[Dict]:
        """
        Builds comprehensive context for agentic decision-making.

        This method creates the full context that enables the agent to make
        intelligent decisions about conversation flow and tool usage.

        Context includes:
        - System instructions for agentic behavior
        - Complete conversation history
        - Current session state and user information
        - Available message sequences and their status

        Args:
            session: Current conversation state

        Returns:
            List[Dict]: Formatted messages for LLM context
        """
        system_prompt = """You are a professional recruiter assistant. Your job is to:
        1. Gather information about the company and role the user wants to recruit for. Do not ask for these details if they are already provided in the current session info.
        2. Generate personalized outreach message sequences.
        3. Help users edit and refine their outreach messages when needed.
        
        Use the provided tools to perform actions like generating, editing, and managing outreach messages.

        Stepwise rules for approval and finalization:

        <step>
        If the user approves the outreach sequence, do not immediately save.
        Instead, confirm with the user:
        "Would you like to finalize and save this sequence?"
        </step>

        <step>
        If, and only if, the user explicitly confirms they want to finalize and save,
        then call the finalize_sequence tool.
        </step>
                
        Be conversational and helpful. Always ask clarifying questions if information is missing or unclear.
        """

        messages = [{"role": "system", "content": system_prompt}]

        messages.extend(session.conversation_history)

        # Add current session context for informed decision-making
        context = f"""
        Current session info:
        - Phase: {session.current_phase}
        - Company: {session.user_info.company or 'Not specified'}
        - Role: {session.user_info.role or 'Not specified'}
        - Message sequence count: {len(session.message_sequence)}
        """

        if session.message_sequence:
            context += "\n\nCurrent message sequence:\n"
            for i, msg in enumerate(session.message_sequence, 1):
                context += f"{i}. {msg.subject} (ID: {msg.id}) body: {msg.content} \n"

        messages.append({"role": "system", "content": context})

        return messages

    def _handle_tool_calls(self, session: ConversationState, response_message) -> str:
        """
        Handles agentic tool execution workflow.

        This method manages the complete tool execution cycle:
        1. Logs tool calls for conversation continuity
        2. Executes tools with real-time user feedback
        3. Processes tool results and errors
        4. Provides intelligent follow-up responses
        5. Maintains agentic workflow progression

        Args:
            session: Current conversation state
            response_message: LLM response containing tool calls

        Returns:
            str: Summary of tool execution and next steps

        Agentic Tool Workflow:
            Tool Decision → Real-time Feedback → Execution → Result Processing → Follow-up
        """
        tool_results = []

        # Add tool call messages to history
        self.state_manager.add_message_to_history(
            session_id=session.session_id,
            role="assistant",
            content=response_message.content,  # Usually '' or None when tool calling
            tool_calls=[
                {
                    "id": call.id,
                    "type": call.type,
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in response_message.tool_calls
            ],
        )

        # Iterate over tool calls and execute
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name

            # Provide real-time feedback to user about tool execution
            self.socket_manager.emit_tool_call(
                session.session_id,
                USER_FRIENDLY_TOOL_CALL.get(tool_name, "Executing tool..."),
            )
            try:
                parameters = json.loads(tool_call.function.arguments)
                result = self.tool_manager.execute_tool(
                    session.session_id, tool_name, parameters
                )
                tool_results.append(result)
                # TODO : Do we want to add entire message sequence response from tool call to history
                self.state_manager.add_message_to_history(
                    session_id=session.session_id,
                    role="tool",
                    content=(
                        result.get("message", "")
                        if result.get("success")
                        else result.get("error", "")
                    ),
                    name=tool_name,
                    tool_call_id=tool_call.id,
                )

            except json.JSONDecodeError:
                tool_results.append({"error": "Invalid tool parameters"})

                # Call LLM again with tool call results and past messages

        # Generate intelligent follow-up based on tool execution results
        if session.current_phase != "finalize_sequence":
            follow_up_prompt = {
                "role": "system",
                "content": """You are a recruiting assistant Agent. You have just executed a tool call and the results have been presented to user.
                                        Briefly summarize whats been done. Ask the user if they would like to approve the sequence 
                                        or want to make further edits.
                                        """,
            }
            messages = session.conversation_history.copy()
            messages.append(follow_up_prompt)
            follow_up_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
            )
            follow_up_message = follow_up_response.choices[0].message.content
            self.state_manager.add_message_to_history(
                session.session_id, "assistant", follow_up_message
            )
            return follow_up_message

        # Extract success messages and errors from tool results
        if all(result.get("success") for result in tool_results):
            success_messages = [result.get("message", "") for result in tool_results]
            response = " ".join(success_messages)

        # GOOD-TO-HAVE: Truly agentic by looping and feeding errors back to LLM
        else:
            error_messages = [
                result.get("error", "")
                for result in tool_results
                if result.get("error")
            ]
            response = f"I encountered some issues: {'; '.join(error_messages)}"
            self.state_manager.add_message_to_history(
                session.session_id, "tool", response
            )
        return response


# =============================================================================
# Initialize components
# =============================================================================

state_manager = StateManager()
socket_manager = SocketManager(socketio)
tool_manager = ToolManager(state_manager, socket_manager)
agent = RecruiterAgent(state_manager, tool_manager, socket_manager)

# =============================================================================
# Routes
# =============================================================================


@app.route("/api/session", methods=["POST"])
def create_session():
    """Create a new conversation session"""
    session_id = str(uuid.uuid4())
    state_manager.create_session(session_id)
    return jsonify({"session_id": session_id})


@app.route("/api/session/<session_id>/user", methods=["POST"])
def update_user_info(session_id):
    """Update user information in the session"""
    data = request.get_json()

    user_info = UserInfo(
        id=str(uuid.uuid4()),
        name=data.get("name", ""),
        company=data.get("company"),
        additional_context=data.get("additional_context", ""),
    )
    print(f"Updating user info for session {session_id}: {user_info}")
    state_manager.update_session_user_info(session_id, user_info)
    return user_info.id


# =============================================================================
# Socket Events
# =============================================================================


@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on("join_session")
def handle_join_session(data):
    """Join a session room"""
    session_id = data.get("session_id")
    if session_id:
        join_room(session_id)
        logger.info(f"Client {request.sid} joined session {session_id}")
        # Emit session information to the client when rejoining a session
        session = state_manager.get_session(session_id)
        if session:
            socket_manager.emit_sequence_update(session_id, session.message_sequence)
        else:
            # Incase server restarts when user was in session
            state_manager.create_session(session_id)


@socketio.on("leave_session")
def handle_leave_session(data):
    """Leave a session room"""
    session_id = data.get("session_id")
    if session_id:
        leave_room(session_id)
        logger.info(f"Client {request.sid} left session {session_id}")


@socketio.on("chat_message")
def handle_chat_message(data):
    """Handle incoming chat message"""
    session_id = data.get("session_id")
    message = data.get("message")

    if not session_id or not message:
        emit("error", {"message": "Invalid message format"})
        return

    # Process message with agent
    response = agent.process_message(session_id, message)

    # Emit response to client
    socket_manager.emit_chat_message(session_id, response, "assistant")


@socketio.on("update_sequence")
def handle_update_sequence(data):
    """Handle sequence update request from users manual edits"""
    session_id = data.get("session_id")
    msg_id = data.get("msg_id")
    content = data.get("content")
    session = state_manager.get_session(session_id)
    if not session:
        emit("error", {"message": "Invalid session"})
        return
    # update message in session message sequence
    for msg in session.message_sequence:
        if msg.id == msg_id:
            msg.content = content
            logger.info(f"Updated message {msg_id} in session {session_id}")
            break


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=4000)
