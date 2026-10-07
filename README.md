# 삼성전자 데이터 채팅

삼성전자(005930)의 일별 종가를 Firestore에 보관하고, 요약 통계를 AI 채팅의 시스템 문맥에 넣어 데이터에 근거한 답변을 제공하는 웹 서비스입니다. 투자 판단이나 실시간 시세 제공 목적이 아닙니다.

## 기술 스택

- 백엔드: Python 3.10+, FastAPI, Pydantic, Firebase Admin SDK / Firestore, OpenAI API
- 프론트엔드: HTML, CSS, 바닐라 JavaScript
- 배포 대상: Render Web Service(백엔드), Vercel Static Site(프론트엔드)

## 데이터

- 종목: 삼성전자(005930), 일별 종가(원)
- 기간: **2025-09-24 ~ 2026-10-07**, **250거래일**
- 파일: [`backend/data/samsung_005930_daily.csv`](backend/data/samsung_005930_daily.csv)
- 수집: [FinanceDataReader 공식 프로젝트](https://github.com/FinanceData/FinanceDataReader)의 `DataReader('005930', '2025-01-01', '2026-10-08')` 결과 중 마지막 250건. 2026-10-07에 수집했습니다. 시세의 정정·수정주가 처리 방식은 제공처에 따릅니다.
- CSV SHA-256: `48268aacc23d322c64427a341085e06d119354c669ca0bb18846c46e72b91e76`
- CSV의 `date`, `value`, `memo`가 각각 거래일, 종가, 설명입니다. 데이터는 앱 시작 시 자동 반영되지 않습니다. 최초 배포 때 `seed.py`를 실행해야 합니다.

요약은 전체 기간의 평균·최대·최소·첫·최근 종가, 전체 변동률, 최근 20거래일 첫날 대비 변동률을 계산합니다. 변동률이 +1% 초과면 상승, -1% 미만이면 하락, 나머지는 보합으로 표시합니다. 채팅은 이 요약만 주입하므로 CSV의 개별 거래일 가격을 전부 알지는 못합니다.

## 로컬 실행

Python 3.10 이상과 Node.js 18 이상을 준비합니다. Firebase 프로젝트에서 Firestore Database를 만들고 서비스 계정 JSON을 발급받은 뒤, OpenAI API 키를 발급받습니다. 비밀키를 저장소에 추가하지 마세요.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 실제 키, 서비스 계정 JSON 또는 파일 경로를 설정
python seed.py
uvicorn app.main:app --reload
```

백엔드: `http://localhost:8000`, Swagger UI: `http://localhost:8000/docs`.

프론트는 `frontend/config.js`의 로컬 API 주소를 확인한 뒤 별도 터미널에서 실행합니다.

```powershell
cd frontend
python -m http.server 3000
```

`http://localhost:3000`에 접속합니다. 로컬 CORS 허용 주소는 `backend/.env`의 `ALLOWED_ORIGINS`에 포함돼야 합니다.

## 환경 변수

| 위치 | 변수 | 설명 |
|---|---|---|
| 백엔드 | `OPENAI_API_KEY` | OpenAI API 비밀키 |
| 백엔드 | `OPENAI_MODEL` | 선택. 기본값 `gpt-4o-mini` |
| 백엔드 | `FIREBASE_SERVICE_ACCOUNT_JSON` | 서비스 계정 JSON 전체 문자열 |
| 백엔드 | `FIREBASE_SERVICE_ACCOUNT_PATH` | JSON 대신 사용할 로컬 파일 경로 |
| 백엔드 | `ALLOWED_ORIGINS` | 쉼표로 구분한 프론트 주소. 마지막 `/` 없이 설정 |
| 프론트 Vercel 빌드 | `API_BASE_URL` | Render API 주소. 마지막 `/` 없이 설정 |

로컬 `.env`, 서비스 계정 파일, 빌드 결과는 `.gitignore`로 제외합니다. Vercel의 `API_BASE_URL`은 **공개 주소**이므로 비밀키를 넣지 마세요.

## API

| 메서드 | 경로 | 기능 |
|---|---|---|
| POST / GET | `/api/data` | 종가 추가 / 전체 조회 |
| PUT / DELETE | `/api/data/{id}` | 날짜 ID의 데이터 수정 / 삭제 |
| GET | `/api/data/summary` | 요약 통계 |
| POST / GET | `/api/conversations` | 대화 저장 / 목록 조회. 목록에 messages 포함 |
| GET / DELETE | `/api/conversations/{id}` | 전체 대화 불러오기 / 삭제 |
| POST | `/api/chat` | 요약을 시스템 문맥에 넣고 AI 응답 생성, 대화 자동 저장 |

`POST /api/chat` 예시: `{"message":"최근 20거래일 추세는?","conversation_id":null}`. 기존 대화의 `conversation_id`를 넘기면 이어서 저장합니다. 사용자 질문은 최대 2,000자, 출력은 최대 400토큰으로 제한합니다. Firestore 컬렉션은 `data`, `conversations`입니다. `data` 문서 ID는 거래일 문자열이며 대화 ID는 Firestore 자동 ID입니다.

## 배포

1. 이 폴더를 GitHub 저장소에 푸시합니다. `.env`와 서비스 계정 JSON이 포함되지 않았는지 `git status`로 확인합니다.
2. Render에서 GitHub 저장소를 연결하고 저장소 루트의 [`render.yaml`](render.yaml)로 Blueprint를 만들거나 Web Service를 수동 생성합니다. Root Directory `backend`, Build `pip install -r requirements.txt`, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`입니다. Render 대시보드에서 `OPENAI_API_KEY`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `ALLOWED_ORIGINS`를 비밀 환경 변수로 입력합니다.
3. Firestore에 초기 데이터를 넣습니다. 로컬에서 Render와 같은 Firebase 프로젝트 키를 설정한 뒤 `cd backend; python seed.py`를 한 번 실행합니다. 250건을 날짜 ID로 덮어써 재실행해도 중복되지 않습니다.
4. Vercel에서 같은 저장소를 연결하고 Root Directory를 `frontend`로 설정합니다. 환경 변수 `API_BASE_URL=https://<render-service>.onrender.com`을 입력하고 배포합니다. `frontend/build.mjs`가 이 값을 공개 `config.js`에 삽입합니다.
5. Vercel URL을 Render `ALLOWED_ORIGINS`에 추가하고 Render를 다시 배포합니다. Vercel 채팅 화면과 Render `/docs`를 확인합니다. 무료 Render 서비스는 첫 요청이 느릴 수 있어 화면에 안내 문구가 있습니다.

| 제출 URL | 값 |
|---|---|
| 프론트엔드 | 배포 후 입력 |
| 백엔드 API | 배포 후 입력 |
| Swagger UI | 배포 후 입력 (`/docs`) |

## 제출 스크린샷

실제 Firebase/OpenAI 연결과 배포 후 다음 화면을 캡처해 `screenshots/`에 보관합니다. 비밀키가 보이지 않게 하세요.

1. 데이터 요약과 사용자 질문·AI 답변이 동시에 보이는 채팅 화면
2. 종가 추가 또는 수정·삭제 결과가 보이는 데이터 관리 화면
3. 이전 대화를 선택해 메시지를 다시 불러온 화면

## 로컬 검증

```powershell
cd backend
pip install pytest httpx
pytest -q
```

테스트는 데이터 250건의 날짜/값 유효성과 핵심 API 입력 검증을 확인하며, 외부 유료 API를 호출하지 않습니다. 실제 Firestore·OpenAI 통합 동작과 제출 스크린샷은 계정 키를 설정한 뒤 확인해야 합니다.

## 보너스 과제

필수 기능의 실제 배포 검증을 마친 뒤 그래프·CSV 내보내기·다크 모드 및 도구 호출 연동을 검토합니다.
