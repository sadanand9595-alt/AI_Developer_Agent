from __future__ import annotations

import json
from typing import Any

from ai.provider import AIProvider
from core.result import Result


class AIPlanner:
    """AI-powered planner that converts natural-language requests into plans."""

    def __init__(self, provider: AIProvider) -> None:
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must be an AIProvider")

        self._provider = provider

    def create_plan(self, request: str) -> Result[list[dict[str, object]]]:
        if not isinstance(request, str):
            return Result.fail(
                "INVALID_REQUEST",
                "request must be a string",
            )

        normalized_request = request.strip()

        if not normalized_request:
            return Result.fail(
                "INVALID_REQUEST",
                "request must not be empty",
            )

        prompt = self._build_prompt(normalized_request)

        try:
            provider_result = self._provider.generate(prompt)
        except Exception as exc:
            return Result.fail(
                "AI_PLANNER_ERROR",
                str(exc),
            )

        if not provider_result.success:
            return Result.fail(
                provider_result.error_code or "AI_PROVIDER_ERROR",
                provider_result.error_message or "AI provider failed",
                provider_result.details,
            )

        try:
            raw_response = provider_result.require_data()
        except Exception as exc:
            return Result.fail(
                "AI_PLANNER_ERROR",
                str(exc),
            )

        if not isinstance(raw_response, str):
            return Result.fail(
                "INVALID_PLAN_JSON",
                "AI planner response must be a string",
            )

        cleaned_response = self._normalize_json_response(raw_response)

        try:
            parsed = json.loads(cleaned_response)
        except json.JSONDecodeError as exc:
            return Result.fail(
                "INVALID_PLAN_JSON",
                str(exc),
            )

        if not isinstance(parsed, list):
            return Result.fail(
                "INVALID_PLAN",
                "AI planner response must be a JSON array",
            )

        validated_steps: list[dict[str, object]] = []

        for index, step in enumerate(parsed):
            if not isinstance(step, dict):
                return Result.fail(
                    "INVALID_PLAN",
                    f"Plan step {index} must be an object",
                )

            name = step.get("name")
            description = step.get("description")
            action = step.get("action")
            requires_approval = step.get("requires_approval")
            metadata = step.get("metadata")

            if not isinstance(name, str) or not name.strip():
                return Result.fail(
                    "INVALID_PLAN",
                    f"Plan step {index} requires a non-empty name",
                )

            if not isinstance(description, str):
                return Result.fail(
                    "INVALID_PLAN",
                    f"Plan step {index} requires a description string",
                )

            if not isinstance(action, str) or not action.strip():
                return Result.fail(
                    "INVALID_PLAN",
                    f"Plan step {index} requires a non-empty action",
                )

            if not isinstance(requires_approval, bool):
                return Result.fail(
                    "INVALID_PLAN",
                    f"Plan step {index} requires requires_approval to be a boolean",
                )

            if not isinstance(metadata, dict):
                return Result.fail(
                    "INVALID_PLAN",
                    f"Plan step {index} requires metadata to be an object",
                )

            validated_steps.append(
                {
                    "name": name.strip(),
                    "description": description,
                    "action": action.strip(),
                    "requires_approval": requires_approval,
                    "metadata": metadata,
                }
            )

        return Result.ok(validated_steps)

    @staticmethod
    def _normalize_json_response(raw_response: str) -> str:
        """
        Normalize common LLM JSON response formats.

        Accepted examples:

            [{"name": "..."}]

        and:

            ```json
            [{"name": "..."}]
            ```

        Also handles surrounding whitespace and attempts to extract a
        JSON array when the model adds explanatory text around it.
        """
        text = raw_response.strip()

        if not text:
            return text

        # Remove Markdown code fences.
        if text.startswith("```"):
            lines = text.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        # If the model added explanatory text around the JSON array,
        # extract the outermost JSON array.
        if not text.startswith("["):
            start = text.find("[")
            end = text.rfind("]")

            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1].strip()

        return text

    def _build_prompt(self, request: str) -> str:
        return f"""You are the planning engine of AI Command Center.

Your job is to convert the user's request into an ordered execution plan.

IMPORTANT RULES:
1. Do not execute anything.
2. Return JSON only.
3. Return a JSON array of steps.
4. Each step must contain:
   - name
   - description
   - action
   - requires_approval
   - metadata
5. requires_approval must be a boolean.
6. metadata must be an object.
7. Actions must describe executable capabilities, not natural-language instructions.

AVAILABLE ACTIONS:
1. generate_code
   Purpose: Generate source code from the user's request.
   Output: The generated source code as text.

2. write_file
   Purpose: Write text content to a filesystem path.
   Required metadata:
   - "file_path": destination file path
   Optional metadata:
   - "content": explicit text content
   - "content_from_output": true when the content must come from the previous action's output.

DATA FLOW RULE:
When the user asks you to generate code and save it to a file, create TWO ordered steps:
1. generate_code
2. write_file

The write_file step must use:
- "content_from_output": true
when it should write the code generated by the previous generate_code step.

Do not place generated source code directly inside write_file metadata when it is already produced by generate_code.

Example: code generation only
[
  {{
    "name": "generate_code",
    "description": "Generate the requested source code.",
    "action": "generate_code",
    "requires_approval": false,
    "metadata": {{}}
  }}
]

Example: generate code and save it to a file
[
  {{
    "name": "generate_code",
    "description": "Generate the requested source code.",
    "action": "generate_code",
    "requires_approval": false,
    "metadata": {{}}
  }},
  {{
    "name": "write_file",
    "description": "Write the generated source code to the requested file.",
    "action": "write_file",
    "requires_approval": false,
    "metadata": {{
      "file_path": "temp_agent_test/hello_agent.py",
      "content_from_output": true
    }}
  }}
]

PLAN QUALITY RULES:
- Preserve the user's requested file path when provided.
- Do not invent unnecessary execution steps.
- Keep steps in the exact order required for execution.
- Use only actions listed in AVAILABLE ACTIONS.
- Never execute actions while planning.
- Return valid JSON only.

USER REQUEST:
{request}
"""
