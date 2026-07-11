from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass(slots=True)
class Breakpoint:
    path: str
    line: int


@dataclass(slots=True)
class StackFrame:
    name: str
    line: int


@dataclass(slots=True)
class DebugSession:
    breakpoints: List[Breakpoint] = field(default_factory=list)
    stack: List[StackFrame] = field(default_factory=list)
    variables: dict[str, object] = field(default_factory=dict)


class Debugger:
    """A lightweight debugger façade with breakpoints and stepping support."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()
        self.session = DebugSession()

    def toggle_breakpoint(self, path: str | Path, line: int) -> None:
        path_str = str(Path(path))
        existing = [bp for bp in self.session.breakpoints if bp.path == path_str and bp.line == line]
        if existing:
            self.session.breakpoints = [bp for bp in self.session.breakpoints if not (bp.path == path_str and bp.line == line)]
        else:
            self.session.breakpoints.append(Breakpoint(path=path_str, line=line))

    def step_into(self) -> List[StackFrame]:
        self.session.stack.append(StackFrame(name="step_into", line=1))
        return self.session.stack

    def step_over(self) -> List[StackFrame]:
        self.session.stack.append(StackFrame(name="step_over", line=1))
        return self.session.stack

    def get_variables(self) -> dict[str, object]:
        return self.session.variables

    def get_call_stack(self) -> List[StackFrame]:
        return self.session.stack
