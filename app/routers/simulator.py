import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from twilio.rest import Client
import json

from app.config import settings

router = APIRouter(prefix="/simulator", tags=["simulator"])


class SimulatorCallRequest(BaseModel):
    primary_name: str
    primary_phone: str
    secondary_name: str | None = None
    secondary_phone: str | None = None
    incident_summary: str
    tts_text: str


def create_twiml(message: str) -> str:
    """TwiML 생성 - 메시지 2번 반복"""
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon">{message}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">{message}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">메시지 전달이 완료되었습니다. 감사합니다.</Say>
  <Hangup/>
</Response>"""


async def check_call_status(client: Client, call_sid: str, max_wait: int = 30) -> dict:
    """
    Twilio 통화 상태를 폴링하여 최종 결과 확인
    
    Returns:
        {"status": "answered" | "no-answer" | "busy" | "failed" | "canceled", "duration": int}
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            call = client.calls(call_sid).fetch()
            status = call.status
            
            # 통화 상태별 처리
            if status == "completed":
                # duration 체크 (문자열일 수도 있음)
                duration = 0
                try:
                    if call.duration:
                        duration = int(call.duration)
                except (ValueError, TypeError):
                    duration = 0
                
                # duration이 5초 이상이면 받은 것으로 간주
                # (메시지를 2번 반복하므로 최소 10초 이상 통화)
                if duration >= 5:
                    return {"status": "answered", "duration": duration}
                else:
                    return {"status": "no-answer", "duration": 0}
            
            elif status == "busy":
                return {"status": "busy", "duration": 0}
            
            elif status in ["failed", "canceled"]:
                return {"status": status, "duration": 0}
            
            # 아직 진행 중이면 대기
            elif status in ["queued", "ringing", "in-progress"]:
                await asyncio.sleep(1)
                continue
                
        except Exception as e:
            print(f"Error checking call status: {e}")
            return {"status": "error", "duration": 0}
    
    # 타임아웃
    return {"status": "timeout", "duration": 0}


async def escalate_with_status(request: SimulatorCallRequest):
    """
    순차적 에스컬레이션 로직 with 실시간 상태 업데이트
    정 → 부 → 정 → 부 (최대 4회)
    한 명이라도 받으면 즉시 종료
    """
    def get_timestamp():
        """한국 시간 타임스탬프 생성"""
        return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
    
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    twiml = create_twiml(request.tts_text)
    
    # 담당자 리스트 (정-부-정-부)
    contacts = [
        {"name": request.primary_name, "phone": request.primary_phone, "role": "정담당자"},
        {"name": request.secondary_name, "phone": request.secondary_phone, "role": "부담당자"},
        {"name": request.primary_name, "phone": request.primary_phone, "role": "정담당자(2차)"},
        {"name": request.secondary_name, "phone": request.secondary_phone, "role": "부담당자(2차)"},
    ]
    
    # 부담당자가 없으면 정담당자만 2회 시도
    if not request.secondary_name or not request.secondary_phone:
        contacts = [
            {"name": request.primary_name, "phone": request.primary_phone, "role": "정담당자"},
            {"name": request.primary_name, "phone": request.primary_phone, "role": "정담당자(2차)"},
        ]
    
    for idx, contact in enumerate(contacts, 1):
        # 발신 시작 이벤트
        yield f"data: {json.dumps({'type': 'call_start', 'attempt': idx, 'name': contact['name'], 'phone': contact['phone'], 'role': contact['role'], 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)
        
        try:
            # 전화 발신
            call = client.calls.create(
                to=contact['phone'],
                from_=settings.twilio_from_number,
                twiml=twiml,
                timeout=settings.call_timeout_seconds
            )
            
            call_sid = call.sid
            
            # 발신 완료 (통화 대기 중)
            yield f"data: {json.dumps({'type': 'call_initiated', 'attempt': idx, 'call_id': call_sid, 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.5)
            
            # 통화 상태 확인 (최대 30초 대기)
            result = await check_call_status(client, call_sid, max_wait=30)
            
            # 결과 전송
            if result['status'] == 'answered':
                yield f"data: {json.dumps({'type': 'call_answered', 'attempt': idx, 'name': contact['name'], 'duration': result['duration'], 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'escalation_complete', 'total_attempts': idx, 'answered_by': contact['name'], 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
                return  # 성공 시 즉시 종료
            else:
                # 실패 (no-answer, busy, failed, timeout)
                yield f"data: {json.dumps({'type': 'call_failed', 'attempt': idx, 'name': contact['name'], 'reason': result['status'], 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(1)
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'call_error', 'attempt': idx, 'name': contact['name'], 'error': str(e), 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(1)
    
    # 모든 시도 실패
    yield f"data: {json.dumps({'type': 'escalation_failed', 'total_attempts': len(contacts), 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"


@router.post("/call")
async def simulator_call(request: SimulatorCallRequest):
    """
    실시간 순차 에스컬레이션 with SSE (Server-Sent Events)
    
    정담당자 → 부담당자 → 정담당자(2차) → 부담당자(2차)
    한 명이라도 받으면 즉시 종료
    """
    async def event_generator():
        try:
            async for event in escalate_with_status(request):
                yield event
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx buffering 방지
        }
    )
