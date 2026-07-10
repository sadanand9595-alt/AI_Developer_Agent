def open_file(self, file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            text = file.read()

        self.editor.clear()
        self.editor.setPlainText(text)

        self.statusBar().showMessage(file_path)

    except Exception as e:
        self.console.append(f"ERROR: {e}")
