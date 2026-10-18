# Configuration Merge Service

## Run locally
```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `/effective-config`. Repeated CLI overrides work, e.g. `/effective-config?set=port=9000&set=debug=true`.

Precedence: defaults -> `config.<APP_ENV>.yaml` (defaults to development) -> `.env` -> OS environment variables prefixed `APP_` -> query `set` overrides. `NUM_WORKERS` aliases to `workers`. `api_key` is always masked. CORS is enabled.
