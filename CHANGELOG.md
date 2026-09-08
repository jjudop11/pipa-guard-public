# 변경 기록

## 0.1.2 — 2026-09-08

- 실제 Claude Code 합성 시나리오에서 발견한 AES 비밀번호 보조 메서드 미검출 수정
- `Cipher` 결과가 반환값에 도달한 메서드와 비밀번호 저장 호출만 연결하는 얕은 전파 추가
- 위반 V071·적법 C094와 실제 `Write` PreToolUse 차단 계약 추가
- GitHub Actions를 Node.js 24 기반 버전의 검증된 커밋 SHA로 갱신

## 0.1.1 — 2026-09-08

- README의 사전 차단 범위를 Claude Code `Write`·`Edit`와 Codex `apply_patch`로 명확히 제한
- 모델의 구체적인 재작성은 보장하지 않는다는 경계 명시
- README 수치·예제·설정 8개·별칭 단독 오탐·비식별화·결정성·무의존성·배포 메타데이터를
  검증하는 주장 계약 10건 추가
- Ubuntu에서 Python 3.10·3.12·3.14 CI 검증

## 0.1.0 — 2026-09-07

- 개인정보의 안전성 확보조치 기준에 근거한 활성 규칙 8개와 하위 검사 25개
- Java·Kotlin 저장·HTTP 송수신·로그·API 응답·접속기록·단말 파일 저장 검사
- Claude Code `Write|Edit`와 Codex `apply_patch`의 PreToolUse 차단·PostToolUse 경고
- Claude Code·Codex용 public GitHub 마켓플레이스
- 합성 fixture 163건과 훅·CLI·패키지 계약 33건

실제 코드베이스의 재현율·오탐률이나 전체 법령 준수를 보증하지 않는다.
