# 개발 규칙 및 문제 해결 가이드

## 목적
이 문서는 AI_PlayGround 프로젝트에서 발생했던 모든 오류와 해결 방법을 정리하여 동일한 문제가 재발하지 않도록 합니다.

---

## 1. 파일 인코딩 문제 ⚠️

### 문제
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa4 in position 10
```

### 원인
- `.env` 파일이 UTF-8이 아닌 다른 인코딩(CP949 등)으로 저장됨
- 한글 주석이 깨져서 발생

### 해결 방법
```powershell
# .env 파일을 UTF-8로 재생성
@"
APP_HOST=0.0.0.0
APP_PORT=8001
PUBLIC_BASE_URL=http://localhost:8001
"@ | Out-File -FilePath .env -Encoding UTF8
```

### 예방 규칙
- ✅ `.env` 파일은 **항상 UTF-8 인코딩**으로 저장
- ✅ 한글 주석은 제거하거나 영문으로 작성
- ✅ VSCode에서 저장 시 "UTF-8" 확인

---

## 2. 포트 충돌 문제 ⚠️

### 문제
```
ERROR: [Errno 10048] 각 소켓 주소(프로토콜/네트워크 주소/포트)는 하나만 사용할 수 있습니다
```

### 원인
- 포트 8000 또는 8001이 이미 다른 프로세스에서 사용 중

### 해결 방법
```powershell
# 1. 포트 사용 프로세스 확인
netstat -ano | findstr :8001

# 2. 프로세스 종료 (PID 확인 후)
taskkill /PID [PID] /F

# 3. 또는 모든 Python 프로세스 종료
taskkill /F /IM python.exe
```

### 예방 규칙
- ✅ 서버 실행 전 항상 포트 사용 여부 확인
- ✅ 서버 재시작 시 기존 프로세스 먼저 종료
- ✅ 포트 변경 시 모든 설정 파일 업데이트 (`.env`, 문서)

---

## 3. 누락된 패키지 문제 ⚠️

### 문제
```
RuntimeError: Form data requires "python-multipart" to be installed.
```

### 원인
- FastAPI에서 Form 데이터 파싱 시 필요한 패키지 누락

### 해결 방법
```bash
pip install python-multipart
```

### 예방 규칙
- ✅ `requirements.txt` 업데이트 시 즉시 설치
- ✅ 새로운 기능 추가 시 필요 패키지 확인
- ✅ Form, File 처리 시 python-multipart 필수

---

## 4. Twilio 통화 상태 오판 문제 ⚠️

### 문제
- 전화를 받았는데도 "실패"로 표시됨
- 3번째 시도에서 받았지만 오탐 발생

### 원인
- `answered_by` 필드에 의존했으나, 이 필드는 항상 존재하지 않음
- 통화 시간(`duration`)으로 판정해야 정확함

### 해결 방법
```python
# ❌ 잘못된 방법
if call.answered_by and call.answered_by != "machine_start":
    return {"status": "answered"}

# ✅ 올바른 방법
duration = int(call.duration) if call.duration else 0
if duration >= 5:  # 5초 이상이면 받은 것으로 판정
    return {"status": "answered", "duration": duration}
else:
    return {"status": "no-answer", "duration": 0}
```

### 예방 규칙
- ✅ Twilio 통화 상태는 `duration >= 5초` 기준 사용
- ✅ `answered_by` 필드는 참고용으로만 사용
- ✅ 메시지 2번 반복 시 최소 10초 이상 통화 예상

---

## 5. 부정확한 처리 시간 문제 ⚠️

### 문제
- 총 처리 시간이 4.9초로 표시됨
- 실제 전화 시간은 20초 이상인데 시뮬레이션 delay만 계산

### 원인
- `delay * 7 / 1000` 계산 (시뮬레이션 딜레이만 계산)
- 실제 API 호출 및 통화 시간 미반영

### 해결 방법
```javascript
// ❌ 잘못된 방법
pushLog(`총 처리 시간: ${((delay * 7) / 1000).toFixed(1)}초`);

// ✅ 올바른 방법
let startTime = Date.now();  // 시작 시
// ... 처리 ...
const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);
pushLog(`총 처리 시간: ${elapsedTime}초`);
```

### 예방 규칙
- ✅ 실제 경과 시간은 `Date.now()` 또는 `time.time()` 사용
- ✅ delay 계산식이 아닌 실제 시간 측정
- ✅ Python: `time.time()`, JavaScript: `Date.now()`

---

## 6. 동시 발신 문제 ⚠️

### 문제
- 정담당자와 부담당자에게 동시에 전화 발신
- 순차적이어야 하는데 동시 발신됨

### 원인
- 두 개의 `place_call()` 호출을 연속으로 실행
- 대기 없이 바로 다음 전화 발신

### 해결 방법
```python
# ❌ 잘못된 방법 (동시 발신)
primary_call = client.calls.create(...)
secondary_call = client.calls.create(...)  # 즉시 발신

# ✅ 올바른 방법 (순차 발신)
for idx, contact in enumerate(contacts):
    call = client.calls.create(...)
    result = await check_call_status(client, call.sid)
    
    if result['status'] == 'answered':
        return  # 성공 시 즉시 종료 (다음 사람에게 전화 안 함)
    
    await asyncio.sleep(1)  # 다음 시도 전 대기
