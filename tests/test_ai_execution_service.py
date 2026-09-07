import py_compile
from ai.planner import AIPlanner
from ai.provider import AIProvider
from core.execution_system_factory import ExecutionSystemFactory
from core.result import Result
from services.ai_execution_service import AIExecutionService


class StubProvider(AIProvider):
    def generate(self, prompt: str) -> Result[str]:
        if prompt.startswith("You are the planning"):
            return Result.ok(
                '[{"name":"generate","description":"Generate code",'
                '"action":"generate_code","requires_approval":false,'
                '"metadata":{}}]'
            )

        return Result.ok("print(42)")


def test_ai_execution_service_plans_and_executes() -> None:
    provider = StubProvider()
    service = AIExecutionService(
        AIPlanner(provider),
        ExecutionSystemFactory.create_with_provider(provider),
    )

    result = service.execute("Create a calculator")

    assert result.is_success()
    context = result.require_data()
    assert context.get_metadata("request") == "Create a calculator"
    assert context.output_data == "print(42)"
    assert context.stage_results["generate"] == "print(42)"

class CodeFileStubProvider(AIProvider):
    def __init__(self, target_path: str) -> None:
        self.target_path = target_path

    def generate(self, prompt: str) -> Result[str]:
        if prompt.startswith("You are the planning"):
            return Result.ok(
                "["
                '{"name":"generate_code",'
                '"description":"Generate source code",'
                '"action":"generate_code",'
                '"requires_approval":false,'
                '"metadata":{}},'
                '{"name":"write_file",'
                '"description":"Write generated source code",'
                '"action":"write_file",'
                '"requires_approval":false,'
                '"metadata":{'
                f'"file_path":"{self.target_path}",'
                '"content_from_output":true'
                "}}"
                "]"
            )

        return Result.ok(
            "```python\n"
            "def hello():\n"
            '    return "Hello from AI Command Center"\n'
            "```"
        )


def test_ai_execution_service_generates_and_writes_valid_python(
    tmp_path,
) -> None:
    target = tmp_path / "hello_agent.py"

    provider = CodeFileStubProvider(
        target.as_posix()
    )

    service = AIExecutionService(
        AIPlanner(provider),
        ExecutionSystemFactory.create_with_provider(provider),
    )

    request = (
        "Create a Python file containing a hello() function "
        "that returns Hello from AI Command Center."
    )

    result = service.execute(request)

    assert result.is_success()

    context = result.require_data()

    assert target.exists()

    content = target.read_text(
        encoding="utf-8"
    )

    assert "```" not in content
    assert "```python" not in content
    assert "def hello():" in content
    assert 'return "Hello from AI Command Center"' in content

    py_compile.compile(
        str(target),
        doraise=True,
    )

    assert context.stage_results["generate_code"] == content
    assert context.stage_results["write_file"]["status"] == "written"
