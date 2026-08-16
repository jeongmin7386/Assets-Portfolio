# Moa — Personal Asset Portfolio Dashboard

Moa는 Notion에서 직접 관리하는 수동 자산과 토스증권 Open API의 투자자산을 PostgreSQL에 통합해 순자산, 자산배분, 투자손익, 예적금, 부채, 재무목표, 일별 성장 추이를 보여주는 읽기 전용 개인 자산 대시보드입니다.

가계부가 아닙니다. 거래내역·수입·지출·소비 카테고리·예산·주문·자동매매·투자 추천 기능은 포함하지 않습니다.

## Architecture

```text
Notion (6 Data Sources)       Toss Securities Open API
          │                              │
          └──────── Sync Services ───────┘
                         │
                    PostgreSQL
              통합데이터 · Snapshot · Sync 이력
                         │
                 FastAPI (read only)
                         │
                 Next.js Dashboard
```

기존 저장소의 포트폴리오/사이트 빌더는 그대로 유지하고, 충돌을 피하기 위해 이 앱을 `asset-dashboard/`에 독립적으로 추가했습니다.

## Tech Stack

- Frontend: Next.js 16, React 18, TypeScript strict, TanStack Query, Zod, Recharts, CSS
- Backend: Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2 async, Alembic, httpx
- Database: PostgreSQL 16, `NUMERIC` 금액/비율, timezone-aware timestamps
- External APIs: Notion API `2026-03-11`, Toss Securities OAuth 2.0 Client Credentials

## Folder Structure

```text
asset-dashboard/
├─ frontend/
│  ├─ app/                    # App Router 9개 화면
│  ├─ components/             # 레이아웃, 차트, 표, 도메인 뷰
│  ├─ lib/                    # API, Zod, 형식화, 데모 데이터
│  └─ public/og.png           # 링크 공유 이미지
├─ backend/
│  ├─ app/api/routes/         # Dashboard/자산/동기화/Webhook API
│  ├─ app/clients/            # Notion/Toss 회복탄력성 클라이언트
│  ├─ app/models/             # SQLAlchemy 모델
│  ├─ app/repositories/       # DB/Demo 데이터 접근
│  ├─ app/services/           # 계산, Sync, Snapshot
│  ├─ migrations/             # Alembic migration
│  └─ tests/                  # 계산·매핑·API 테스트
├─ docker-compose.yml
├─ render.yaml
└─ .env.example
```

## Database Schema

초기 migration은 아래 테이블을 만듭니다.

- `financial_accounts`
- `manual_assets`
- `savings_products`
- `debts`
- `financial_goals`
- `allocation_targets`
- `investment_accounts`
- `investment_positions`
- `security_master`
- `exchange_rates`
- `asset_snapshots`
- `asset_snapshot_items`
- `sync_runs`
- `provider_cache`

계좌 Rollup 금액은 합계에 더하지 않습니다. `manual_assets + savings_products + investment_positions`만 총자산 계산에 사용하며 `debts`를 차감해 순자산을 계산합니다. TOSS 계좌에 연결된 수동 자산은 중복 가능 항목으로 감지해 합계에서 제외하고 경고합니다.

## Environment Variables

`asset-dashboard/.env.example`을 `asset-dashboard/.env`로 복사한 뒤 값을 입력합니다. 실제 Secret은 커밋하지 않습니다.

필수 기본값:

```text
DATABASE_URL=postgresql+asyncpg://portfolio:portfolio@localhost:5433/portfolio
FRONTEND_URL=http://localhost:3001
DEMO_MODE=true
NEXT_PUBLIC_API_URL=http://localhost:8001/api
NEXT_PUBLIC_DEMO_MODE=true
```

실데이터 전환 시 두 `DEMO_MODE` 값을 `false`로 바꾸고 Notion/Toss 환경변수를 설정합니다.

## Development Setup

### 1. PostgreSQL

```powershell
cd asset-dashboard
docker compose up -d postgres
```

### 2. Backend

