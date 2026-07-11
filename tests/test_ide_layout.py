from ui.split_editor import SplitEditor
from ui.tabs import EditorTabs
from ui.terminal import IntegratedTerminal


def test_layout_components_initialize():
    tabs = EditorTabs()
    split_editor = SplitEditor()
    terminal = IntegratedTerminal()

    assert tabs.count() == 0
    assert split_editor.count() == 2
    assert terminal.output.toPlainText().startswith("Integrated terminal")
