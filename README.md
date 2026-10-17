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

Render는 `backend`를 루트로 사용하며 `render.yaml`에 실행 설정이 있습니다. Render에는 `FIREBASE_SERVICE_ACCOUNT_JSON`, `OPENAI_API_KEY`, `SITE_ACCESS_TOKEN`을 비밀 환경 변수로 등록합니다. `OPENAI_BASE_URL`, `OPENAI_MODEL`, `ALLOWED_ORIGINS=https://sese15260-samsung-stock-chat.vercel.app`도 설정합니다. 로컬에서는 `ALLOWED_ORIGINS=http://localhost:3000`을 사용합니다. 브라우저가 다른 도메인의 API를 호출하므로 허용 오리진에 실제 프론트 주소를 정확히 넣어야 합니다. Vercel은 `frontend`를 루트로 사용하고 빌드 변수 `API_BASE_URL=https://sese15260-samsung-stock-api.onrender.com`을 설정합니다. 비밀값은 README·코드·Git에 기록하지 않습니다.

## 제출 화면과 확인 범위

- [공개 접속 화면](screenshots/live-public.png), [Swagger UI](screenshots/live-api-docs.png), [데이터 요약·그래프](screenshots/live-dashboard.png)
- [실제 질문과 AI 답변](screenshots/live-chat-answer.jpg), [데이터 수정 저장](screenshots/live-data-update.jpg), [이전 대화 불러오기](screenshots/live-history-reloaded.jpg), [390px 모바일 화면](screenshots/live-mobile.png)

캡처는 실제 배포 화면이며 접속 코드와 API 키는 보이지 않습니다. 모바일은 배포 화면을 390px와 320px 폭에서 확인했고 가로 넘침이 없었습니다. 데이터 **추가** 후 Firestore 콘솔 확인은 별도 실배포 검증이 필요합니다. 관리자 화면에서 사용하지 않는 날짜의 시험 데이터를 추가하고 목록·Firestore `data` 문서를 확인한 뒤 삭제하면 원본 250건을 보존할 수 있습니다.

## 코드 구조와 데이터 설계

| 파일 | 책임 |
|---|---|
| `backend/app/main.py` | FastAPI 경로, 접근 제어, AI 호출과 HTTP 오류 처리 |
| `backend/app/models.py` | Pydantic 요청 스키마와 입력 검증 |
| `backend/app/store.py` | Firestore `data`·`conversations` 읽기와 쓰기 |
| `backend/app/summary.py` | 기간, 평균, 최고·최저, 최근 추세 계산 |
| `frontend/app.js` | API 요청, 화면 상태, 데이터·대화 표시 |

서비스 규모가 작아 별도 `APIRouter` 파일은 두지 않았습니다. HTTP 처리·검증·저장·계산을 파일 책임으로 분리했습니다.

Firestore `data`는 날짜를 문서 ID로 사용하고 `{date, value, memo}`를 저장합니다. 같은 날짜의 중복 등록을 확인하고 날짜로 수정·삭제하기 위한 구조입니다. `conversations`는 자동 생성 ID마다 `{title, messages: [{role, content}, ...], updated_at}`을 저장합니다. 대화 단위로 목록을 정렬하고 ID로 전체 메시지를 다시 불러오기 위한 구조입니다.

`DataIn`은 날짜 형식, 양수 종가, 최대 300자 메모를 검사합니다. `ChatIn`은 최대 2,000자 질문을, `ConversationIn`과 `Message`는 제목·메시지 개수·내용 길이·`user`/`assistant` 역할을 검사합니다. FastAPI가 요청 시 검증해 잘못된 입력은 422로 반환합니다. `DataOut`은 정의돼 있지만 현재 라우트에 `response_model`로 적용되지는 않았습니다. 날짜 중복·없는 ID 검사는 저장소 결과에 따라 409·404로 처리합니다.

## 데이터·대화 처리 흐름

