from __future__ import annotations

import json
from typing import Any


def parse_setting_value(value_type: str, raw_value: str) -> Any:
    if value_type == "string":
        return raw_value
    if value_type == "int":
        return int(raw_value)
    if value_type == "float":
        return float(raw_value)
    if value_type == "bool":
        normalized = raw_value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
        raise ValueError("布尔值只允许 true 或 false")
    if value_type == "json":
        return json.loads(raw_value)
    raise ValueError(f"不支持的配置类型：{value_type}")


def serialize_setting_value(value_type: str, value: Any) -> str:
    if value_type == "string":
        if not isinstance(value, str):
            raise ValueError("字符串配置必须传入字符串值")
        return value

    if value_type == "int":
        if isinstance(value, bool):
            raise ValueError("整数配置不能使用布尔值")
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str):
            return str(int(value.strip()))
        raise ValueError("整数配置必须传入整数或整数字符串")

    if value_type == "float":
        if isinstance(value, bool):
            raise ValueError("浮点配置不能使用布尔值")
        if isinstance(value, (int, float)):
            return str(float(value))
        if isinstance(value, str):
            return str(float(value.strip()))
        raise ValueError("浮点配置必须传入数字或数字字符串")

    if value_type == "bool":
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "false"}:
                return normalized
        raise ValueError("布尔配置必须传入 true/false")

    if value_type == "json":
        if isinstance(value, str):
            parsed = json.loads(value)
            return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    raise ValueError(f"不支持的配置类型：{value_type}")