```powershell
cd asset-dashboard/backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

### 3. Frontend

```powershell
cd asset-dashboard/frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:3001/overview`를 엽니다. `DEMO_MODE=true` 상태에서는 외부 계정 없이 전체 화면과 계산 흐름을 확인할 수 있습니다.

## Notion Setup

내부 Integration을 생성해 다음 6개 원본 Data Source에 연결 권한을 부여합니다.

1. Accounts
2. Assets
3. Savings
4. Debts
5. Goals
6. Allocation Targets

연결 토큰과 각 Data Source ID를 `.env`에 입력합니다. 연결된(Linked) Data Source가 아니라 원본 Data Source를 공유해야 하며 Relation 대상 Data Source도 Integration에 공유되어야 합니다.

### Notion Property Mapping

속성명은 서비스 코드에 흩어져 있지 않고 `backend/app/services/notion/property_maps.py`에 모여 있습니다. 현재 한국어 속성명과 실제 워크스페이스가 다르면 이 파일의 값만 수정합니다. 가능하면 Data Source의 속성 ID 기반으로 확장하는 것을 권장합니다.

현재 API 버전은 `2026-03-11`이며 행 조회는 `POST /v1/data_sources/{data_source_id}/query`를 사용합니다. Webhook은 `X-Notion-Signature` HMAC-SHA256을 검증한 뒤 변경 신호로만 사용하고, 최종 값은 Notion API에서 다시 조회합니다.

## Notion Sync

```text
POST /api/sync/notion
```

동기화 순서는 Relation을 고려해 Accounts → Assets → Savings → Debts → Goals → Allocation Targets입니다. `notion_page_id` unique key를 기준으로 upsert하며 `notion_last_edited_time`을 저장합니다.

Webhook URL:

```text
POST /api/webhooks/notion
```

Notion 개발자 포털에서 공개 HTTPS URL을 등록하고 전달받은 verification token을 `NOTION_WEBHOOK_VERIFICATION_TOKEN`에 저장합니다.

## Toss Securities API Setup

토스증권 WTS의 설정 → Open API에서 Client ID/Secret과 허용 IP를 등록합니다. 구현은 공식 OpenAPI의 다음 읽기 전용 endpoint만 사용합니다.

- `POST /oauth2/token`
- `GET /api/v1/accounts`
- `GET /api/v1/holdings`
- `GET /api/v1/exchange-rate?baseCurrency=USD&quoteCurrency=KRW`

계좌·보유종목 요청에는 `X-Tossinvest-Account: {accountSeq}`가 포함됩니다. 주문 관련 endpoint는 코드에 존재하지 않습니다. 토큰은 서버 메모리에서 만료 전까지 재사용하고 브라우저·로그·DB에 저장하지 않습니다. 429의 `Retry-After`와 5xx에 한정해 jitter가 있는 지수 백오프를 적용합니다.

종목 유형은 근거 없이 ETF/개별주식으로 추정하지 않습니다. 메타데이터를 아직 조회하지 않은 실데이터는 `UNKNOWN`으로 저장합니다.

## Snapshot System

수동 실행:

```text
POST /api/snapshots
```

스케줄러/cron 실행:

```powershell
cd asset-dashboard/backend
.\.venv\Scripts\python.exe -m app.jobs.create_daily_snapshot
```

같은 날짜의 스냅샷은 upsert되고 상세 구성은 `asset_snapshot_items`로 다시 저장됩니다. 배포 제공자의 cron이나 GitHub Actions 등 외부 스케줄러에서 하루 한 번 호출할 수 있습니다.

## Frontend Pages

- `/overview`: 순자산, 총자산/부채, 자산배분, 1년 성장
- `/assets`: Notion 수동자산과 자산군 필터
- `/investments`: 투자 평가액·원금·손익·수익률·보유종목
- `/savings`: 현재잔액·만기·예상 세후이자
- `/debts`: 현재잔액·상환 진행률
- `/allocation`: 현재/목표/허용범위·리밸런싱 정보
- `/goals`: 실제 자산 기준 목표 달성률
- `/history`: 1M/3M/6M/1Y/ALL 스냅샷
- `/settings`: Notion/Toss/PostgreSQL 연결 상태와 수동 Sync

## Backend API

주요 endpoint는 `/api/dashboard/summary`, `/api/dashboard/allocation`, `/api/history/net-worth`, `/api/accounts`, `/api/assets`, `/api/savings`, `/api/debts`, `/api/investments`, `/api/goals`, `/api/sync/*`, `/api/snapshots`입니다. FastAPI 문서는 개발 중 `http://localhost:8001/docs`에서 확인할 수 있습니다.

## Verification

```powershell
cd asset-dashboard/frontend
npm run lint
npm run typecheck
npm run build
npm audit --omit=dev

cd ../backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic upgrade head --sql
.\.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"
```

테스트는 총자산·순자산·부채 차감·자산배분·%p 차이·목표 진행률·예적금 추정·환율·TOSS 중복 합산·include 규칙의 계층 책임·공식 TOSS HoldingsItem 매핑·주요 API 응답을 검증합니다.

## Deployment

`frontend/Dockerfile`, `backend/Dockerfile`, `render.yaml`을 제공합니다. 기본 Blueprint는 데이터가 30일 뒤 만료되는 무료 PostgreSQL 대신 `basic-256mb`를 사용합니다. Render Blueprint를 사용할 경우 Postgres 내부 URL은 애플리케이션에서 자동으로 asyncpg URL로 정규화됩니다. 배포 환경에서는 다음을 반드시 설정합니다.

- Backend `FRONTEND_URL`: 실제 프런트엔드 origin
- Frontend `NEXT_PUBLIC_API_URL`: `https://<api-host>/api`
- 두 앱의 Demo Mode: `false`
- Notion/Toss Secret과 6개 Data Source ID
- Notion Webhook 공개 URL과 verification token
- 토스증권 Open API 허용 IP

배포 후 backend release 단계에서 `alembic upgrade head`를 실행하고, 하루 한 번 Snapshot job을 예약합니다.

## Security Notes

- Secret은 서버 환경변수에서만 읽습니다.
- 브라우저와 LocalStorage에 토큰을 저장하지 않습니다.
- 로그 필터는 key/token/password 관련 메시지를 redaction합니다.
- CORS는 `FRONTEND_URL` 한 곳만 허용합니다.
- 외부 API 오류가 나도 마지막 PostgreSQL 데이터를 계속 제공할 수 있는 구조입니다.
- 공개 인터넷에 배포할 경우 Cloudflare Access, VPN, reverse-proxy 인증 등 개인 접근 제어를 반드시 추가하세요.

## Known Limitations

- 실제 Notion/Toss 계정 데이터는 사용자 Secret이 없어 호출 검증하지 않았습니다. 공식 OpenAPI 응답 예제 기반 unit test를 사용합니다.
- Notion의 USD 수동자산은 환율 이력이 연결되기 전 `amount_krw=0`으로 동기화됩니다. 운영 전 최신 환율 적용 정책을 연결해야 합니다.
- TOSS 종목 상세 메타데이터 조회를 아직 사용하지 않으므로 실데이터의 종목 유형은 `UNKNOWN`입니다.
- 사용자 로그인은 포함하지 않았습니다. 개인용 비공개 네트워크 또는 별도 접근 제어가 필요합니다.
- 금융기관별 실제 이자 계산 규칙을 알 수 없는 예적금은 `is_estimated=true` 단순 추정치입니다.

## Recommended Next Steps

1. 개인 Notion의 실제 속성명/타입에 mapping을 맞추고 첫 Full Sync를 검증합니다.
2. 토스증권 허용 IP와 Secret을 설정해 계좌·보유종목·환율 동기화를 검증합니다.
3. 공식 종목 메타데이터 endpoint를 연결해 ETF/개별주식 분류를 채웁니다.
4. 배포 환경에 개인 접근 제어와 매일 Snapshot cron을 추가합니다.
5. 운영 데이터 1개월이 쌓인 뒤 stale 기준과 anomaly warning 임계값을 조정합니다.

## Official References

- [Notion Data Source API](https://developers.notion.com/reference/retrieve-a-data-source)
- [Notion Webhooks](https://developers.notion.com/reference/webhooks)
- [Notion API 2026-03-11 upgrade guide](https://developers.notion.com/guides/get-started/upgrade-guide-2026-03-11)
- [Toss Securities Open API guide](https://developers.tossinvest.com/docs)
- [Toss Securities OpenAPI schema](https://openapi.tossinvest.com/openapi-docs/latest/openapi.json)
