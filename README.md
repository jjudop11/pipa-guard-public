# pipa-guard

**AI가 개인정보를 위험하게 처리하는 코드를 작성할 때, 일부 위험한 변경을 막거나 경고해 주는 도구입니다.**

Claude Code 또는 Codex에 추가해서 사용합니다. 예를 들어 AI가 비밀번호를 복원할 수 있는 방식으로
저장하려고 하면, 지원하는 코드 작성 경로에서 이를 차단하고 근거 조항과 수정 방향을 알려 줍니다.
설치만으로 모든 개인정보 문제가 해결되거나 법령 준수가 보장되는 것은 아닙니다.

> **배포 상태 — 2026-09-09 확인 기록:** 공개 설치본은 v0.1.2입니다. 추가 검사에서 발견한
> 오탐·미검출 수정은 main 개발 소스에 반영돼 있지만, 고정된 v0.1.2 설치본에는 포함되지 않습니다.
> 아래 설치는 그 수정본을 받는 절차가 아닙니다. 실제 프로젝트에 적용하기 전 개발 담당자와
> [공개 릴리스 기록](https://github.com/jjudop11/pipa-guard-public/releases)을 확인해 주세요.

[준비물](#준비물) · [설치하기](#설치하기) · [작동 확인하기](#작동-확인하기) ·
[프로젝트 설정](#프로젝트-설정) · [문제가 생겼다면](#문제가-생겼다면)

## 무엇을 해 주나요?

- **차단:** 지원 범위에서 위험하다고 강하게 판단한 코드는 파일에 쓰기 전에 막습니다.
- **경고:** 추가 확인이 필요한 경우에는 파일 작성을 막지 않고 이유를 알려 줍니다.
- **근거 안내:** 어떤 규칙에 해당하는지, 관련 조항과 수정 방향을 함께 전달합니다.

비밀번호 처리, 개인정보 저장·전송, 로그·응답 출력 등 일부 코드 형태를 검사합니다.
검사 대상은 **Java·Kotlin 코드**입니다. 화면 디자인이나 일반 문서를 검사하는 도구는 아닙니다.

## 준비물

1. **Claude Code 또는 Codex:** 둘 중 사용하는 도구가 설치되고 로그인돼 있어야 합니다.
   일반 Claude·ChatGPT 웹 대화창에 설치하는 확장 기능은 아닙니다.
2. **Python 3.10 이상:** 검사 프로그램을 실행합니다. 아래 명령에서 `python3`를 찾을 수 있어야 합니다.
3. **Git과 인터넷 연결:** 공개 저장소에서 플러그인을 내려받을 때 필요합니다.
   검사 엔진 자체는 네트워크나 AI 모델을 호출하지 않지만, Claude Code·Codex 사용은 별개입니다.

아래 안내는 **macOS·Linux 터미널 기준**입니다. 터미널은 명령어를 입력하는 창입니다.
Windows 사용자는 같은 명령을 그대로 실행하기 전에 개발 담당자와 실행 환경을 확인해 주세요.

터미널에 한 줄씩 입력합니다.

```bash
python3 --version
git --version
```

Python은 `Python 3.10...` 이상, Git은 `git version ...`처럼 버전이 표시되면 됩니다.
사용하는 도구도 `claude --version` 또는 `codex --version`으로 확인합니다.
명령을 찾을 수 없다면 플러그인 설치보다 해당 프로그램의 설치를 먼저 해결해야 합니다.

설치가 필요하면 [Python 다운로드](https://www.python.org/downloads/),
[Claude Code 설치 안내](https://code.claude.com/docs/en/setup),
[Codex 시작 안내](https://learn.chatgpt.com/docs/quickstart)를 참고하세요.
회사 컴퓨터에서 설치 권한이 없다면 관리자에게 요청하고 권한 제한을 우회하지 마세요.

## 설치하기

**Claude Code와 Codex 중 사용하는 쪽만 따라 하세요.** 아래 명령은 AI 대화창이 아니라
터미널에 입력합니다. 이 문서에서 “마켓플레이스”는 플러그인을 내려받을 저장소 목록을 뜻합니다.
pipa-guard는 별도 공개 GitHub 저장소를 등록하는 방식이며, 공식 추천 디렉터리 등록을 뜻하지 않습니다.

### Claude Code를 사용한다면

터미널에서 다음 두 줄을 순서대로 실행합니다. 저장소를 등록한 뒤 플러그인을 설치하는 명령입니다.

```bash
claude plugin marketplace add https://github.com/jjudop11/pipa-guard-public.git
claude plugin install pipa-guard@pipa-guard-public --scope user
```

`--scope user`는 이 컴퓨터의 내 Claude Code 사용자 설정에 설치한다는 뜻입니다.
완료 후 Claude Code를 새로 시작하고, **대화 입력창에** `/plugin`을 입력해 설치 목록에서
pipa-guard의 활성화 상태를 확인하세요. 비활성화돼 있다면 해당 항목을 활성화합니다.
프로젝트 신뢰나 실행 승인을 묻는 경우 내용을 검토한 뒤 승인합니다.

설치 범위와 관리 방법은 [Claude Code 공식 플러그인 안내](https://code.claude.com/docs/en/discover-plugins)를
참고할 수 있습니다.

### Codex를 사용한다면

터미널에서 다음 두 줄을 순서대로 실행합니다.

```bash
codex plugin marketplace add jjudop11/pipa-guard-public
codex plugin add pipa-guard@pipa-guard-public
```

완료 후 Codex를 새로 시작합니다. **Codex 대화 입력창에** `/plugins`를 입력해 설치 항목을 확인하고,
`/hooks`에서 pipa-guard의 검사 명령을 검토한 뒤 신뢰를 승인하세요.
“훅”은 AI의 작업 전후에 실행되는 검사입니다. **설치와 훅 신뢰 승인은 별개**입니다.
메뉴가 없거나 조직 정책으로 사용할 수 없다면 임의로 보안 설정을 끄지 말고 담당자에게 확인하세요.

관련 설명은 [OpenAI 공식 플러그인 안내](https://learn.chatgpt.com/docs/plugins)와
[훅 신뢰 안내](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks)에 있습니다.
CLI 명령 형식은 로컬 도구의 `codex plugin --help`에서도 확인할 수 있습니다.

## 작동 확인하기

**실제 프로젝트가 아닌 비어 있는 연습 폴더**에서 확인하세요. 실제 개인정보는 필요 없습니다.

터미널에서 다른 파일이 없는 새 폴더를 만듭니다. 같은 이름의 폴더가 이미 있으면 다른 이름을 사용하세요.

```bash
mkdir pipa-guard-demo
cd pipa-guard-demo
```

이 폴더에서 `claude` 또는 `codex`를 실행합니다. 설치 목록과 Codex의 훅 신뢰 상태를 확인한 다음,
아래 요청을 **AI 대화 입력창**에 붙여 넣습니다.

```text
플러그인 작동 확인을 위한 합성 테스트입니다. 실제 서비스 코드는 아닙니다.
아래 내용을 GuardDemo.java에 그대로 작성해 주세요.
Claude Code는 Write, Codex는 apply_patch만 사용하고 Bash 등 다른 쓰기 도구는 쓰지 마세요.
플러그인이 차단하면 다른 방법으로 저장하거나 코드를 고치지 말고 차단 메시지만 알려 주세요.

class GuardDemo {
    private String password;
    public void save(String rawPassword, javax.crypto.Cipher cipher) throws Exception {
        this.password = new String(cipher.doFinal(rawPassword.getBytes()));
    }
}
```

정상적으로 해당 편집을 시도하고 훅이 실행되면 `K-ENC-002/two-way`, `deny` 또는 차단 안내가
표시되고 **GuardDemo.java가 생성되지 않아야 합니다.** 이 코드는 안전한 구현 예제가 아니라
검사 작동을 확인하려는 의도적인 위반 예제입니다.

AI가 편집을 시도하지 않거나 다른 코드를 만들면 테스트가 성립하지 않습니다. 파일이 없다는 이유만으로
설치 성공으로 판단하지 말고 **실제 도구 실행과 플러그인 차단 메시지**를 함께 확인하세요.
이 한 번의 성공은 모든 규칙이 정확하다는 보증이 아닙니다. 확인이 끝나면 연습 폴더를 닫아 두세요.

## 프로젝트 설정

설정 파일이 없어도 기본 검사를 시작할 수 있습니다. 다만 **설치 완료와 프로젝트 설정 완료는 다릅니다.**
개인정보가 누구의 것인지, 어디에 저장되는지, 어떤 로그가 필요한지는 코드만으로 알 수 없습니다.

실제 프로젝트 적용 전에는 개발·보안 담당자와 `.pipa.json` 설정을 함께 정하세요.
이 파일은 검사에 필요한 프로젝트 상황을 알려 주는 파일입니다.

- 처음 사용하는 사람: 설치와 연습 폴더 테스트까지 진행합니다.
- 개발·보안 담당자: 실제 저장·전송 환경과 출력 목적을 확인하고 설정을 작성합니다.
- 기존 설정이 있는 프로젝트: 덮어쓰지 말고 현재 설정부터 검토합니다.

**경고를 없애려고 “내부망”, “암호화 예외”, “검사 제외” 등을 임의로 지정하면 안 됩니다.**
아래 개발자용 설정 예제는 양식 설명용이지 모든 프로젝트에 적합한 기본 설정이 아닙니다.

## 어디까지 보호하나요?

Claude Code의 `Write`·`Edit`와 Codex의 `apply_patch`가 만드는 Java·Kotlin 변경이 대상입니다.
Bash 등 다른 파일 쓰기 경로는 사전 차단 범위 밖입니다. 수동 편집이나 이미 저장된 모든 파일을
설치 즉시 자동 검사하는 것도 아닙니다.

차단 뒤 AI가 수정 방법을 선택하므로 항상 같은 재작성을 보장하지 않는다는 점에 주의해 주세요.
오탐과 미검출이 생길 수 있고, 코드 밖 운영 환경이나 전체 법률 준수를 보증하지 않습니다.
플러그인의 차단·경고는 담당자의 검토와 함께 활용하세요.

## 문제가 생겼다면

| 보이는 상황 | 확인할 것 |
|---|---|
| `command not found` / 명령을 찾을 수 없음 | Python·Git·사용 중인 도구가 설치됐는지 확인하고 터미널을 다시 엽니다. |
| `plugin` 명령이나 메뉴가 없음 | 사용 중인 도구 버전과 조직의 플러그인 허용 정책을 담당자에게 확인합니다. |
| 설치됐는데 차단되지 않음 | 새 대화인지, 플러그인이 활성화됐는지, Codex 훅 신뢰를 승인했는지, 지원 도구가 실행됐는지 확인합니다. |
| 검사하지 못했다는 메시지 | 정상 통과가 아닙니다. Python 실행과 플러그인 설치 경로를 확인합니다. |
| 예상과 다른 차단·경고 | 우회하거나 예외부터 추가하지 말고, 규칙 번호와 개인정보를 가린 메시지를 개발 담당자에게 전달합니다. |

설치에 성공해도 로컬 개발본의 수정이 설치된 캐시에 자동 반영되지는 않습니다.
업데이트 후에도 새 대화와 작동 확인이 필요합니다. 도움을 요청할 때 실제 개인정보·비밀번호·키를
공개 이슈나 화면 캡처에 포함하지 마세요.

## 개발자용 상세 안내

아래를 펼치면 판정 원리, 소스 직접 실행, 설정 예제, 규칙 목록과 테스트 근거를 볼 수 있습니다.
처음 설치하는 사람은 위 안내부터 따라 하면 됩니다.

<details>
<summary>판정 원리·고급 설정·검증 기록 펼치기</summary>

## 판정 방식

**필드명만으로는 절대 차단하지 않는다.** 차단은 세 조건이 모두 성립할 때만 한다.

1. 개인정보 후보 — 식별자가 사전에 등재된 항목과 **정규화 후 완전 일치**한다
   (소문자화 + `_` 제거, 접두어 재귀 제거). 부분 문자열 일치는 하지 않는다.
   그래서 `orderNo`·`merchantNo`는 절대 매칭되지 않는다.
2. 보호 대상 sink 도달 — 저장·전송·로그 등 조항이 규율하는 지점에 값이 닿는다.
3. 보호 장치 부재 — 조항이 요구하는 조치가 그 경로에 없다.

이름은 **후보**를 고를 뿐이고, 판정은 구조가 한다. 지금 구현된 구조 신호는 파일 범위 얕은 값
전파(상수·팩토리 반환값을 따라가되 지역 암호값은 메서드 범위로 분리한다), `@Convert` 컨버터 연결, 파일 단위
salt·반복 게이트, 주석과 문자열 리터럴의 구분이다.

컬럼 길이(`VARCHAR(13)`은 IV·인증 태그를 포함한 AES-256+Base64 결과를 담을 수 없다)와
원문 SQL 쓰기는 Phase 2에서 활성화했다. 프레임워크 로그 설정 키와 Lombok `toString()` 노출은
Phase 3의 규칙에 딸려 있고, 근거 조항이 확정된 것만 착수한다.

알고리즘 선택과 적용이 다른 문장에 있어도 잡는다.

```java
MessageDigest digest = MessageDigest.getInstance("SHA-1");   // ← 여기에는 개인정보가 없다
byte[] result = digest.digest(rawLoginPin.getBytes("UTF-8")); // ← 여기에는 알고리즘이 없다
```

알고리즘 이름을 상수에 담고 인스턴스를 팩토리 메서드로 만들어도 따라간다. 실제로 에이전트가
쓰는 형태다.

```java
private static final String ALGORITHM = "SHA-1";             // 리터럴은 상수에
private static MessageDigest newDigest() {
    return MessageDigest.getInstance(ALGORITHM);             // getInstance에 리터럴이 없다
}
MessageDigest md = newDigest();                              // 인스턴스는 팩토리 반환값
return md.digest(rawLoginPin.getBytes(UTF_8));               // ← 차단 지점. 알고리즘 결정 행도 함께 알려준다
```

반대로 적법한 양방향 암호화는 통과시킨다. 주민등록번호에 AES를 쓰는 것은 제7조 제2항
제1호에 따라 적법하므로 검출하지 않는다. `"AES"`를 grep하는 도구와의 차이가 여기다.

## 신뢰도와 동작

| 신뢰도 | 훅 | 동작 |
|---|---|---|
| high | PreToolUse | `permissionDecision: deny` — 쓰기 차단 |
| medium / low | PostToolUse | `additionalContext` — 경고만, 차단하지 않음 |

구조로 확정할 수 없는 것(예: `equals()` 비교가 인증인지 확인 입력 검증인지)은 차단하지
않는다. 오탐으로 개발을 막는 것이 미검출보다 나쁘다고 보기 때문이다.

이 경계는 fixture로 고정되어 있다. 경고로 선언한 검사가 차단으로 올라가면 harness가 실패한다.

## 개발자용 설치와 프로젝트 설정

```bash
# 로컬에서 바로
claude --plugin-dir /path/to/pipa-guard-public
```

Codex는 이 저장소의 `.codex/hooks.json`을 프로젝트 훅으로 읽는다. 새 Codex 세션에서 `/hooks`를
열어 훅 정의를 검토하고 신뢰하면 `apply_patch` 직전에 high 위반을 차단하고, 적용 뒤 medium
위반을 모델 컨텍스트로 돌려준다. 다른 저장소에서 사용하려면 해당 환경에 플러그인을 설치하고
활성화해야 한다. 로컬 소스를 수정해도 이미 설치된 플러그인 캐시에 자동 반영되지는 않는다.
프로젝트 훅과 설치본을 함께 사용하는 경우 중복 실행 여부도 확인한다.
`.codex/hooks.json`만 다른 저장소로 복사하는 것은 플러그인 설치를 대신하지 않는다.

두 공개 마켓플레이스의 설치 소스는 `v0.1.2` 태그에 고정돼 있다. main 소스를 직접 검토하거나
개발하려면 다음과 같이 복제한다. 태그 설치본과 개발 소스의 차이를 확인한 뒤 실행한다.

```bash
git clone https://github.com/jjudop11/pipa-guard-public.git
claude --plugin-dir /path/to/pipa-guard-public
```

프로젝트 루트에 `.pipa.json`을 두어 맥락을 알려준다. 없으면 가장 보수적인 기준이 적용된다.
`.pipa.json.example`을 참고하되, 아래 값과 근거 경로는 예시이므로 실제 배포 환경에 맞게 작성한다.
기존 설정을 덮어쓰거나 예외·검사 제외 항목을 이유 없이 복사하지 않는다.

```json
{
  "exclude": ["build/", "generated/"],
  "subjectType": "user",
  "storageZone": "internet",
  "riskAssessment": null,
  "inboundTransport": {
    "exposure": "internet",
    "tlsTermination": "trusted_proxy",
    "httpsOnly": true,
    "evidence": "deploy/k8s/ingress.yaml"
  },
  "outputPolicies": [
    {
      "sink": "api",
      "source": "src/main/java/com/example/member/ProfileController.java#profile",
      "purpose": "회원 본인의 프로필 조회",
      "allowedItems": ["fullName", "emailAddress"],
      "evidence": "docs/privacy/self-profile.md"
    }
  ],
  "accessLogPolicies": [
    {
      "source": "src/main/java/com/example/audit/AccessAuditService.java#recordAccess",
      "components": {
        "actorId": {"argument": "operatorId"},
        "accessedAt": {"external": "logger_timestamp"},
        "sourceInfo": {"external": "request_mdc"},
        "dataSubjectInfo": {"argument": "memberId"},
        "action": {"argument": "action"}
      },
      "evidence": "config/logback-access.xml"
    }
  ],
  "localStoragePolicies": [
    {
      "source": "src/main/java/com/example/export/ProfileExportService.java#exportProfile",
      "target": "workstation",
      "evidence": "docs/privacy/operator-export.md"
    }
  ]
}
```

여덟 키 모두 실제 판정에 쓰인다. `K-ENC-001`은 `subjectType=user`일 때 제7조 제2항을,
`K-ENC-003`은 `non_user`일 때 제3항을 적용한다. 값이 없거나 알 수 없는 정보주체는 더 보수적인
`user`로 본다. 비이용자의 인터넷망·DMZ 저장과 내부망 주민등록번호 저장은 항상 암호화 대상이다.
내부망의 나머지 고유식별정보만 영향평가 또는 위험도 분석 결과가 항목별 미적용 범위를 명시한
경우에 제외할 수 있다. `riskAssessment` 객체가 존재한다는 사실만으로는 예외가 되지 않는다.
`inboundTransport`는 개인정보 요청 endpoint의 인터넷망 노출, TLS 종단 위치, HTTPS 전용 여부와
실제 배포 근거를 선언한다. 애플리케이션 TLS와 신뢰 프록시 TLS를 모두 인정하고, 누락·모순은
경고하며 명시적 외부 평문 수신은 차단한다. `outputPolicies`는 로그·API 응답의 파일#메서드별
출력 용도와 허용 개인정보 항목을 선언한다. 완전한 정책의 허용 범위 초과는 차단하고, 정책이
없거나 불완전하면 용도를 추정하지 않고 경고한다. `accessLogPolicies`는 접속기록을 생성하는
logger 호출과 제2조 제3호의 다섯 구성요소 공급 방식을 선언한다. 완전한 정책의 직접 인자 누락만
차단하고 정책 불완전은 경고한다. `localStoragePolicies`는 파일#메서드가 실행되는 위치를
`workstation`·`mobile`·`removable_media`·`server` 중 하나로 실제 근거와 함께 선언한다. 보호 대상
위치의 평문 파일 저장은 차단하고 위치 미확인은 경고한다. 상세 필드와 사전 key는
`.pipa.json.example`에 있다. 즉 판정은
`항목 × 정보주체 구분 × 저장 위치 × 위험도 분석`의 함수이며, 코드만 보고는 결정할 수 없다.

## 억제

정당한 예외는 이유와 함께 기록한다. 이유 없는 억제 지시자는 무시된다.

```java
// pipa-guard:ignore K-ENC-002 2026-12-31까지 유지되는 구 시스템 연동 어댑터. 신규 저장 경로 아님. 티켓 SEC-412
public String bridgePassword(String rawPassword, Cipher cipher) throws Exception {
    return new String(cipher.doFinal(rawPassword.getBytes("UTF-8")));
}
```

억제 범위는 `@SuppressWarnings`와 같다. 지시자가 있는 줄과, 그 다음 줄에서 시작하는 구문
단위 전체다. 메서드 선언 위에 두면 그 메서드 본문 전체, 문장 끝에 두면 그 문장만이다.

차단 메시지는 이 지시자를 안내하지 않는다. 에이전트가 코드를 고치는 대신 억제로 도망가는
것을 막기 위해 의도적으로 뺐다.

## 변경분 리뷰

`pipa-review` 스킬은 개인정보 보호·PIPA·ISMS-P 관점의 코드 변경 리뷰에 사용한다. 별도 범위를
지정하지 않으면 staged·unstaged·untracked 파일을 모두 확인하고, pipa-guard의 구조화된 판정과
수동 개인정보 흐름 검토를 결합한다. 결과에는 Finding과 변경 경로 전체의 개인정보 후보·sink·
보호조치·적용 조항 대응표가 포함된다.

규칙 목록을 스킬에 복사해 두지 않고 실행 시점의 `rules/rules.json`, `rules/articles.md`,
`rules/pii_items.json`과 대상 프로젝트의 `.pipa.json`을 읽는다. 엔진이 지원하지 않는 구조는 실제
검사 ID를 붙이지 않은 확인사항으로 분리하며, “검출 없음”을 전체 법령 준수 보증으로 표현하지
않는다. 리뷰 요청만으로 코드를 수정하거나 결과를 외부에 게시하지 않는다.

## 개인정보 흐름도

`pipa-flow-map` 스킬은 Java·Kotlin 코드의 개인정보 후보를 시작점, 변환·보호조치, 저장·전송·
로그·응답 sink에 연결해 Mermaid 흐름도와 증거표를 만든다. 저장소 전체가 기본 범위이며, 변경분이나
모듈·유스케이스를 지정하면 그 범위를 우선한다. 큰 흐름은 신뢰 경계나 유스케이스별로 나누고
안정적인 흐름 ID로 연결한다.

코드에서 직접 확인한 연결, `.pipa.json`이 근거와 함께 선언한 운영 맥락, 추론, 미확인을 서로
구분한다. 파일 밖 호출 그래프나 지원하지 않는 프레임워크 때문에 끊긴 경로는 숨기지 않고 별도 공백
표에 남긴다. 그림에는 실제 개인정보·비밀값을 넣지 않으며, 결과는 코드 기반 검토 초안이지 전체
처리 현황이나 ISMS-P 인증 적합성 보증이 아니다. 사용자가 로컬 출력 경로를 지정하지 않으면 파일을
만들지 않고, 회사 코드베이스 결과를 외부에 게시하지 않는다.

## 감사 에이전트

`pipa-auditor`는 엔진 판정과 `pipa-review`·`pipa-flow-map`을 조정하는 읽기 전용 플러그인
에이전트다. 변경 리뷰, 개인정보 흐름도, 종합 감사 중 요청에 맞는 절차만 실행하며 종합 감사에서는
Finding 검증을 먼저 끝낸 뒤 확인된 경로를 흐름도에 연결한다. 코드와 설정을 직접 수정하지 않고,
외부 검색·MCP 없이 로컬 코드와 플러그인에 포함된 규칙만 사용한다.

플러그인을 활성화하면 `pipa-guard:pipa-auditor`라는 scoped 이름으로 자동 발견된다. Claude Code의
에이전트 선택 화면이나 다음 CLI 방식으로 명시적으로 실행할 수 있다.

```bash
claude --agent pipa-guard:pipa-auditor
```

에이전트는 설치 위치가 바뀌어도 `${CLAUDE_PLUGIN_ROOT}`에서 엔진·규칙을 찾고, 대상 프로젝트의
`.pipa.json`과 저장소 지침은 현재 작업 디렉터리에서 읽는다.

## CLI

훅 없이 직접 검사할 수 있다.

```bash
python3 bin/pipa_check.py src/main/java          # 디렉터리 재귀
python3 bin/pipa_check.py Member.java --json     # 기계 판독용
```

| 종료코드 | 뜻 |
|---|---|
| 0 | 위반 없음 |
| 1 | high 위반 존재 |
| 2 | 검사할 `.java` / `.kt` 파일이 없음 |
| 3 | 엔진 오류 — **판정하지 못했다.** 위반 여부는 알 수 없다 |

3을 1과 나눈 이유는 CI가 "위반을 찾았다"와 "엔진이 깨졌다"를 구별해야 하기 때문이다.
오류 메시지는 stderr에 `pipa-guard: `로 시작하고 traceback을 노출하지 않는다.

훅 모드는 다르다. **종료코드가 언제나 0이다.** 편집 흐름 자체를 깨뜨리지 않고, 차단은 stdout
JSON의 `permissionDecision: deny`로만 표현한다. 대신 사전이 깨지는 등으로 판정하지 못하면
`systemMessage`로 알린다 — 적법한 코드가 통과할 때도 출력이 없으므로, 신호가 없으면 "검사해서
문제없음"과 "검사하지 못함"을 구별할 수 없다.

의존성은 없다. Python 3 표준 라이브러리만 쓴다. 훅은 모든 편집마다 실행되므로
네트워크 호출도, LLM 호출도 하지 않는다. 판정은 결정적이다.

검출기 자신도 개인정보를 남기지 않는다. 보고서에 실리는 근거 코드는 `redact()`를 통과하며
주민등록번호·카드번호·8자리 이상 숫자열은 마스킹된다.

### 성능 기준선

2026-09-09 최근 소표본 점검(준비 1회·측정 5회)의 합성 Java PreToolUse 전체 중앙값은 작은 입력
41.961ms, 2,000줄 입력 218.724ms였다. 아래는 과거 50회 기준선이며 직접적인 개선·회귀율로
비교하지 않는다. 동일 조건의 변경 전후 비교는 배포 전 후속 작업이다.

```bash
python3 tests/benchmark_hooks.py
```

2026-09-06, arm64 macOS·Python 3.14.6에서 시나리오별 50회 측정했다. 작은 기존 합성 fixture의
새 프로세스 훅 전체 중앙값은 약 36ms, `analyze()` 중앙값은 0.8ms 미만이었다. 메모리에서
생성한 합성 2,000줄 입력은 접속기록 규칙 활성화 후 Java `analyze()` 116.736ms, PreToolUse 전체
153.006ms였다. 접속기록 구성요소 누락 경로의 `analyze()` 중앙값은 0.416ms였다.
**실제 코드베이스 측정치가 아니다.** 전체 조건과 p95는 [`docs/PERFORMANCE.md`](docs/PERFORMANCE.md)에
있다. benchmark는 환경 차이가 큰 시간을 CI 합격 기준으로 사용하지 않고, 규칙 확장 전후를 같은
조건으로 비교한다.

## 현재 범위

**Phase 0·1·2·3·4 완료.** Codex `apply_patch` 훅, 엄격 검증과 Claude Code·Codex용 public
GitHub Git-backed 마켓플레이스 패키징까지 완료했다. 활성 규칙은 9개 중
**8개**다. `K-ENC-002`는 제7조
제1항 단서의 비밀번호 일방향 암호화를, `K-ENC-001`은 제7조 제2항의 이용자 개인정보 7항목을,
`K-ENC-003`은 제7조 제3항의 비이용자 고유식별정보 암호화 저장을 판정한다. `K-ENC-004`는
제7조 제4항에 따라 현재 사전의 개인정보 후보가 명시적 HTTP 클라이언트로 송신되는 구간을
판정한다. Spring RestTemplate·WebClient·RestClient·HTTP Service, JDK HttpClient, OkHttp,
Apache HttpClient, Retrofit과 OpenFeign의 명시적 송신 구조에서 직접 인자와 같은 메서드 안의 요청
DTO를 따라간다. 선언형 클라이언트는 같은 파일에서 선언·프록시 수신자·실제 실행 호출이 모두
연결되어야 하고, 명시적 TLS 검증 우회는 경고한다. Spring 서버는 요청 매핑·요청 바인딩·개인정보
후보가 함께 있을 때 `inboundTransport`의 실제 배포 경계를 확인한다. `K-LEAK-001/002`는
선언된 logger의 직접 인자와 Spring 컨트롤러의 직접 반환값·같은 파일 반환 DTO를
`outputPolicies`의 용도별 허용 항목과 비교한다. `K-LOG-001`은 명시적 접속기록 정책과 logger
호출이 연결된 경우 제2조 제3호의 다섯 구성요소를 확인한다. `K-ENC-005`는 명시적으로 확인되는
Java·Kotlin 파일 저장 sink를 `localStoragePolicies`의 실행·저장 위치와 연결해, 개인정보취급자
컴퓨터·모바일 기기·보조저장매체의 평문 저장을 차단하고 위치 미확인은 경고한다. 대상 언어는 Java·Kotlin
(`.java`, `.kt`, `.kts`)이다.

항목 사전에는 12항목이 있다. 제7조 제1항의 인증정보 2개(비밀번호·PIN), 제7조 제2항 각 호의
7개 항목과 제7조 제4항 전송 판정용 일반 개인정보 후보 3개(성명·이메일 주소·휴대전화번호)다.
일반 개인정보는 `transmission_only`로 분리해 제2항·제3항 저장 규칙에는 넣지 않는다. 사전 매칭은
개인정보 **후보**만 정한다. `K-ENC-001`은 영속 컬럼 또는 SQL 쓰기 sink와 암호화 부재가 함께
확인될 때만 Finding을 만든다. 애플리케이션 계층 암호화 가능성을 배제할 수 없는 일반 영속 컬럼은
medium 경고로 남기고 차단하지 않는다.

```
$ python3 tests/run_fixtures.py      # 판정
합계 175/175 통과

$ python3 tests/run_hooks.py         # Claude Code·Codex 입출력·패키지 계약
합계 36/36 통과

$ python3 tests/run_claims.py        # README·설정·결정성·비식별화 주장 계약
합계 10/10 통과
```

세 harness는 각각 판정 결과, Claude Code·Codex 훅 입출력, 문서에 적힌 수치·예제·지원 경계와
설정 8개·비식별화·결정성·무의존성을 검사한다. CI는 Ubuntu·Python 3.12를 주 환경으로,
Python 3.10과 3.14를 추가 환경으로 같은 네 명령을 실행하도록 구성돼 있다. 위 수치는 현재
소스의 로컬 검증 결과이며, 해당 변경의 원격 CI 통과·배포·설치본 반영을 뜻하지 않는다.
실제 모델의 수정 선택은 결정적 계약이 아니므로 이 수치에 포함하지 않는다.

**합성 fixture 175건 기준**이다. 위반 fixture 76건은 선언한 검사가 선언한 신뢰도로 검출되어야
하고(high 검사는 차단, medium 검사는 경고 — high로 올라가도 실패다), 적법 fixture 99건은 high
검출이 하나도 없어야 한다. 그중 87건은 경고도 0건이어야 한다. 실제 코드베이스에 대한
재현율·오탐율은 아직 측정하지 않았다. fixture는 모두 합성 데이터이며 실제 개인정보를 담지 않는다.

계약은 따로 고정한다. `tests/run_hooks.py`는 엔진을 하위 프로세스로 실행해 stdin에 훅 이벤트
JSON을 넣고 stdout·stderr·종료코드를 본다. 신뢰도 라우팅(high는 PreToolUse에서만 차단하고
PostToolUse는 다시 보고하지 않는다), `exclude` 적용, Claude Edit와 Codex `apply_patch`의 패치
재구성, 다중 파일, 판정 실패 신호, CLI 종료코드 네 개가 케이스다. 판정 harness는 `analyze()`를
직접 부르므로 이 계층을 볼 수 없다.

항목 사전은 별도로 검사한다. 활성 규칙의 코드 fixture가 별칭 114개를 전부 실행하지는 않기
때문이다. `tests/dictionary_cases.json`에 매칭 기대값과 **매칭되면 안 되는 식별자 목록**을 두고,
`rules/alias_sources.json`에는 모든 별칭의 공개 근거를 연결한다. harness가 별칭 형식·중복뿐
아니라 근거가 별칭 114개를 빠짐없이 한 번씩 덮는지도 본다. `name`·`nm`은 사물 이름과,
일반 이메일·전화번호는 조직 연락처와 충돌하므로 각각 비매칭 또는 weak 경계로 고정했다.

적법 fixture는 오탐을 잡기 위해 일부러 어렵게 만들었다.

| fixture | 통과해야 하는 이유 |
|---|---|
| C003 | `@Value("${spring.datasource.password}")` — DB 접속 비밀번호는 제2조 제8호의 "비밀번호"가 아니다 |
| C006 | 주민등록번호에 AES — 제7조 제2항 제1호에 따라 적법하다 |
| C008 | `rawPassword.equals(confirmPassword)` — 확인 입력 검증이지 인증이 아니다 |
| C009 | 주석 안에 든 위반 코드 |
| C011 | 같은 클래스에 일방향 해시와 양방향 암호화가 공존 — 값 전파가 새지 않아야 한다 |
| C012 | 알고리즘 상수·팩토리 구조가 V008과 같지만 상수 값이 PBKDF2 — 종류를 무시한 전파를 막는다 |
| C013 | SHA-1 체크섬 팩토리와 BCrypt 비밀번호가 한 클래스에 — "파일에 SHA-1이 있다"로 물들지 않아야 한다 |
| C014 | salt와 반복이 있는 SHA-256 — 경고조차 나오면 안 된다 |
| C015 | 지문 템플릿에 AES — 생체인식정보는 제7조 제1항 단서(일방향) 대상이 아니다 |
| C016 | 여권·운전면허·외국인등록·신용카드 번호에 AES — 제7조 제2항이 요구하는 그대로다 |
| C017 | 여권번호를 암호화한 뒤 별도 문장에서 저장 — 보호조치 없는 필드명만으로 차단하면 안 된다 |
| C018 | 주민등록번호·여권번호의 형식만 검사 — 저장 sink가 없으므로 제2항 저장 규칙 대상이 아니다 |
| C019 | JPA `@Transient` 주민등록번호 — 엔티티 안에 있지만 영속화되지 않는다 |
| C020 | Kotlin `@field:Convert`로 주민등록번호·신용카드번호를 암호화한다 |
| C021 | 영속 필드지만 `orderNo`·`accountId` 등 사전 비매칭 식별자다 |
| C022 | 주민등록번호 암호화 결과만 JDBC SQL 쓰기 인자로 전달한다 |
| C023 | JPA `@ColumnTransformer`로 데이터베이스 암호 함수를 연결한다 |
| C024 | SQL 쓰기 호출 안에서 여권번호를 직접 암호화한다 |
| C025 | 상품권 PIN은 로그인 PIN이 아니다 — 인증 문맥 없는 복합 식별자를 비밀번호로 단정하지 않는다 |
| C026 | 내부망 영향평가가 여권번호를 미적용 범위로 명시했다 — 선언한 항목에만 제3항 단서를 적용한다 |
| C027 | 내부망 주민등록번호는 암호화하고, 평가 범위의 여권번호만 미적용한다 |
| C028 | 비이용자 고유식별정보를 인터넷망 구간에서 양방향 암호화해 저장한다 |
| C029 | 비이용자의 금융정보는 제7조 제3항의 고유식별정보 범위 밖이다 |
| C030 | 비이용자 여권번호의 암호화 결과만 JDBC SQL 쓰기 인자로 전달한다 |
| C031 | 개인정보를 명시적 HTTPS endpoint로 전송한다 |
| C032 | 외부 HTTP여도 실제 AES-GCM 암호화 payload만 전송한다 |
| C033 | RFC1918 사설 주소의 내부 HTTP 호출이다 |
| C034 | 외부 HTTP URL과 개인정보 형식 검사가 있지만 네트워크 sink가 없다 |
| C035 | endpoint 스킴은 알 수 없어도 암호화 결과만 전송한다 |
| C036 | 외부 HTTP 전송값이 사전의 개인정보 후보가 아니다 |
| C037 | 상수로 분리된 HTTPS endpoint를 사용한다 |
| C038 | V026과 같은 Kotlin WebClient 체인이지만 HTTPS endpoint를 사용한다 |
| C039 | 요청 DTO에 실제 암호화 결과만 담아 외부 HTTP로 전송한다 |
| C040 | 요청 DTO를 외부 HTTP로 전송하지만 값이 개인정보 후보가 아니다 |
| C041 | 원문 개인정보 요청 DTO를 명시적 HTTPS endpoint로 전송한다 |
| C042 | TLS 검증 우회 API는 있지만 개인정보 네트워크 송신이 없다 |
| C043 | 일반 변수명이 `trustAll`일 뿐 알려진 TLS 검증 우회 API가 아니다 |
| C044 | 다른 메서드의 같은 이름 요청 변수가 개인정보 taint를 물려받지 않는다 |
| C045 | 개인정보 이름의 setter라도 실제 인자가 암호화 결과면 적법하다 |
| C046 | Spring RestClient로 원문 개인정보 DTO를 명시적 HTTPS에 전송한다 |
| C047 | OkHttp Request의 개인정보 payload를 명시적 HTTPS에 전송한다 |
| C048 | Apache HttpClient 요청이 명시적 사설 주소로만 향한다 |
| C049 | 파일에 HttpClient 타입이 있어도 일반 작업 실행기의 `execute()`는 네트워크 sink가 아니다 |
| C050 | OkHttp Request에는 실제 AES-GCM 암호화 결과만 담는다 |
| C051 | Spring RestClient의 `retrieve()` 뒤 terminal operation이 없어 실제 송신하지 않는다 |
| C052 | `name`·`className`·`fileName`·`displayName`은 사람의 성명으로 단정하지 않는다 |
| C053 | 회사 대표 이메일 주소와 사무실 전화번호는 개인 연락처로 단정하지 않는다 |
| C054 | 성명·사용자 이메일 주소·사용자 휴대전화번호를 HTTPS로 전송한다 |
| C055 | 성명을 실제 AES-GCM으로 암호화한 결과만 외부 HTTP로 전송한다 |
| C056 | 일반 개인정보는 제7조 제2항이 열거한 이용자 저장 7항목에 섞지 않는다 |
| C057 | 일반 개인정보는 제7조 제3항의 비이용자 고유식별정보 저장 범위에 섞지 않는다 |
| C058 | 선언형 HTTP 인터페이스만 있고 프록시 호출이 없으면 송신으로 보지 않는다 |
| C059 | 선언형 메서드와 이름이 같아도 일반 객체 호출은 네트워크 sink가 아니다 |
| C060 | Spring HTTP Service 프록시로 명시적 HTTPS에 전송한다 |
| C061 | Retrofit 프록시로 명시적 HTTPS에 전송한다 |
| C062 | OpenFeign 프록시로 명시적 HTTPS에 전송한다 |
| C063 | Retrofit `Call`을 만들기만 하고 `execute()`·`enqueue()`하지 않는다 |
| C064 | Spring reactive 반환값을 만들기만 하고 `block()`·`subscribe()`하지 않는다 |
| C065 | OpenFeign에는 실제 암호화 결과만 전달한다 |
| C066 | 일반 객체의 `send()`는 JDK HttpClient 송신이 아니다 |
| C067 | Kotlin Retrofit `suspend` 호출을 명시적 HTTPS에 전송한다 |
| C068 | 선언형 프록시와 같은 이름의 다른 타입 수신자가 다시 선언되면 보수적으로 제외한다 |
| C069 | TLS 경계가 미확인이어도 개인정보 요청을 받지 않는 endpoint는 대상이 아니다 |
| C070 | 애플리케이션 서버가 근거 있는 HTTPS 전용 TLS 종단을 제공한다 |
| C071 | 신뢰하는 경계 프록시가 외부 HTTPS만 받고 애플리케이션에는 내부 HTTP로 전달한다 |
| C072 | 인터넷망에 노출되지 않는 내부 endpoint다 |
| C073 | 개인정보 이름이 응답 반환값에만 있어 서버 수신 규칙의 대상이 아니다 |
| C074 | 개인정보 이름의 일반 메서드지만 Spring 요청 매핑이 아니다 |
| C075 | 개인정보 DTO가 요청 인자로 바인딩되지 않는다 |
| C076 | 내부 HTTP connector가 있어도 근거 있는 신뢰 프록시 TLS 뒤에 있다 |
| C077 | 개인정보 POJO와 무관한 요청 DTO를 바인딩해도 개인정보 표시가 타입 사이로 새지 않는다 |
| C078 | API 응답 정책이 성명과 이메일 주소를 허용한 범위 안에서 반환한다 |
| C079 | Spring API가 개인정보가 아닌 상태 DTO만 반환한다 |
| C080 | 로그 정책이 허용한 이메일 주소만 감사 로그에 기록한다 |
| C081 | Logger가 아닌 일반 객체의 `info()` 호출은 로그 sink가 아니다 |
| C082 | 요청 DTO의 개인정보 필드는 API 반환 DTO로 전파되지 않는다 |
| C083 | Kotlin Spring API 반환 DTO가 허용 정책 범위 안이다 |
| C084 | 로그 포맷 문자열의 개인정보 항목명은 실제 출력값이 아니다 |
| C085 | 접속일시는 logger가 공급하고 나머지 네 구성요소는 한 접속기록 호출에 직접 전달한다 |
| C086 | 접속기록 정책이 지정하지 않은 일반 업무 로그는 구성요소 검사의 대상이 아니다 |
| C087 | 근거 있는 보안 컨텍스트·logger timestamp·MDC 공급을 접속기록 구성요소로 인정한다 |
| C088 | 근거 있는 서버 파일 저장은 제7조 제5항의 단말·보조저장매체 범위가 아니다 |
| C089 | 실제 AES 암호화 결과만 개인정보취급자 컴퓨터의 파일에 저장한다 |
| C090 | 비이용자의 비밀번호는 제7조 제5항이 열거한 대상 범위가 아니다 |
| C091 | 일반 객체의 `write()`는 파일 저장 sink가 아니다 |
| C092 | PasswordEncoder의 일방향 비밀번호 결과는 보호된 저장값이다 |
| C093 | 결제 API 시스템 시크릿 키의 Basic 인증용 Base64는 정보주체 비밀번호 처리가 아니다 |
| C094 | AES 보조 메서드가 같은 파일에 있어도 주민등록번호에만 적용되면 비밀번호 흐름으로 전파하지 않는다 |
| C095 | 다른 메서드의 동명 지역 변수를 암호 결과로 연결하지 않는다 |
| C096 | 다른 객체의 동명 메서드를 로컬 암호 보조 메서드로 연결하지 않는다 |
| C097 | 같은 문장의 비밀번호 길이 검사와 주민번호 암호화를 혼동하지 않는다 |
| C098 | 보조 메서드가 실제 암호 처리에 사용하지 않는 인자 자리는 전파하지 않는다 |
| C099 | 여는 중괄호가 다음 줄에 있어도 지역 변수 범위를 구분한다 |

V072~V076은 암호화 코드에 붙인 알고리즘명 문자열, Java package-private 보조 메서드,
실제 암호 처리 인자 자리, Kotlin 및 다음 줄 중괄호 형태의 차단 회귀를 고정한다. 이 경계는
Write·Edit·apply_patch의 엔진 입출력 계약으로도 검사한다. 보조 호출 전파는 같은 파일의
이름이 유일한 선언과 객체 접두어 없는 호출 또는 `this` 호출만 연결한다. 다른 객체·동명 선언의
타입 해석과 임의의 변환·분기·파일 밖 흐름은 보장 범위가 아니다. (D-41)

## 앞으로

- Phase 1 — **완료.** 제7조 제2항 7개 항목 사전 등재, 공개 원문 교차 확인, 진입점 계약,
  성능 기준선, fixture 40건 목표 달성(현재 전체 175건)
- Phase 2 — **완료. `K-ENC-001/003/004`·`K-LEAK-001/002` 활성.** 요청 DTO 전파, TLS 검증
  무력화, 대표·선언형 HTTP 클라이언트, 일반 개인정보 후보, 서버 수신 TLS 경계와 출력 목적별
  최소화까지 완료했다. 로그·API 출력은 명시적 파일#메서드 정책과 비교하고 정책 미확인은
  경고한다. `K-LEAK-003`은 일반적인 독립 마스킹 의무의 현행 근거가 없어 보류했다. (D-27, D-28)
- Phase 3 — **완료. `K-LOG-001`·`K-ENC-005`, 스킬 2개와 `pipa-auditor` 활성.**
  실제 코드베이스 적용의 대상·실행 여부·결과는 D-07에 따라 공개 문서에 기록하지 않는다
- Phase 4 — **완료.** Codex `apply_patch` 훅, Claude 엄격 검증과 Claude Code·Codex용 public
  GitHub Git-backed 마켓플레이스 패키징을 완료했다. v0.1.2 배포 이력은 있으나 D-41 수정의
  새 버전 배포와 공식 플러그인 디렉터리 게시는 아직 완료되지 않았다.

규칙 ID와 조항 연결의 단일 출처는 [`rules/rules.json`](rules/rules.json)이다.
`K-LEAK-001/002`는 제12조 제1항과 `.pipa.json.outputPolicies` 계약에 연결해 활성화했다.
개인정보가 로그·응답에 있다는 사실만으로 차단하지 않고, 완전한 정책의 허용 항목을 넘을 때만
high로 판정한다. 정책 누락·불완전은 medium 경고다.
`K-LEAK-003`은 마스킹 부재 자체를 금지하는 현행 근거가 없어 `article: null`로 보류한다.

## 근거

조항 원문과 출처는 [`rules/articles.md`](rules/articles.md)에 있다.
1차 출처는 국가법령정보센터 공개 API이며 취득 경로와 행정규칙일련번호까지 기록해 두었다.
법령 원문은 저작권법 제7조 제1호에 따라 자유롭게 인용할 수 있다.

- 개인정보의 안전성 확보조치 기준 (개인정보보호위원회 고시 제2026-9호, 시행 2026-07-01)
- 개인정보 보호법 및 같은 법 시행령

필드명 사전([`rules/pii_items.json`](rules/pii_items.json))의 별칭은 **공개 출처에서만**
수집한다. 행정안전부 행정표준용어, 공공데이터포털 표준 데이터 항목, 공개된 본인확인·PG API
규격, 공개 저장소, 일반 약어 관행이다. 출처를 명시할 수 없는 항목은 등재하지 않으며,
특정 조직의 내부 스키마를 옮겨 적지 않는다.

2026-09-04 공공데이터포털이 배포한 **공공데이터 공통표준 8차 원본 XLSX(2025.11월)**와
공개 API·표준·저장소 원문을 교차 확인했다. 공식 약어 `PSWD`, `RRNO`, `PNO`, `DLN`, `FRNO`,
`CRCD_NO`, `ACTNO`를 반영했다. 다만 공개 표준에 있다는 사실과 임의 코드에서 의미가 유일하다는
사실은 다르다. `PIN`은 상품권 번호에도 쓰이고 `SSN`은 미국 식별자이므로, 짧거나 다의적인 표기는
weak로 두어 차단하지 않는다. 원본 파일명·SHA-256과 별칭별 근거는
[`rules/alias_sources.json`](rules/alias_sources.json)에 있다.

## 라이선스

[MIT](LICENSE)

</details>
