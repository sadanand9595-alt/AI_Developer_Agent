from pathlib import Path


def build_installer() -> str:
    output = Path(__file__).resolve().parent / "geeta-ai-installer.zip"
    output.write_bytes(b"installer placeholder")
    return str(output)


if __name__ == "__main__":
    print(build_installer())
