# 변경 로그 - 순차적 에스컬레이션 및 실시간 로그 (2025-01-17)

## 주요 변경 사항

### 1. 순차적 에스컬레이션 로직 구현 ✅

**이전**: 정담당자와 부담당자에게 **동시 발신**
```
정담당자 ━━━━━━━━┓
                 ┣━━━> 동시 발신 (❌ 잘못됨)
부담당자 ━━━━━━━━┛
```

**현재**: **순차적 에스컬레이션** (정 → 부 → 정 → 부)
```
정담당자(1차) ━━━> ❌ 받지 않음
                  ↓
부담당자(1차) ━━━> ❌ 받지 않음
                  ↓
정담당자(2차) ━━━> ❌ 받지 않음
                  ↓
부담당자(2차) ━━━> ✅ 전화 받음 → 즉시 종료!
```

**특징**:
- 한 명이라도 전화를 받으면 **즉시 종료**
- 최대 4회 시도 (정-부-정-부)
- 각 시도마다 15초 타임아웃
- 실시간 통화 상태 모니터링

### 2. 실시간 로그 업데이트 구현 ✅

**이전**: 모든 로그를 한 번에 출력
```javascript
// 발신 완료 후 결과를 한 번에 표시
pushLog("✅ 정담당자: 발신 완료");
pushLog("✅ 부담당자: 발신 완료");
```

**현재**: SSE(Server-Sent Events)로 실시간 업데이트
```
[Step 10] 📞 정담당자 홍길동 (010-1234-5678): 발신중...
          ↓ (실시간 업데이트)
[Step 10] ✅ 홍길동: 전화 연결 성공! (통화시간: 12초)
```

**구현 방식**:
- Backend: FastAPI `StreamingResponse` 사용
- Frontend: Fetch API Stream 방식
- 이벤트 타입:
  - `call_start`: 발신 시작
  - `call_initiated`: 호출 시작
  - `call_answered`: 연결 성공
  - `call_failed`: 연결 실패
  - `escalation_complete`: 에스컬레이션 성공
  - `escalation_failed`: 에스컬레이션 실패

### 3. 메시지 2번 반복 (이미 구현됨) ✅

TwiML 구조:
```xml
<Response>
  <Say>메시지 내용</Say>
  <Pause length="1"/>
  <Say>메시지 내용</Say>  <!-- 2번째 반복 -->
  <Pause length="1"/>
  <Say>메시지 전달이 완료되었습니다.</Say>
  <Hangup/>
</Response>
```

## 수정된 파일

### 1. `app/routers/simulator.py` (완전히 재작성)

**변경 내용**:
- 동시 발신 → 순차 발신으로 변경
- `escalate_with_status()` 함수 추가: 순차 에스컬레이션 로직
- `check_call_status()` 함수 추가: Twilio 통화 상태 폴링
- SSE 스트리밍 응답 구현
- 실시간 이벤트 전송 (`call_start`, `call_answered`, `call_failed` 등)

**주요 함수**:
```python
async def check_call_status(client, call_sid, max_wait=30):
    """Twilio 통화 상태를 폴링하여 최종 결과 확인"""
    # answered | no-answer | busy | failed | timeout

async def escalate_with_status(request):
    """순차적 에스컬레이션 with 실시간 상태 업데이트"""
    # 정 → 부 → 정 → 부 (최대 4회)
    # 한 명이라도 받으면 즉시 종료
```

### 2. `app/static/simulator_experience.html`

**변경 내용**:
- `callRealAPI()` 함수: SSE 스트림 방식으로 변경
- `handleSSEEvent()` 함수 추가: 이벤트별 로그 처리
- `updateLastLog()` 함수 추가: 기존 로그 라인 업데이트
- API 결과 처리 로직 간소화 (SSE로 이미 출력되므로)

**핵심 코드**:
```javascript
// SSE 스트림 읽기
const reader = response.body.getReader();
const decoder = new TextDecoder();

function readStream(){
  reader.read().then(({done, value}) => {
    const text = decoder.decode(value);
    // data: {...} 형식 파싱
    handleSSEEvent(data, callResults);
  });
}
```

### 3. 문서 추가

- `ESCALATION_LOGIC.md`: 에스컬레이션 로직 상세 설명
- `CHANGELOG_20251017_ESCALATION.md`: 이 문서

### 4. README.md 업데이트

- 주요 기능에 "순차적 에스컬레이션" 추가
- 주요 기능에 "실시간 로그" 추가
- `ESCALATION_LOGIC.md` 링크 추가

## 기술 스택

### Backend
- **FastAPI StreamingResponse**: SSE 구현
- **Twilio SDK**: 통화 상태 모니터링
- **asyncio**: 비동기 처리

