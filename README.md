# 삼성전자 주가 데이터 채팅

삼성전자(005930)의 일별 종가를 조회·관리하고, 저장된 데이터 요약을 바탕으로 AI와 대화하는 웹 서비스입니다. 실시간 시세나 투자 조언을 제공하지 않습니다.

## 서비스

- [웹사이트](https://sese15260-samsung-stock-chat.vercel.app/)
- [API 문서](https://sese15260-samsung-stock-api.onrender.com/docs)

링크를 열면 주가 조회와 AI 채팅을 이용할 수 있습니다. 종가 수정·삭제와 전체 대화 기록 관리는 관리자 접속 코드가 필요합니다.

## 주요 기능

- 삼성전자 종가 **250거래일**(2025-09-24~2026-10-07) 조회 및 추가·수정·삭제
- 평균, 최고·최저, 최근 20거래일 추세 요약과 종가 그래프
- 데이터 요약을 반영한 AI 채팅과 대화 기록 저장·불러오기
- CSV 내보내기, 라이트·다크 모드

## 기술 구성

| 구성 | 기술 |
|---|---|
| 프론트엔드 | HTML, CSS, 바닐라 JavaScript · Vercel |
| 백엔드 | FastAPI · Render |
| 데이터베이스 | Firebase Firestore |
| AI | OpenAI 호환 Chat Completions API(Codyssey) |

원본 데이터는 [`backend/data/samsung_005930_daily.csv`](backend/data/samsung_005930_daily.csv)에 있습니다. [FinanceDataReader](https://github.com/FinanceData/FinanceDataReader)의 삼성전자 일별 종가 중 마지막 250건을 사용했습니다.

## 로컬 실행

Python 3.10 이상이 필요합니다. 저장소 폴더에서 아래 명령을 실행합니다(Windows PowerShell).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`backend/.env`에 Codyssey virtual key(`OPENAI_API_KEY`), `OPENAI_BASE_URL`, `OPENAI_MODEL`, Firebase 서비스 계정 파일의 저장소 밖 경로(`FIREBASE_SERVICE_ACCOUNT_PATH`), `SITE_ACCESS_TOKEN`, `ALLOWED_ORIGINS=http://localhost:3000`을 설정합니다. `.env`와 서비스 계정 파일은 Git에 올리지 않습니다.

같은 터미널에서 데이터를 확인·등록하고 API를 실행합니다.

```powershell
python seed.py --dry-run
python seed.py
python -m uvicorn app.main:app --reload
```

다른 터미널에서 저장소의 `frontend` 폴더로 이동해 실행합니다.

```powershell
cd frontend
..\.venv\Scripts\python.exe -m http.server 3000
```

로컬 주소는 `http://localhost:3000`입니다. 관리자 기능은 `#access=<SITE_ACCESS_TOKEN>`을 붙인 주소로 사용할 수 있습니다. 테스트는 가상환경을 활성화한 터미널에서 `backend` 폴더로 이동한 뒤 `python -m pip install pytest httpx`와 `python -m pytest -q tests`로 실행합니다.

## 배포 설정

Render는 `backend`를 루트로 사용하며 `render.yaml`에 실행 설정이 있습니다. 비밀 환경 변수 `FIREBASE_SERVICE_ACCOUNT_JSON`, `OPENAI_API_KEY`, `SITE_ACCESS_TOKEN`과 `OPENAI_BASE_URL`, `OPENAI_MODEL`, 프론트 주소를 담은 `ALLOWED_ORIGINS`가 필요합니다. Vercel은 `frontend`를 루트로 사용하고 빌드 변수 `API_BASE_URL`에 Render 서버 주소를 설정합니다.

실제 배포 화면과 API 문서 캡처는 [`screenshots/`](screenshots/)에 있습니다.
