# HTML 시뮬레이터 사용 가이드

## 개요

웹 브라우저에서 담당자 정보를 입력하고 실제 Twilio 음성 전화를 발신할 수 있는 시뮬레이터입니다.

## 구성 요소

### 1. Backend API
- **엔드포인트**: `POST /simulator/call`
- **파일**: `app/routers/simulator.py`
- **기능**: 입력받은 전화번호로 직접 전화 발신

### 2. Frontend Web UI
- **URL**: `http://localhost:8001/static/simulator_experience.html`
- **파일**: `app/static/simulator_experience.html`
- **기능**: 담당자 정보 입력 및 시뮬레이션 시각화

## 실행 방법

### 로컬 테스트

```bash
# 1. 서버 실행
cd "D:\9. Cursor_AI\AI_PG\AI_PlayGround"
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 2. 브라우저 접속
http://localhost:8001/static/simulator_experience.html
```

### 외부 접속 (ngrok 사용)

```bash
# 터미널 1: FastAPI 서버
uvicorn app.main:app --host 0.0.0.0 --port 8001

# 터미널 2: ngrok으로 공개
ngrok http 8001

# ngrok 출력 확인
# Forwarding: https://abc123.ngrok.io -> http://localhost:8001

# 브라우저 접속
https://abc123.ngrok.io/static/simulator_experience.html
```

## 사용 방법

### 1. 웹 페이지 접속

브라우저에서 `http://localhost:8001/static/simulator_experience.html` 접속

### 2. 담당자 정보 입력

**정담당자 (필수)**:
- 성명: 홍길동
- 휴대폰: 010-1234-5678

**부담당자 (선택)**:
- 성명: 김철수
- 휴대폰: 010-9876-5432

### 3. 시뮬레이션 시작

- "시뮬레이션 시작" 버튼 클릭
- 실시간 로그에서 진행 상황 확인
- **실제로 입력한 번호로 전화가 발신됩니다!**

## 주요 기능

### 1. 동적 전화번호
- 환경변수의 담당자 정보 무시
- 웹에서 입력받은 번호로 직접 전화

### 2. 전화번호 형식 자동 변환
- 입력: `010-1234-5678`
- 변환: `+821012345678`
- Twilio 국제 형식으로 자동 변환

### 3. 실시간 시뮬레이션
- 7단계 워크플로우 시각화
- API 호출 및 응답 로그
- 전화 발신 결과 실시간 표시

### 4. 외부 접속 지원
- CORS 전체 허용
- ngrok으로 공개 URL 생성
- 인터넷에서 누구나 접속 가능

## API 명세

### POST /simulator/call

**Request**:
```json
{
  "primary_name": "홍길동",
  "primary_phone": "+821012345678",
  "secondary_name": "김철수",
  "secondary_phone": "+821098765432",
  "incident_summary": "단위DB 서버 다운 Critical",
  "tts_text": "[긴급] 단위DB 서버에 Critical 장애가 발생했습니다."
}
```

**Response**:
```json
{
  "success": true,
  "provider": "twilio",
  "incident_id": 0,
  "calls": [
    {
      "role": "primary",
      "name": "홍길동",
      "phone": "+821012345678",
      "call_id": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "status": "initiated"
    },
    {
      "role": "secondary",
      "name": "김철수",
      "phone": "+821098765432",
      "call_id": "CAyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
      "status": "initiated"
    }
  ]
}
```

## 기술 스택

### Backend
- **FastAPI**: REST API 서버
- **Twilio SDK**: 음성 전화 발신
- **Static Files**: HTML/CSS/JS 서빙
- **CORS**: 외부 접속 허용

### Frontend
- **Vanilla JavaScript**: 프레임워크 없이 구현
- **Fetch API**: RESTful API 호출
- **CSS3**: 그라데이션 및 애니메이션

## 보안 고려사항

### 현재 설정 (데모용)
- ✅ CORS: 모든 도메인 허용 (`allow_origins=["*"]`)
- ✅ 인증: 없음
- ✅ 공개 접속: ngrok으로 가능

### 프로덕션 환경 권장
- 🔒 CORS: 특정 도메인만 허용
- 🔒 인증: JWT 토큰 또는 API 키
- 🔒 Rate Limiting: 요청 제한
- 🔒 HTTPS: SSL/TLS 인증서

## 트러블슈팅

### 1. "python-multipart" 오류
```bash
pip install python-multipart
```

### 2. 포트 이미 사용 중
```bash
# 포트 확인
netstat -ano | findstr :8001

# 프로세스 종료
taskkill /PID <PID> /F
```

### 3. CORS 오류
- `app/main.py`에서 CORS 설정 확인
- `allow_origins=["*"]` 확인

### 4. Static 파일 404
- `app/static` 디렉토리 존재 확인
- `app.mount()` 순서 확인 (라우터 등록 후)

## 파일 구조

```
AI_PlayGround/
├── app/
│   ├── main.py                      # CORS, Static 마운트
│   ├── routers/
│   │   └── simulator.py             # /simulator/call API
│   └── static/
│       └── simulator_experience.html # 웹 UI
├── requirements.txt                  # python-multipart 추가
└── SIMULATOR_GUIDE.md               # 이 문서
```

## 데모 시나리오

### 시나리오 1: 정담당자만
1. 정담당자 정보 입력
2. 시뮬레이션 시작
3. 정담당자에게만 전화 발신

### 시나리오 2: 정담당자 + 부담당자
1. 정담당자와 부담당자 정보 모두 입력
2. 시뮬레이션 시작
3. 두 담당자 모두에게 전화 발신 (순차적)

### 시나리오 3: 외부 참여자
1. ngrok으로 공개 URL 생성
2. URL을 외부 참여자에게 공유
3. 참여자가 자신의 번호 입력
4. 실제로 참여자 전화로 발신

## 비용 안내

- Twilio Trial Account: Verified 번호만 가능
- Twilio Paid Account: 모든 번호 가능
- 통화당 비용: 약 $0.013/분 (한국)
- 시뮬레이터 1회: 약 16원 (4통화 기준)

## 라이브 데모

시뮬레이터를 실제 운영 환경에 배포하려면:

1. **클라우드 서버 배포** (AWS, GCP, Azure)
2. **도메인 연결** (예: https://simulator.shinhan-ds.com)
3. **SSL 인증서** (Let's Encrypt)
4. **모니터링** (로그, 메트릭)

## 문의

- GitHub: https://github.com/aibkinfois-cmyk/AI_PlayGround_20251017
- 문제 보고: GitHub Issues

