import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
DEFAULTS = {"port": 8000, "workers": 1, "debug": False, "log_level": "info", "api_key": "default-secret-000"}
ALIASES = {"NUM_WORKERS": "workers", "APP_PORT": "port", "APP_WORKERS": "workers", "APP_DEBUG": "debug", "APP_LOG_LEVEL": "log_level", "APP_API_KEY": "api_key"}

def normalized_key(raw_key: str) -> str:
    return ALIASES.get(raw_key, raw_key.lower())

def coerce(key: str, value):
    key = key.lower()
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "1", "yes", "on")
    return str(value)

def read_yaml_layer(env_name: str) -> dict:
    path = BASE_DIR / f"config.{env_name}.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {normalized_key(str(k)): v for k, v in data.items()}

def read_dotenv_layer() -> dict:
    values = dotenv_values(BASE_DIR / ".env")
    layer = {}
    for raw_key, value in values.items():
        if value is None:
            continue
        if raw_key.startswith("APP_") or raw_key == "NUM_WORKERS":
            layer[normalized_key(raw_key)] = value
    return layer

def read_os_layer() -> dict:
    return {normalized_key(k): v for k, v in os.environ.items() if k.startswith("APP_")}

def effective_config(overrides: list[str]) -> dict:
    env_name = os.environ.get("APP_ENV", "development").strip().lower()
    config = dict(DEFAULTS)
    config.update(read_yaml_layer(env_name))
    config.update(read_dotenv_layer())
    config.update(read_os_layer())
    for item in overrides:
        if "=" not in item:
            continue
        raw_key, raw_value = item.split("=", 1)
        config[normalized_key(raw_key.strip())] = raw_value
    result = {key: coerce(key, value) for key, value in config.items()}
    result["api_key"] = "****"
    return result

app = FastAPI(title="Configuration Merge Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"service": "configuration-merge-service", "status": "ok"}

@app.get("/effective-config")
def get_effective_config(set: Optional[list[str]] = Query(default=None)):
    try:
        return effective_config(set or [])
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid configuration value: {exc}")
