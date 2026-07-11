from pathlib import Path


def build_portable_zip() -> str:
    output = Path(__file__).resolve().parent / "geeta-ai-portable.zip"
    output.write_bytes(b"portable placeholder")
    return str(output)


if __name__ == "__main__":
    print(build_portable_zip())
