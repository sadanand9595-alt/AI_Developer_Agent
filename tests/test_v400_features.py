from pathlib import Path

from core.ai_code_review import AICodeReview
from core.ai_debugger import AIDebugger
from core.ai_refactor_engine import AIRefactorEngine
from core.crash_reporter import CrashReporter
from core.language_support import LanguageSupport
from core.memory_analyzer import MemoryAnalyzer
from core.performance_profiler import PerformanceProfiler


def test_language_support_detects_supported_languages():
    support = LanguageSupport()
    assert support.detect("app.py") == "Python"
    assert support.detect("Main.java") == "Java"
    assert support.detect("main.go") == "Go"
    assert support.detect("main.rs") == "Rust"


def test_ai_debugger_explains_and_repairs():
    debugger = AIDebugger()
    explanation = debugger.explain_exception("NameError: name 'x' is not defined")
    assert "NameError" in explanation
    fix = debugger.auto_fix("print(x)", "NameError")
    assert "x" in fix or "fix" in fix.lower()
    repaired = debugger.one_click_repair("print(x)", "NameError")
    assert repaired


def test_ai_code_review_and_refactor_engine():
    reviewer = AICodeReview()
    issues = reviewer.review("def demo():\n    pass\n")
    assert issues

    refactorer = AIRefactorEngine()
    updated = refactorer.extract_method("def demo():\n    value = 1\n    print(value)\n", "helper")
    assert "def helper" in updated


def test_performance_profiler_and_memory_analyzer():
    profiler = PerformanceProfiler()
    result = profiler.measure(lambda: sum(range(5)))
    assert result.duration_ms >= 0

    analyzer = MemoryAnalyzer()
    summary = analyzer.analyze_path(Path("."))
    assert summary["path"]


def test_crash_reporter_writes_log(tmp_path: Path):
    reporter = CrashReporter(tmp_path)
    report_path = reporter.capture("Traceback: boom")
    assert Path(report_path).exists()