```

### 예방 규칙
- ✅ 에스컬레이션은 반드시 순차 처리 (for loop)
- ✅ 한 명이라도 받으면 `return`으로 즉시 종료
- ✅ `break`가 아닌 `return` 사용 (함수 완전 종료)

---

## 7. SSE/스트리밍 응답 문제 ⚠️

### 문제
- EventSource가 POST 요청을 지원하지 않음
- 데이터를 전송하면서 스트리밍 받기 불가

### 해결 방법
```javascript
// ❌ 잘못된 방법
const eventSource = new EventSource(url);  // GET만 지원

// ✅ 올바른 방법
fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
}).then(response => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    function readStream() {
        reader.read().then(({done, value}) => {
            if (done) return;
            const text = decoder.decode(value);
            // SSE 파싱: "data: {...}\n\n"
            handleSSE(text);
            readStream();
        });
    }
    readStream();
});
```

### 예방 규칙
- ✅ POST + SSE는 fetch + body.getReader() 사용
- ✅ EventSource는 GET 전용
- ✅ SSE 형식: `data: {json}\n\n`

---

## 8. PowerShell 명령 문법 ⚠️

### 문제
```
'&&'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램이 아닙니다.
```

### 원인
- Bash 문법(`&&`)을 PowerShell에서 사용

### 해결 방법
```powershell
# ❌ Bash 문법
cd path && command

# ✅ PowerShell 문법
cd path; command
```

### 예방 규칙
- ✅ PowerShell에서는 세미콜론(`;`) 사용
- ✅ 명령 체인: `command1; command2; command3`
- ✅ Windows 환경임을 항상 인지

---

## 9. Git 설정 문제 ⚠️

### 문제
```
fatal: detected dubious ownership in repository
Author identity unknown
```

### 해결 방법
```bash
# 안전한 디렉토리 추가
git config --global --add safe.directory "D:/9. Cursor_AI/AI_PG/AI_PlayGround"

# 사용자 정보 설정
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

### 예방 규칙
- ✅ 새 환경에서는 Git 설정 먼저 확인
- ✅ safe.directory, user.name, user.email 설정
- ✅ 저장소 클론 후 첫 작업 전 설정

---

## 10. Python 스크립트 호환성 ⚠️

### 문제
```
UnicodeEncodeError: 'cp949' codec can't encode character '✅'
EOFError: EOF when reading a line
```

### 해결 방법
```python
# ❌ 잘못된 코드
print("✅ 성공")  # cp949 오류
answer = input("입력: ")  # 비대화형 환경에서 오류

# ✅ 올바른 코드
print("OK - 성공")  # 영문/숫자만 사용
# input() 사용하지 않음
```

### 예방 규칙
- ✅ 유니코드 이모지 사용 금지 (✅❌🎉 등)
- ✅ `input()` 함수 사용 금지
- ✅ Windows 터미널은 cp949 인코딩

---

## 11. 타임스탬프 처리 ⚠️

### 문제
- 서버 시간과 실제 시간이 다름
- UTC와 한국 시간 혼동

### 해결 방법
```python
from datetime import datetime
from zoneinfo import ZoneInfo

# ✅ 한국 시간
timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
```

### 예방 규칙
- ✅ 한국 시간: `ZoneInfo("Asia/Seoul")` 사용
- ✅ Python 3.9+ zoneinfo 모듈 사용
- ✅ UTC 아닌 명확한 타임존 지정

---

## 12. 불필요한 로그 제거 ⚠️

### 문제
- "API 연결 중..." 같은 불필요한 로그
- 사용자가 요청한 로그만 출력해야 함

### 해결 방법
```javascript
// ❌ 불필요한 로그
pushLog(`API 연결 중... (${API_BASE_URL}/simulator/call)`);

// ✅ 필요한 로그만
// (해당 로그 제거)
```

### 예방 규칙
- ✅ 사용자 요청에 없는 로그는 제거
- ✅ 실시간 업데이트 로그만 유지
- ✅ 중간 과정 로그 최소화

---

## 체크리스트

### 개발 시작 전
- [ ] Git 설정 확인 (user.name, user.email, safe.directory)
- [ ] .env 파일 UTF-8 인코딩 확인
- [ ] 필요 패키지 설치 (requirements.txt)
- [ ] 포트 충돌 확인 (netstat)

### 코드 작성 시
- [ ] 유니코드 이모지 사용하지 않음
- [ ] input() 함수 사용하지 않음
- [ ] PowerShell 문법 사용 (세미콜론)
- [ ] 실제 시간 측정 (Date.now() 또는 time.time())

### API 구현 시
- [ ] Twilio duration >= 5초 기준 사용
- [ ] 순차 에스컬레이션 (for loop + return)
- [ ] SSE는 fetch + getReader() 사용
- [ ] 한국 시간 타임스탬프 (ZoneInfo)

### 서버 실행 전
- [ ] 기존 프로세스 종료 확인
- [ ] 포트 번호 확인 (8001)
- [ ] .env 파일 존재 및 내용 확인

### GitHub Push 전
- [ ] 불필요한 파일 제외 (.env, .env.backup)
- [ ] 커밋 메시지 명확히 작성
- [ ] force push 주의 (데이터 손실 위험)

---

## 참고 문서

- [UPDATE_20251017_FIXES.md](UPDATE_20251017_FIXES.md) - 오늘의 수정사항
- [ESCALATION_LOGIC.md](ESCALATION_LOGIC.md) - 에스컬레이션 로직
- [CHANGELOG_20251017_ESCALATION.md](CHANGELOG_20251017_ESCALATION.md) - 변경 로그

---

**마지막 업데이트**: 2025-01-17  
**작성자**: AI Assistant  
**목적**: 동일한 오류 재발 방지

