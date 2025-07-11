# HELIX - AI-Powered Recruitment Agent

An intelligent recruitment assistant that leverages AI to generate, edit, and manage personalized outreach sequences for recruiters.

## Overview

HELIX is an application that combines real-time communication with agentic decision-making architecture to help recruiters create effective outreach messages. Built from scratch as a first exploration into agentic AI systems, the system autonomously decides between conversation and tool execution without relying on existing agentic frameworks.

## Features

- **AI-Driven Sequence Generation**: Create personalized outreach messages using GPT-4o mini
- **Real-time Communication**: Bi-directional communication between frontend and backend
- **Session Management**: Persistent session state with conversation history
- **Tool-Based Operations**: Comprehensive set of tools for sequence management
- **Structured Output**: Validated AI responses using Instructor

## Technology Stack

### Backend
- **Flask**: Lightweight REST API framework
- **Flask-SocketIO**: Real-time communication
- **OpenAI API**: GPT-4o mini for LLM completions and tool calling
- **Instructor**: Structured output parsing and validation
- **SQLite**: Lightweight database for persistence

### Frontend
- **React with TypeScript**: Modern component-based UI
- **Next.js**: React framework for production
- **Socket.IO Client**: Real-time client communication

## Architecture
<img width="2187" height="1225" alt="image" src="https://github.com/user-attachments/assets/1f568578-4f07-4e27-b47f-4614c23022a6" />

### Core Components

#### StateManager
- Session lifecycle management
- Conversation history tracking
- User data persistence
- Sequence state management

#### SocketManager
- Real-time event broadcasting between client and server

#### ToolManager
- Tool schema definition and validation
- Function call routing and execution

#### RecruiterAgent
- LLM-driven decision making
- Autonomous choice between conversation and tool execution

### Available Tools

1. **generate_sequence**: Create new outreach messages
2. **edit_sequence**: Modify existing sequences
3. **add_to_sequence**: Append to current sequence
4. **delete_sequence**: Remove sequences
5. **finalize_sequence**: Mark sequence as complete and save to database

## Decision Flow

1. Receive user input and conversation context
2. LLM evaluates: Continue conversation OR call backend tool
3. If tool call: Execute → Return results → Summarize to user
4. If conversation: Generate response directly

## Database Schema

### Key Tables
- **session**: Session metadata and state
- **sequences**: Generated outreach messages and history

## Session Flow

```
App Load → Check localStorage → Create/Join Session → Socket Connection → Ready
```

## Getting Started

### Prerequisites
- Node.js (v14 or higher)
- Python 3.8+
- pnpm or npm
- OpenAI API key

### Installation

1. Clone the repository
```bash
git clone https://github.com/SandhyaChinnaPillai/Helix-Agent.git
cd Helix-Agent
```

2. Install backend dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
# Add your OpenAI API key to .env in /backend
```

4. Install frontend dependencies and build
```bash
cd into /client
pnpm install
pnpm build
```

5. Run the app
```bash
# Backend
python recruiter_backend.py

# Frontend (in another terminal)
pnpm run dev
```

## Usage

1. Access the application in your browser localhost:3000
2. Interact with the AI agent to generate recruitment sequences
3. Finalize sequences to save them to the database

## Roadmap

### Near-Term Enhancements
- [ ] Streaming responses
- [ ] Robust error handling with self-healing agents
- [ ] Retry capabilities for failed operations
- [ ] Parallel tool calls with error handling
- [ ] Authentication and user context retrieval
- [ ] User token limits
- [ ] Rate limiting and spam protection
- [ ] Comprehensive testing suite

### Frontend Improvements
- [ ] User session switching
- [ ] Load conversation history
- [ ] Drag and drop for sequences
- [ ] Enhanced UI/UX


**Note**: This is an active development project. Features and architecture may change as the system evolves.
