# ngrok 설정 가이드

## ngrok이란?

localhost를 인터넷에 공개하는 터널링 서비스입니다. 외부 참여자가 웹 시뮬레이터에 접속할 수 있게 해줍니다.

## 설치 방법

### Windows

#### 방법 1: Chocolatey (권장)
```powershell
choco install ngrok
```

#### 방법 2: 직접 다운로드
1. https://ngrok.com/download 방문
2. Windows 버전 다운로드
3. 압축 해제 후 ngrok.exe를 PATH에 추가

#### 방법 3: Scoop
```powershell
scoop install ngrok
```

## 무료 계정 생성 (선택)

ngrok 무료 계정을 만들면 더 긴 세션 시간과 고정 URL을 얻을 수 있습니다:

1. https://dashboard.ngrok.com/signup 회원가입
2. 로그인 후 "Your Authtoken" 확인
3. 터미널에서 인증:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

## 사용 방법

### Step 1: FastAPI 서버 실행

```bash
cd "D:\9. Cursor_AI\AI_PG\AI_PlayGround"
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Step 2: ngrok 실행 (새 터미널)

```bash
ngrok http 8001
```

### Step 3: ngrok URL 확인

터미널에 다음과 같이 표시됩니다:

```
ngrok

Session Status     online
Account            your-email@example.com (Plan: Free)
Version            3.x.x
Region             Japan (jp)
Latency            20ms
Web Interface      http://127.0.0.1:4040
Forwarding         https://abc123.ngrok.io -> http://localhost:8001

Connections        ttl     opn     rt1     rt5     p50     p90
                   0       0       0.00    0.00    0.00    0.00
```

**중요**: `https://abc123.ngrok.io` 부분을 복사하세요!

### Step 4: .env 파일 업데이트

`AI_PlayGround/.env` 파일을 열고:

```env
PUBLIC_BASE_URL=https://abc123.ngrok.io
```

**주의**: URL 끝에 `/` 없이 입력!

### Step 5: 서버 재시작

FastAPI 서버를 재시작하세요 (Ctrl+C 후 다시 실행):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Step 6: 외부 접속 테스트

브라우저에서 접속:

```
https://abc123.ngrok.io/static/simulator_experience.html
```

## 자동/수동 모드 전환

시스템은 자동으로 감지합니다:

### 로컬 모드 (ngrok 없이)
```env
PUBLIC_BASE_URL=http://localhost:8001
```
- ✅ TwiML 직접 전달
- ✅ 빠른 테스트
- ❌ 자동 에스컬레이션 불가
- ❌ 외부 접속 불가

### ngrok 모드 (외부 공개)
```env
PUBLIC_BASE_URL=https://abc123.ngrok.io
```
- ✅ URL 방식
- ✅ 자동 에스컬레이션 가능
- ✅ 외부 접속 가능
- ✅ Status callback 작동

## 트러블슈팅

### 1. "command not found: ngrok"

**해결**: ngrok을 PATH에 추가하거나 전체 경로로 실행:

```bash
# 전체 경로 예시
C:\path\to\ngrok.exe http 8001
```

### 2. "Session Expired"

**원인**: 무료 ngrok은 8시간 후 세션 만료

**해결**: 
- ngrok 재시작
- 새 URL 확인
- .env 업데이트
- 서버 재시작

### 3. "Invalid URL" 오류

**원인**: .env의 URL이 잘못됨

**확인사항**:
- ✅ `https://` 포함
- ✅ 끝에 `/` 없음
- ✅ ngrok 터미널과 일치

### 4. 외부에서 접속 안됨

**체크리스트**:
1. ngrok 실행 중인지 확인
2. .env의 URL이 ngrok URL과 일치하는지 확인
3. 서버 재시작했는지 확인
4. 방화벽 설정 확인

### 5. 전화는 오는데 메시지가 안들림

**원인**: ngrok URL이 .env에 설정되지 않음

**해결**: .env 파일 확인 및 서버 재시작

## ngrok 대시보드

ngrok 실행 중 http://127.0.0.1:4040 접속하면:
- 실시간 요청 확인
- 요청/응답 내용 확인
- 디버깅 정보 확인

## 무료 vs 유료

### 무료 (Free Tier)
- ✅ 1개 동시 세션
- ✅ 8시간 세션 시간
- ❌ URL 매번 변경
- ❌ 속도 제한

### 유료 (Paid)
- ✅ 무제한 세션
- ✅ 고정 도메인 (예: https://yourname.ngrok.io)
- ✅ 빠른 속도
- ✅ 추가 기능

데모/테스트 용도라면 **무료 버전으로 충분**합니다!

## 빠른 시작 체크리스트

- [ ] ngrok 설치
- [ ] FastAPI 서버 실행
- [ ] ngrok 실행 (`ngrok http 8001`)
- [ ] ngrok URL 복사 (예: https://abc123.ngrok.io)
- [ ] .env 파일 수정 (`PUBLIC_BASE_URL=https://abc123.ngrok.io`)
- [ ] 서버 재시작
- [ ] 브라우저 접속 테스트
- [ ] 외부 참여자에게 URL 공유

## 참여자에게 공유할 URL

```
https://abc123.ngrok.io/static/simulator_experience.html
```

이 URL을 참여자에게 공유하면:
1. 웹 브라우저에서 접속
2. 자신의 전화번호 입력
3. 실제로 전화 수신!

## 보안 주의사항

ngrok은 localhost를 인터넷에 노출합니다:
- ⚠️ 민감한 정보 노출 주의
- ⚠️ 테스트/데모 용도로만 사용
- ⚠️ 프로덕션은 클라우드 서버 사용

## 대안

ngrok 대신 사용할 수 있는 서비스:
- **localtunnel**: https://localtunnel.github.io/www/
- **serveo**: https://serveo.net/
- **Cloudflare Tunnel**: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

하지만 ngrok이 가장 안정적이고 사용하기 쉽습니다!

