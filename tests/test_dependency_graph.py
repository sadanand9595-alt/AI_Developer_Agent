from core.dependency_graph import DependencyGraph
from pathlib import Path


def test_dependency_graph_records_imports_for_python_files(workspace):
    graph = DependencyGraph()
    built = graph.build(workspace)

    main = str(Path("src") / "main.py")
    assert built[main] == {"os", "src.helpers"}
    assert graph.dependencies_of(main) == ["os", "src.helpers"]
    assert graph.files() == [main]
    assert graph.total_dependencies() == 2
