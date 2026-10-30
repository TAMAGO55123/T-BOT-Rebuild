from pathlib import Path
import sys

def get_main_dir() -> Path:
    """メイン直下のディレクトリのPathを取得します"""
    main_module = sys.modules["__main__"]
    main_file = Path(main_module.__file__).resolve()
    return main_file.parent

def create_file(path: Path, default: str = "") -> None:
    path = path.resolve()
    parent = path.parent
    print(path)
    if not path.parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        with path.open(mode="w", encoding="utf-8") as f:
            f.write(default)
def create_dir(path: Path, default: str = "") -> None:
    path = path.resolve()
    print(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)