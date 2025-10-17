# Call Orchestrator - 긴급 알림 시스템

FastAPI + SOLAPI를 사용한 긴급 음성 통화 알림 시스템

## 주요 기능

- 🚨 긴급 알림 자동 전화 발신
- 📞 SOLAPI 음성 메시지 API 연동
- 🔄 담당자 교대 로직 (Primary/Secondary)
- 📊 발신 내역 추적 (SQLite)
- 🎯 DTMF 입력 처리
- 🔁 자동 재시도 메커니즘
- 🌐 **웹 시뮬레이터** - 브라우저에서 실시간 테스트 (NEW!)

## 시스템 구성

### 지원 프로바이더
- SOLAPI (음성 메시지)
- Twilio (음성 통화)
- Vonage (음성 통화)
- Mock (테스트용)

### 기술 스택
- **Backend**: FastAPI
- **Database**: SQLite
- **SMS/Voice**: SOLAPI, Twilio, Vonage
- **Language**: Python 3.11+

## 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/call-orchestrator.git
cd call-orchestrator
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가:

```env
# 기본 설정
APP_HOST=0.0.0.0
APP_PORT=8001
PUBLIC_BASE_URL=http://localhost:8001

# 프로바이더 선택 (solapi, twilio, vonage, mock)
VOICE_PROVIDER=solapi

# 연락처 정보
PRIMARY_CONTACT=01000000000
SECONDARY_CONTACT=01000000000

# SOLAPI 설정
SOLAPI_API_KEY=your_api_key
SOLAPI_API_SECRET=your_api_secret
SOLAPI_FROM_NUMBER=01098942273

# Twilio 설정 (선택)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Vonage 설정 (선택)
VONAGE_API_KEY=your_api_key
VONAGE_API_SECRET=your_api_secret
VONAGE_FROM_NUMBER=14155550100
```

## 🌐 웹 시뮬레이터 (NEW!)

### 빠른 시작

```bash
# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8001

# 브라우저 접속
http://localhost:8001/static/simulator_experience.html
```

### 주요 기능
- ✅ 웹 UI에서 담당자 정보 입력
- ✅ **순차적 에스컬레이션**: 정담당자 → 부담당자 → 정담당자(2차) → 부담당자(2차)
- ✅ **실시간 로그**: 전화 발신 상태를 실시간으로 표시 (발신중 → 성공/실패)
- ✅ **자동 종료**: 한 명이라도 전화를 받으면 즉시 종료
- ✅ 7단계 워크플로우 시각화
- ✅ 실제 Twilio 전화 발신 (메시지 2번 반복)
- ✅ 외부 접속 지원 (ngrok)

### 외부 공개 (ngrok)

```bash
# 터미널 1
uvicorn app.main:app --host 0.0.0.0 --port 8001

# 터미널 2
ngrok http 8001

# 출력된 URL로 접속
https://abc123.ngrok.io/static/simulator_experience.html
```

### 📚 상세 가이드
- [SIMULATOR_GUIDE.md](SIMULATOR_GUIDE.md) - 시뮬레이터 전체 가이드
- [ESCALATION_LOGIC.md](ESCALATION_LOGIC.md) - 순차적 에스컬레이션 로직 설명
- [NGROK_SETUP_GUIDE.md](NGROK_SETUP_GUIDE.md) - ngrok 설치 및 설정

### 🎯 모드 자동 전환
시스템은 `PUBLIC_BASE_URL`을 보고 자동으로 모드를 선택합니다:
- **로컬 모드** (`localhost`): TwiML 직접 전달 → ngrok 불필요
- **외부 모드** (`ngrok.io`): URL 방식 → 자동 에스컬레이션 가능

---

## 사용 방법

### 1. 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 2. 긴급 알림 발송
```bash
# API 호출
curl -X POST "http://localhost:8001/webhook/start" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_summary": "긴급 알림",
    "tts_text": "긴급 상황입니다. 확인 부탁드립니다."
  }'
```

### 3. API 엔드포인트

#### 긴급 알림 발송
```http
POST /webhook/start
Content-Type: application/json

{
  "incident_summary": "알림 제목",
  "tts_text": "음성 메시지 내용"
}
```

#### 상태 확인
```http
GET /webhook/incident/{incident_id}
```

#### 헬스 체크
```http
GET /health
```

## SOLAPI 설정

### 1. SOLAPI 계정 생성
- [SOLAPI 콘솔](https://console.solapi.com)에서 계정 생성
- API 키 발급
- 발신번호 등록

### 2. 발신번호 등록
- SOLAPI 콘솔 → 발신번호 관리
- 사용할 발신번호 등록 및 인증

### 3. 포인트 충전
- 음성 메시지 1건당 200포인트 필요
- SOLAPI 콘솔에서 충전

### 4. 환경 변수 설정
```bash
export VOICE_PROVIDER=solapi
export SOLAPI_API_KEY=your_api_key
export SOLAPI_API_SECRET=your_api_secret
export SOLAPI_FROM_NUMBER=01098942273
```

## 테스트

### SOLAPI 테스트
```bash
# REST API 직접 호출 테스트
python solapi_direct_test.py

# SDK 테스트
python solapi_sdk_test.py

# 기본 테스트
python solapi_test.py
```

### 연동 테스트
```bash
# pytest 실행
pytest tests/

# 스모크 테스트
python -m pytest tests/test_smoke.py
```

## 프로젝트 구조

```
call-orchestrator/
├── app/
│   ├── main.py                 # FastAPI 애플리케이션
│   ├── config.py               # 설정 관리
│   ├── models.py               # 데이터 모델
│   ├── db.py                   # 데이터베이스
│   ├── providers/              # 프로바이더
│   │   ├── base.py
│   │   ├── solapi_provider.py
│   │   ├── twilio_provider.py
│   │   └── vonage_provider.py
│   ├── routers/                # API 라우터
│   │   ├── health.py
│   │   └── webhook.py
│   └── services/               # 비즈니스 로직
│       ├── escalation.py
│       └── tts_text.py
├── tests/                      # 테스트
├── SOLAPI_GUIDE.md            # SOLAPI 가이드
├── SOLAPI_RULES.md            # 개발 규칙
├── requirements.txt           # 패키지 목록
└── README.md                  # 이 파일
```

## 문제 해결

### SOLAPI 관련

#### 메시지가 짤리는 경우
- `replyRange`를 3 이상으로 설정
- `headerMessage`, `tailMessage` 제거로 단순화

#### 발신 실패
- 발신번호 SOLAPI 등록 확인
- 발신번호 ≠ 수신번호 확인
- 포인트 잔액 확인

#### 인증 오류
- API 키/시크릿 정확성 확인
- ISO 8601 날짜 형식 확인
- hexdigest() 서명 생성 방식 확인

자세한 내용은 [SOLAPI_RULES.md](SOLAPI_RULES.md) 참고

## 문서

- [SOLAPI 사용 가이드](SOLAPI_GUIDE.md)
- [SOLAPI 개발 규칙](SOLAPI_RULES.md)
- [구현 완료 보고서](SOLAPI_IMPLEMENTATION_SUMMARY.md)
- [인수인계 문서](FINAL_HANDOVER_REPORT.md)

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여

이슈 및 PR은 언제든 환영합니다!

## 참고 자료

- [SOLAPI 공식 문서](https://developers.solapi.com)
- [Twilio 문서](https://www.twilio.com/docs)
- [Vonage 문서](https://developer.vonage.com)
- [FastAPI 문서](https://fastapi.tiangolo.com)