"""Task management AI agent using OpenAI function calling.

This agent handles natural language requests to manage tasks,
using OpenAI's function calling to determine which tools to invoke.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from openai import OpenAI
from sqlmodel import Session

from config import get_settings
from .tools import (
    add_task,
    list_tasks,
    complete_task,
    update_task,
    delete_task,
    get_user_projects,
    TaskResult,
    TaskListResult
)

settings = get_settings()

# Define the tools/functions available to the agent
TASK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Create a new task in a project. Use this when the user wants to add, create, or make a new task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to add the task to"
                    },
                    "title": {
                        "type": "string",
                        "description": "The title/name of the task"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional detailed description of the task"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority level of the task"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Optional due date in ISO format (YYYY-MM-DD)"
                    }
                },
                "required": ["project_id", "title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List tasks in a project. Use this to show, display, or get tasks. Can filter by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to list tasks from"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in_progress", "completed"],
                        "description": "Optional filter by task status"
                    }
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed. Use this when the user wants to finish, complete, or mark done a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to complete"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update a task's properties. Use this to modify, edit, or change a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title for the task"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description for the task"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in_progress", "completed"],
                        "description": "New status for the task"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "New priority for the task"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task. Use this when the user wants to remove or delete a task. Requires admin permission.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to delete"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_projects",
            "description": "Get the list of projects the user has access to. Use this when you need to know which projects are available.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


class TaskAgent:
    """AI agent for task management using OpenAI function calling."""

    def __init__(self, session: Session, user_id: str, project_id: Optional[int] = None):
        """
        Initialize the task agent.

        Args:
            session: Database session for tool execution
            user_id: ID of the user making requests
            project_id: Optional default project ID for context
        """
        self.session = session
        self.user_id = user_id
        self.project_id = project_id
        self.client = OpenAI(api_key=settings.openai_api_key)

    def _get_system_prompt(self) -> str:
        """Build the system prompt with context about available projects."""
        projects = get_user_projects(self.session, self.user_id)

        project_context = ""
        if projects:
            project_list = "\n".join([
                f"- Project '{p['name']}' (ID: {p['id']}, Role: {p['role']})"
                for p in projects
            ])
            project_context = f"\n\nUser's available projects:\n{project_list}"

            if self.project_id:
                current = next((p for p in projects if p['id'] == self.project_id), None)
                if current:
                    project_context += f"\n\nCurrent active project: '{current['name']}' (ID: {current['id']})"

        return f"""You are a helpful task management assistant. You help users manage their tasks and projects.

You have access to tools to:
- Add new tasks to projects
- List tasks (with optional status filtering)
- Complete tasks
- Update task details
- Delete tasks (admin only)
- Get the user's projects

When the user asks about tasks without specifying a project, use the current active project if available, or ask them which project they mean.

When listing tasks, format them in a clear, readable way.

When creating tasks, confirm what was created.

For destructive actions (delete), confirm before executing if the user's intent seems ambiguous.

Be concise but friendly in your responses.{project_context}"""

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            Tool execution result as a dictionary
        """
        # Add project_id default if not specified but available
        if "project_id" not in arguments and self.project_id:
            if tool_name in ["add_task", "list_tasks"]:
                arguments["project_id"] = self.project_id

        if tool_name == "add_task":
            # Parse due_date if provided
            if "due_date" in arguments and arguments["due_date"]:
                try:
                    arguments["due_date"] = datetime.fromisoformat(arguments["due_date"])
                except ValueError:
                    arguments["due_date"] = None

            result = add_task(
                session=self.session,
                user_id=self.user_id,
                project_id=arguments["project_id"],
                title=arguments["title"],
                description=arguments.get("description"),
                priority=arguments.get("priority", "medium"),
                due_date=arguments.get("due_date")
            )
            return result.model_dump()

        elif tool_name == "list_tasks":
            result = list_tasks(
                session=self.session,
                user_id=self.user_id,
                project_id=arguments["project_id"],
                status=arguments.get("status")
            )
            return result.model_dump()

        elif tool_name == "complete_task":
            result = complete_task(
                session=self.session,
                user_id=self.user_id,
                task_id=arguments["task_id"]
            )
            return result.model_dump()

        elif tool_name == "update_task":
            result = update_task(
                session=self.session,
                user_id=self.user_id,
                task_id=arguments["task_id"],
                title=arguments.get("title"),
                description=arguments.get("description"),
                status=arguments.get("status"),
                priority=arguments.get("priority")
            )
            return result.model_dump()

        elif tool_name == "delete_task":
            result = delete_task(
                session=self.session,
                user_id=self.user_id,
                task_id=arguments["task_id"]
            )
            return result.model_dump()

        elif tool_name == "get_projects":
            projects = get_user_projects(self.session, self.user_id)
            return {"success": True, "projects": projects}

        else:
            return {"success": False, "message": f"Unknown tool: {tool_name}"}

    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Process a chat message and return a response.

        Args:
            message: The user's message
            history: Optional conversation history

        Returns:
            Tuple of (response_text, tool_calls)
        """
        # Build messages for the API
        messages = [{"role": "system", "content": self._get_system_prompt()}]

        # Add conversation history
        if history:
            for h in history:
                messages.append({
                    "role": h.get("role", "user"),
                    "content": h.get("content", "")
                })

        # Add current message
        messages.append({"role": "user", "content": message})

        tool_calls_made = []

        try:
            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TASK_TOOLS,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # Process tool calls if any
            while assistant_message.tool_calls:
                # Add assistant's response to messages
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })

                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    # Execute the tool
                    result = self._execute_tool(tool_name, arguments)

                    # Record the tool call
                    tool_calls_made.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
                    })

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })

                # Get next response from model
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=TASK_TOOLS,
                    tool_choice="auto"
                )
                assistant_message = response.choices[0].message

            return assistant_message.content or "I processed your request.", tool_calls_made

        except Exception as e:
            # Handle API errors gracefully
            error_msg = f"I encountered an error processing your request: {str(e)}"
            return error_msg, tool_calls_made


async def run_task_agent(
    session: Session,
    user_id: str,
    message: str,
    project_id: Optional[int] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Convenience function to run the task agent.

    Args:
        session: Database session
        user_id: User ID
        message: User's message
        project_id: Optional project context
        history: Optional conversation history

    Returns:
        Tuple of (response_text, tool_calls)
    """
    agent = TaskAgent(session, user_id, project_id)
    return agent.chat(message, history)
