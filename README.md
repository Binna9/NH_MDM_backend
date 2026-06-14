# NH MDM Backend

FastAPI backend for the NH MDM mobile app.

Frontend repo: `../NH_MDM`

## Setup

```sh
py -m venv .venv

source venv/Scripts/activate

pip install -r requirements.txt

cp .env.example .env
```

## Run

```sh
uvicorn app.main:app --reload
## 전역으로 열기 
uvicorn app.main:app --host 0.0.0.0 --port 8000 

```

Default API URLs:

- Health check: `GET http://127.0.0.1:8000/health`
- API health check: `GET http://127.0.0.1:8000/api/health`
- Auth placeholder: `POST http://127.0.0.1:8000/api/auth/partner-login`
- Kakao placeholder: `POST http://127.0.0.1:8000/api/kakao/login`