### Frontend
- **Fetch API Streams**: SSE 수신
- **TextDecoder**: 스트림 디코딩
- **Dynamic DOM Update**: 실시간 로그 업데이트

## 테스트 방법

### 1. 로컬 테스트

```bash
cd "D:\9. Cursor_AI\AI_PG\AI_PlayGround"

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 브라우저 접속
http://localhost:8001/static/simulator_experience.html
```

### 2. 테스트 시나리오

#### 시나리오 A: 정담당자가 바로 받는 경우
1. 정담당자 전화번호 입력
2. 시뮬레이션 시작
3. 예상 결과:
   ```
   📞 정담당자 홍길동: 발신중...
   ✅ 홍길동: 전화 연결 성공!
   🎉 에스컬레이션 성공 (총 1회 시도)
   ```

#### 시나리오 B: 정담당자 불응, 부담당자 응답
1. 정담당자, 부담당자 전화번호 입력
2. 정담당자는 전화를 받지 않음
3. 예상 결과:
   ```
   📞 정담당자 홍길동: 발신중...
   ❌ 홍길동: 전화 연결 실패 (no-answer)
   📞 부담당자 김철수: 발신중...
   ✅ 김철수: 전화 연결 성공!
   🎉 에스컬레이션 성공 (총 2회 시도)
   ```

#### 시나리오 C: 모두 불응 (4회 시도)
1. 모든 전화를 받지 않음
2. 예상 결과:
   ```
   📞 정담당자 홍길동: 발신중...
   ❌ 홍길동: 전화 연결 실패
   📞 부담당자 김철수: 발신중...
   ❌ 김철수: 전화 연결 실패
   📞 정담당자(2차) 홍길동: 발신중...
   ❌ 홍길동: 전화 연결 실패
   📞 부담당자(2차) 김철수: 발신중...
   ❌ 김철수: 전화 연결 실패
   ⚠️ 에스컬레이션 실패 (총 4회 시도)
   ```

### 3. 외부 접속 테스트 (ngrok)

```bash
# 터미널 1: 서버
uvicorn app.main:app --host 0.0.0.0 --port 8001

# 터미널 2: ngrok
ngrok http 8001

# 출력된 URL로 접속
https://abc123.ngrok.io/static/simulator_experience.html
```

## 알려진 제한사항

### 1. Twilio Trial 계정
- Verified Caller IDs만 사용 가능
- 매번 Verification 메시지 재생

### 2. 통화 상태 확인 지연
- Twilio API 폴링 방식 (1초 간격)
- 실제 전화 받은 시점과 로그 업데이트 사이 약 1-2초 지연

### 3. 네트워크 지연
- SSE 스트림 지연 가능
- 모바일 네트워크에서 더 느릴 수 있음

## 성능 개선 가능 영역

### 1. WebSocket 사용
현재: SSE (단방향)
개선: WebSocket (양방향) - 더 빠른 응답

### 2. Twilio Status Callback 활용
현재: 폴링 방식
개선: Webhook 콜백 방식 (ngrok 필요)

### 3. Redis/DB 상태 저장
현재: 메모리 (서버 재시작 시 손실)
개선: 영구 저장

## 비용 분석

### Twilio 통화 비용 (한국)
- 통화당: $0.013/분
- 4회 시도 (모두 실패): 약 $0.05 (65원)
- 1회 성공: $0.013 (16원)
- 평균 (2회 시도): $0.026 (33원)

### 월간 예상 비용
- 일 10회 시뮬레이션: 약 $3.9/월 (5,070원)
- 일 100회 시뮬레이션: 약 $39/월 (50,700원)

## 다음 단계 (선택사항)

1. **WebSocket 마이그레이션**: 더 빠른 실시간 업데이트
2. **상태 지속성**: Redis 또는 DB에 에스컬레이션 상태 저장
3. **통계 대시보드**: 성공률, 평균 시도 횟수 등 시각화
4. **알림 히스토리**: 과거 발신 내역 조회
5. **담당자 그룹**: 3명 이상의 담당자 지원

## 참고 자료

- [Twilio Call Status](https://www.twilio.com/docs/voice/api/call-resource#call-status-values)
- [MDN Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)

## 완료 체크리스트

- [x] 순차적 에스컬레이션 로직 구현
- [x] 실시간 로그 업데이트 (SSE)
- [x] 메시지 2번 반복 (이미 구현됨)
- [x] 자동 종료 (한 명이라도 응답 시)
- [x] 최대 4회 시도 (정-부-정-부)
- [x] 통화 상태 실시간 모니터링
- [x] 문서 작성 (ESCALATION_LOGIC.md)
- [x] README 업데이트
- [x] 포트 8000 → 8001 변경

---

**구현 완료 일시**: 2025-01-17
**구현자**: AI Assistant
**테스트 상태**: 로컬 테스트 대기

