# NH MDM Backend

FastAPI backend for the NH MDM mobile app.

Frontend repo: `../NH_MDM`

## Setup

```sh
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

## Run

```sh
uvicorn app.main:app --reload
```

Default API URLs:

- Health check: `GET http://127.0.0.1:8000/health`
- API health check: `GET http://127.0.0.1:8000/api/health`
- Auth placeholder: `POST http://127.0.0.1:8000/api/auth/partner-login`
- Kakao placeholder: `POST http://127.0.0.1:8000/api/kakao/login`