1. 데이터 추가·수정·삭제 후 프론트엔드가 `refresh()`를 호출해 `/api/data` 목록·그래프와 `/api/data/summary` 요약을 다시 읽습니다. `rows`는 화면의 데이터 목록, `editingId`는 수정 중인 데이터 ID입니다. 아래는 실제 요청 형식을 나타낸 **예시**이며 배포 저장 성공 기록은 아닙니다.

   ```text
   POST /api/data  {"date":"2026-10-08","value":270000,"memo":"예시"}
   201             {"date":"2026-10-08","value":270000,"memo":"예시","id":"2026-10-08"}
   GET /api/data   → 갱신된 목록
   ```

2. 요약 API는 `symbol`·`name`·`unit`, `period`(시작·끝 날짜), `count`(건수), `metrics`(평균·최고·최저·최신 종가와 변화율), `recent_daily_counts`(최근 상승·하락·보합일), `trend`·`trend_method`, `monthly`(월별 평균), `recent`(최근 20거래일)를 반환합니다. 화면과 채팅이 같은 `summarize()` 함수를 재사용하므로 통계 기준이 같습니다.
3. 채팅은 저장된 데이터를 요약해 시스템 프롬프트에 넣고, 기존 대화의 최근 12개 메시지와 새 질문을 AI에 보냅니다. AI가 내용 있는 답변을 반환한 **후에만** 질문·답변을 함께 Firestore에 저장합니다. 첫 질문 앞부분이 대화 제목이 되고, `activeId`에 반환된 `conversation_id`를 보관해 이어 묻습니다. 제목을 누르면 `GET /api/conversations/{id}`로 저장된 메시지를 다시 표시합니다. AI 호출 실패나 빈 답변은 저장하지 않습니다.

   ```text
   POST /api/chat  {"message":"최근 종가는?","conversation_id":null}
   200             {"answer":"…","conversation_id":"생성된 ID","summary":{…}}
   GET /api/conversations       → [{"id":"생성된 ID","title":"최근 종가는?","messages":[…],"updated_at":"…"}]
   GET /api/conversations/{id}  → 해당 대화의 전체 메시지
   ```

요약을 주입하는 이유는 AI가 Firestore 데이터를 직접 알지 못하기 때문입니다. 전체 250행 대신 통계를 전달해 입력량을 줄이지만, 요약에 없는 세부 거래일은 정확히 답하기 어렵고 AI가 수치를 잘못 해석할 가능성은 남습니다. 시스템 지침은 저장된 수치만 단정하고 투자 권유·미래 예측을 피하도록 합니다. 이 지침만으로 악성 프롬프트를 완전히 차단할 수는 없습니다.

## 운영과 변경 지점

- Render 무료 서비스의 첫 요청은 지연될 수 있어 최초 요약 로딩과 채팅 대기 중 안내 문구를 표시합니다. `render.yaml`의 `/health`는 상태 확인용이며 서버를 계속 깨워 두는 기능은 아닙니다. 별도 워밍업 작업은 운영하지 않습니다.
- Pydantic 길이·형식 검증, 날짜 중복 확인, 관리자 접속 코드가 기본 방어입니다. 프론트엔드는 메시지를 `textContent`로 표시해 HTML로 실행하지 않습니다. 별도 악성 문구 필터·사용량 제한은 없으므로 공개 범위를 넓힐 때 보완이 필요합니다. 사용자 질문·키·인증 헤더를 로그에 남기지 않습니다.
- 최근 **20거래일** 기준은 `backend/app/summary.py`의 `values[-20:]`와 `rows[-20:]`에 있습니다. 30거래일로 바꾸려면 두 구간, `backend/app/main.py`의 20거래일 지침, 프론트의 예시 문구, 관련 테스트를 함께 수정합니다. 데이터가 크게 늘면 현재의 전체 조회 대신 기간 조회나 사전 계산 요약을 검토합니다.
