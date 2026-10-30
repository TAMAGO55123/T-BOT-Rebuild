import os
from typing import Any, Optional
import json
from func.log import get_log
from func.dir import create_file
from pathlib import Path

class File:
    def __init__(self, path:str) -> None:
        """
        設定ファイル管理用クラス
        JSONであること。
        """
        self.log = get_log(f"File.py")
        if not path.endswith(".json"):
            raise ValueError("JSONファイルのパスを指定してください")
        self.file_path:Path = Path(path)
        if not self.file_path.exists():
            create_file(self.file_path, "{}")
            self.log.info(f"{path}が存在しないため、ファイルを作成しました。")
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        with open(self.file_path, "r") as f:
            data = json.load(f)
        if key not in data:
            if default is not None:
                return default
            raise KeyError(f"{key}が存在しません。")
        return data[key]
    def get_all(self) -> dict:
        with open(self.file_path, "r") as f:
            return json.load(f)
    def default(self, key: str, value: Any) -> Any:
        d = self.get_all()
        if key not in d:
            self.set(key, value)
            return value
        return d[key]
    def set(self, key:str, value:Any) -> None:
        d = self.get_all()
        d[key] = value
        with open(self.file_path, "w") as f:
            json.dump(d, f, indent=4, ensure_ascii=False)
    def delete(self, key:str):
        d = self.get_all()
        d.pop(key)
        with open(self.file_path, "w") as f:
            json.dump(d, f, indent=4, ensure_ascii=False)
    def include(self, key:str) -> bool:
        return key in self.get_all()