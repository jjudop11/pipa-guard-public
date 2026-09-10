# 결정 기록

확정된 판단과 그 근거다. **append-only.** 뒤집을 때는 항목을 지우지 말고 새 항목을 추가하고
기존 항목에 `→ D-NN 으로 대체됨`을 덧붙인다. 왜 그렇게 했는지가 남아야 같은 논의를 반복하지 않는다.

여기 적힌 "검증됨"은 실제로 실행하거나 1차 출처에서 확인했다는 뜻이다.
추정은 "미검증"으로 표기한다.

---

## D-01. 법적 근거와 출처 (검증됨)

**개인정보의 안전성 확보조치 기준** — 개인정보보호위원회 고시 제2026-9호, 시행 2026-07-01.
- 행정규칙일련번호 `2100000281400`, 행정규칙ID `73493`
- 취득 경로: 국가법령정보센터 공개 API `lawService.do?target=admrul&type=XML`
- 상위 법령: 개인정보 보호법 및 같은 법 시행령 (시행령 MST `286175`)

법령 원문은 **저작권법 제7조 제1호**에 따라 보호받는 저작물이 아니므로 자유롭게 인용·배포할 수 있다.
그래서 `rules/articles.md`에 원문을 그대로 담는 것이 가능하고, 그것이 이 프로젝트의 근거 전략이다.

원문·출처 메타데이터·재검토 기한은 모두 `rules/articles.md` 상단 블록에 있다.
고시는 개정되므로 시행일과 고시번호를 반드시 함께 기록한다.

**근거가 사용자의 wiki·회사 프로젝트와 무관함**을 명시한다. 1차 출처는 공개 법령 API뿐이다.

---

## D-02. 판정은 `항목 × 정보주체 × 저장위치 × 위험도분석`의 함수다 (검증됨)

제7조 제2항과 제3항의 구조가 다르다.

- **제2항** — 대상은 **이용자**(제2조 제2호). 7개 항목. **무조건** 적용.
- **제3항** — 대상은 **이용자가 아닌 정보주체**. **고유식별정보만**.
  내부망(제2조 제12호) 저장 시에는 **주민등록번호를 제외하고** 영향평가·위험도 분석
  (제2조 제13호) 결과에 따라 암호화 범위를 조정할 수 있다.

같은 항목, 같은 코드여도 정보주체 구분과 저장 위치에 따라 적법성이 갈린다.
**코드만 보고는 결정할 수 없다.** 그래서 `.pipa.json`에 `subjectType` / `storageZone` /
`riskAssessment`를 둔다. 파일이 없으면 가장 보수적인 값(`user` / `internet` / `null`)을 쓴다.

이것이 이 도구가 단순 린터와 갈리는 지점이다. 맥락 없이는 판정하지 않는다.

---

## D-03. 신뢰도 2단계 → 훅 2개로 라우팅 (검증됨)

**검증된 제약: PreToolUse에서 `additionalContext`는 `permissionDecision` 없이 단독으로 반환할 수 없다.**
즉 PreToolUse는 "막거나 통과"만 가능하고 "통과시키면서 경고"가 안 된다.

그래서 이렇게 나눴다.

| 신뢰도 | 훅 | 출력 |
|---|---|---|
| high | PreToolUse | `permissionDecision: "deny"` + `permissionDecisionReason` |
| medium / low | PostToolUse | `additionalContext` (차단 불가, 경고만) |

구조로 확정할 수 없는 것은 차단하지 않는다. 예: `equals()` 비교가 인증인지 확인 입력
검증인지는 구조로 구분이 불가능하므로 medium이다. **오탐으로 개발을 막는 것이 미검출보다 나쁘다.**

관련 검증 사실:
- PreToolUse stdin: `{session_id, prompt_id, transcript_path, cwd, permission_mode, hook_event_name, tool_name, tool_input, tool_use_id}`
- `hookSpecificOutput.permissionDecision`: `deny` | `allow` | `escalate`
- PostToolUse는 차단할 수 없지만 `additionalContext`를 지원한다
- exit code 2로 차단되는 것은 PreToolUse뿐이다
- 플러그인 변수 `${CLAUDE_PLUGIN_ROOT}` 존재. 인용 방식은 `"\"${CLAUDE_PLUGIN_ROOT}\"/bin/x.py"`

---

## D-04. 사전 매칭은 정규화 후 완전 일치. 부분 문자열 금지 (검증됨)

`normalize_ident()` = 소문자화 + `_`·`$` 제거. 그 다음 **완전 일치**만 본다.
일치하지 않으면 등록된 접두어를 벗기고 재귀 시도한다 (최대 3단계).

부분 문자열 일치를 **의도적으로 하지 않는다.** 만약 했다면 `orderNo`, `merchantNo`,
`pinpoint`, `passthrough` 같은 것들이 전부 걸린다. 그런 도구는 개발자가 즉시 끈다.

접두어 목록에서 `a`, `an`, `the`, `my`를 제거했다. 너무 짧아서 방어할 수 없는 매칭을 만든다.

---

## D-05. 이름은 후보만 고른다. 판정은 구조가 한다 (설계 원칙)

차단 조건은 세 가지가 **모두** 성립할 때다.

1. 개인정보 후보 — 식별자가 사전과 정규화 완전 일치 (D-04)
2. 보호 대상 sink 도달 — 저장·전송·로그 등 조항이 규율하는 지점에 값이 닿는다
3. 보호 장치 부재 — 조항이 요구하는 조치가 그 경로에 없다

구조 신호로 쓰는 것들:
- **얕은 값 전파** — 알고리즘 선택과 적용이 다른 문장에 있는 경우 (D-11)
- **`@Convert` 컨버터 연결** — 컨버터는 복호화를 전제한다
- **컬럼 길이 = 수학적 증명** — `VARCHAR(13)`은 AES-256+Base64 결과(44자 이상)를
  물리적으로 담을 수 없다. 암호화하지 않았다는 증명이다.
- 프레임워크 로그 설정 키, Lombok `toString()` 노출, DDL 한글 주석, VO 타입

역방향도 성립해야 한다. **주민등록번호에 AES를 쓰는 것은 제7조 제2항 제1호에 따라 적법**하므로
검출하지 않는다. `fixtures/compliant/C006`이 이것을 고정한다. `"AES"`를 grep하는 도구와의 차이다.

---

## D-06. 억제는 이유가 필수. 차단 메시지는 억제를 안내하지 않는다 (설계 원칙)

`pipa-guard:ignore <RULE> <이유>` — 이유가 없으면 지시자를 **무시한다**.
정당한 예외는 존재하지만, 기록 없는 예외는 예외가 아니라 구멍이다.

**`format_deny_reason()`은 이 지시자를 의도적으로 언급하지 않는다.**
에이전트에게 탈출구를 알려주면 코드를 고치는 대신 억제로 도망간다.
차단 메시지는 명령형으로 끝난다: "위 위반을 모두 해소한 코드로 다시 작성하십시오."

---

## D-07. 출처 정책 — 공개 출처만, 회사 결과 비공개 (제약)

사전 별칭은 공개 출처에서만 수집한다: 행정안전부 행정표준용어, 공공데이터포털 표준 데이터
항목, 공개된 본인확인·PG API 규격, 공개 저장소, 일반 약어 관행.
출처를 명시할 수 없는 항목은 등재하지 않는다. 특정 조직의 내부 스키마를 옮겨 적지 않는다.

`rules/pii_items.json._meta.source_policy`에 이 정책을 박아 두었고, 항목마다 `source` 필드가 있다.

**회사 코드베이스에 pipa-guard를 돌린 결과는 어떤 형태로도 공개하지 않는다.**
검출 건수, 규칙 분포, 익명화한 코드 조각 전부 포함이다. 이건 Phase 3의 발행 금지 조항이다.

---

## D-08. 측정하지 않은 수치는 만들지 않는다 (제약)

fixture 기준 수치는 반드시 "**합성 fixture N건 기준**"으로 표기한다.
실제 코드베이스에 대한 재현율·오탐율은 측정하기 전까지 존재하지 않는 것으로 다룬다.
설계·개발·테스트·운영 반영 상태를 구분해서 쓴다. 합리적 기대효과를 실제 결과처럼 쓰지 않는다.

---

## D-09. Edit는 패치 후 파일을 재구성해서 검사한다 (검증됨)

`new_string`만 보면 파일 전체 맥락(같은 파일에 `PasswordEncoder`가 있는지 등)을 알 수 없고,
행번호도 틀린다. 그래서 `resulting_text()`가 디스크의 현재 내용에 패치를 적용해 결과 파일을
만든다 (`current.replace(old, new, 1)`, `replace_all`이면 전체). 재구성이 불가능하면
`new_string`으로 폴백한다.

검증: 적법한 파일의 `encoder.encode(rawPassword)`를 `aesUtil.encrypt(rawPassword)`로 바꾸는
Edit가 **재구성된 파일의 정확한 행번호(9행)**로 차단됨을 확인했다.

---

## D-10. 억제 범위는 구문 단위 (검증됨)

처음에는 지시자가 있는 줄과 다음 줄에만 적용했다. 지시자를 메서드 선언 위에 쓰고 위반이
본문에 있는 실제 관행에서 실패했다 (`C010`).

주석 제거된 코드로 줄별 중괄호 깊이를 계산해서 `@SuppressWarnings`와 같은 의미로 바꿨다.
지시자가 있는 줄 + 그 다음 비어 있지 않은 줄에서 시작하는 **구문 단위 전체**.
메서드 선언 위에 두면 본문 전체, 문장 끝에 두면 그 문장만이다.

---

## D-11. 파일 범위 얕은 값 전파 (검증됨)

문장 하나만 보면 판정할 수 없는 경우가 실제로 흔하다.

```java
MessageDigest digest = MessageDigest.getInstance("SHA-1");   // 개인정보가 없다
byte[] result = digest.digest(rawPin.getBytes("UTF-8"));     // 알고리즘이 없다
```

두 개의 전파를 둔다.

- `_config_credential_idents()` — 설정 주입 신호(`@Value`, `System.getenv` 등)와 함께 선언된
  인증정보 식별자를 표시해 **대상에서 뺀다**. `@Value("${spring.datasource.password}")`로 받은
  `dbPassword`는 제2조 제8호의 "비밀번호"가 아니다. 사용 문장이 따로 있어도 대상 밖이다. (`C003`)
- `_crypto_receivers()` — 알고리즘 객체를 담은 변수에 종류(`two_way`/`weak_hash`/`strong_hash`)를
  표시하고, 그 변수가 `.digest(`/`.doFinal(`/`.encrypt(` 등 **실제로 값을 처리하는 호출**에
  쓰일 때만 전파를 인정한다. 이름만 등장하는 것으로는 발동하지 않는다. (`V006`, `V007`)

**전파를 넓힐 때는 적법 fixture를 먼저 추가한다.** 전파가 무관한 문장으로 새는 것이 이 설계의
주된 오탐 경로다. `C011`(한 클래스에 BCrypt와 AES 공존)이 그 방어선이다.

---

## D-12. 상태는 저장소에 둔다 (설계 원칙)

세션 트랜스크립트는 특정 기계, 특정 도구에만 있다. 이어서 작업할 수 있으려면 상태가
저장소에 있어야 한다.

- `AGENTS.md` — 작업 규약. Codex와 Claude Code가 같은 파일을 읽는다.
  `CLAUDE.md`는 `@AGENTS.md` 한 줄로 이 파일을 가리킨다.
- `docs/STATE.md` — 지금 어디까지 왔고 다음에 무엇을 하는가. 세션마다 덮어쓴다.
- `docs/DECISIONS.md` — 이 파일. append-only. 변경률이 달라서 STATE와 분리했다.
  STATE를 덮어쓸 때 결정 기록이 함께 날아가면 안 된다.
- `tests/run_fixtures.py` — 기계가 검증할 수 있는 상태. 문서와 어긋나면 harness가 옳다.

---

## D-13. 규칙 ID의 단일 출처는 `rules/rules.json`. 정합은 harness가 강제한다 (검증됨)

규칙 ID가 `rules/articles.md`·`docs/STATE.md`·`README.md` 세 곳에 손으로 적혀 있었고,
예상대로 어긋났다.

- `articles.md`는 제7조 제2항을 `K-ENC-001`, 제3항을 `K-ENC-003`으로 나눴는데
  `STATE.md`와 `README.md`는 `K-ENC-001` 하나로 합쳐 썼다.
- `K-LOG-001`은 `articles.md` 해석 메모에만 있고 로드맵 어디에도 없었다.

**제2항과 제3항은 나눈다.** D-02가 두 항의 구조가 다르다고 이미 확정했다. 제2항은 이용자를
대상으로 7항목에 무조건 적용되고, 제3항은 이용자가 아닌 정보주체를 대상으로 저장 구간과
위험도 분석에 따라 적용범위가 갈린다. 판정 입력이 다르므로 규칙도 다르다. 합쳐 쓴 쪽이 오류다.

`rules/rules.json`을 레지스트리로 두고 `tests/run_fixtures.py`가 세 가지를 검사한다.

1. `status: active` 규칙의 검사 목록 == 엔진이 실제로 생성하는 `(rule, check)` 집합
   (엔진 소스에서 `rule="..."`, `check="..."` 쌍을 정적으로 뽑는다. fixture가 없는 medium
   검사도 등재를 강제하기 위해 실행 경로에 의존하지 않는다)
2. `articles.md`에 등장하는 모든 규칙 ID가 레지스트리에 있는지 — 고아 ID 방지
3. 근거 조항이 확정된 규칙(`article` 비어 있지 않음)이 `articles.md`에 등재되어 있는지

세 검사가 실제로 드리프트를 잡는지 값을 일부러 어긋내어 확인했다.

**근거 조항이 확정되지 않은 규칙은 `article: null`로 두고 구현하지 않는다.** 규칙 9에 따라
Finding의 `quote`는 원문 인용이어야 하므로, 조항을 확정해 `articles.md`에 원문을 옮기기 전에는
Finding을 만들 수 없다. 현재 `K-LEAK-001/002/003`이 이 상태다. 로드맵에 이름이 있다는 것이
근거가 있다는 뜻은 아니다.

엔진은 아직 레지스트리를 읽지 않는다. `article`·`quote`는 여전히 `bin/pipa_check.py`의
상수다. 정합이 기계로 강제되므로 어긋날 수는 없지만, 규칙이 늘어나면 엔진이 레지스트리를
직접 읽는 편이 낫다.

---

## D-14. 차단하지 않는 검사도 fixture로 신뢰도까지 고정한다 (검증됨)

harness가 위반 fixture를 high 기준으로만 검사했기 때문에 medium 검사 두 개
(`unsalted-hash`, `plaintext-compare`)는 `rules.json`에 등재만 되어 있고 아무것도 고정하지
않았다. 규약 1이 실질적으로 깨져 있던 지점이다. 검사가 조용히 사라져도, 반대로 슬그머니
차단으로 승격돼도 harness는 통과했다.

**신뢰도가 곧 동작이다.** high는 PreToolUse deny, medium/low는 PostToolUse 경고다(D-03).
따라서 "검출되는가"만 고정하는 것으로는 부족하고 "차단하는가"까지 고정해야 한다. 선언 두 개를
추가했다.

- `// pipa-fixture-expect-warn: <rule>/<check>` — medium/low로 검출되어야 한다.
  미검출도 실패고, **high로 올라가도 실패**다
- `// pipa-fixture-expect-clean` — 적법 fixture에서 경고도 0건이어야 한다. medium 검사의
  오탐 방어선을 고정할 때 쓴다

medium 검사에는 위반 쪽과 적법 쪽을 짝으로 둔다. 경고만 하는 검사는 오탐의 대가가 작아 보여서
방어선 없이 늘어나기 쉽고, 그렇게 늘어난 경고는 결국 아무도 읽지 않게 된다.

- `unsalted-hash` — V010(salt 없는 SHA-256) / C014(salt·반복 있는 SHA-256)
- `plaintext-compare` — V011(저장값과 입력값 비교) / C008(확인 입력 비교)

새 검사가 헛돌지 않는지 엔진을 일부러 망가뜨려 확인했다. `unsalted-hash`의 신뢰도를 high로
바꾸면 V010이, 파일 단위 salt/반복 게이트를 지우면 C014가, `CONFIRM_HINT` 구분을 지우면
C008이, `EQUALS_RE`를 무력화하면 V011이 각각 실패한다. 네 경우 모두 확인한 뒤 되돌렸다.

---

## D-15. 사전은 사전으로 검증한다 — 활성 규칙이 없는 항목도 계약으로 고정한다 (검증됨)

Phase 1에서 제7조 제2항 각 호의 7항목을 `rules/pii_items.json`에 등재했다. 그런데 이 항목들을
소비하는 활성 규칙이 없다(`K-ENC-001`은 Phase 2다). 별칭이 60개 넘게 늘어나도 코드 fixture는
아무것도 검출하지 않으므로 harness는 그대로 통과한다. **오탐 방어선이 없는 상태로 사전이
커지는 것**이 Phase 1의 실제 위험이다.

그래서 사전 자체를 검사한다. `tests/dictionary_cases.json`에 기대값을 두고 harness가 본다.

- `match` — 식별자를 `dic.match()`에 넣으면 항목 key와 강도가 정확히 나와야 한다.
  camelCase·snake_case 실물 형태를 섞어 접두어 제거가 실제로 도는지 확인한다
- `no_match` — 매칭되면 안 되는 식별자. **"왜 이 별칭을 등재하지 않았는가"를 기계가 읽을 수
  있게 남긴 것**이다. `fingerprint`(인증서·브라우저 지문), `licenseKey`, `accountId`,
  `pinnedMessage`, `panel`이 여기 있다
- 별칭은 정규화된 형태(`^[a-z0-9]+$`)로만 적는다. 대문자·밑줄·비ASCII 오타를 잡는다
- 항목마다 `source`가 비어 있으면 실패한다. 규약 4·5(D-07)를 기계로 강제한다
- 같은 별칭이 두 항목에 등재되면 실패한다

**규칙이 사전에서 대상을 고르는 기준은 분류가 아니라 조항이 요구하는 조치다.** 항목에
`encryption`을 둔다. `one_way_only`는 제7조 제1항 단서 대상이고, `two_way_allowed`는 암호화가
필요하지만 양방향이 적법한 항목이다. `K-ENC-002`는 `one_way_only`만 본다.

분류(`category`)로 골랐다면 생체인식정보가 걸린다. 제2조 제11호의 인증정보이고 제7조 제1항이
암호화를 요구하지만, 같은 항 단서의 "복호화되지 아니하도록 일방향 암호화"는 "비밀번호를
저장하는 경우"만 규율한다. 지문 템플릿을 AES-GCM으로 암호화하는 것은 적법하다. 실제로 분류
기준으로 되돌려 `C015`가 오탐으로 실패하는 것을 확인했다.

별칭 강도 배분도 이 원칙을 따른다. 신용카드·계좌는 한정 표기만 strong으로 두고
`cardNo`·`accountNo`는 weak에 둔다(회원카드번호, 회계 계정번호일 수 있다). weak는 차단하지
않고 경고만 하므로(D-03) 애매한 것은 weak가 맞다. `arn`(Amazon Resource Name)과
`fingerprint`처럼 다른 뜻이 압도적인 약어는 아예 등재하지 않는다.

새 검사 다섯 개가 헛돌지 않는지 값을 일부러 어긋내어 확인했다. `fingerprint` 등재, 별칭
대문자 오타, 별칭 중복 등재, `source` 삭제, 엔진 필터를 분류 기준으로 되돌리기 — 모두 실패를
만들었고 되돌렸다.

---

## D-16. 진입점 계약은 판정과 따로 고정한다. 판정 실패는 조용할 수 없다 (검증됨)

`tests/run_fixtures.py`는 `pipa_check.analyze()`를 직접 부른다. 그래서 **판정**은 27건으로
고정되어 있었지만 진입점의 입출력 계약은 하나도 고정되어 있지 않았다. 훅 경로 4개를 손으로
한 번 확인한 기록이 `docs/STATE.md`에 있었을 뿐이고, CI에 없었고 재현되지 않았다.

그 틈에서 실제로 두 가지가 어긋나 있었다.

**1. 훅이 조용히 fail-open이었다.** `run_hook()`은 사전 로드 실패도 `return 0`으로 삼켰다.
적법한 코드가 통과할 때의 출력도 "없음 / exit 0"이므로 **"검사해서 문제없음"과 "검사하지
못함"이 구별되지 않았다.** 보호가 사라진 사실을 아무도 모르는 상태다. 이 프로젝트의 전제가
"위반이 디스크에 닿기 전에 막는다"인데, 막지 못하게 된 것을 알 방법이 없으면 전제가 무너진다.

편집을 막는 방향으로 고치지는 않았다. 판정하지 못한 것을 근거로 차단하면 조항 없는 차단이
된다(규약 9). 종료코드 0을 유지하고 `systemMessage`로 알린다. 훅 공통 출력 필드이고 사용자에게
경고로 보이며 결정에는 관여하지 않는다.

실패와 "검사 대상 아님"은 구별한다. 확장자 불일치·`exclude` 적용·검사할 텍스트 없음은 정상
통과이므로 조용하다. 이벤트 구조가 깨진 것, 사전을 읽을 수 없는 것, 판정 중 예외는 알린다.
예외 메시지에는 소스 조각이 섞일 수 있으므로 **종류(`type(exc).__name__`)만** 싣는다 (규약 7).

**2. CLI의 exit 1이 두 가지 뜻이었다.** `load_dictionary()`가 감싸여 있지 않아 사전이 깨지면
traceback + exit 1이었고, 이것이 "high 검출 → exit 1"과 같은 코드였다. 그래서 CI의 자기 검사
단계가 **사전이 깨진 것을 exclude 설정 문제로 오진했다** — `|| (echo "차단 검출됨. .pipa.json
exclude 확인 필요." && exit 1)`. 가정이 아니라 그렇게 동작하고 있었다.

종료코드를 넷으로 나눴다. `0` 위반 없음 / `1` high 위반 / `2` 검사할 파일 없음 / `3` 엔진 오류.
오류 메시지는 stderr에 `pipa-guard: `로 시작하고 traceback을 노출하지 않는다. CI는 네 코드를
각각 다른 메시지로 진단한다.

**계약 harness를 따로 두었다.** `tests/run_hooks.py`는 엔진을 **하위 프로세스로 실행하고**
stdin에 훅 이벤트 JSON을 넣어 stdout·stderr·종료코드를 본다. 15건이다. 판정 계층과 I/O 계약
계층은 다른 것이고, 한 harness가 둘을 다 볼 수는 없다. 규약 1의 "계약은 fixture로 고정한다"를
훅 계층에 적용한 것이다.

테스트용 우회 스위치를 엔진에 넣지 않았다. 사전 실패를 만들 때는 `bin/pipa_check.py`를 빈 임시
디렉터리에 복사한다. `PLUGIN_ROOT`를 `__file__` 기준으로 잡으므로 사본은 사전 경로를 찾지
못하고, 실제 실패 경로를 그대로 탄다.

계약을 먼저 쓰고 실패를 확인한 뒤 엔진을 고쳤다(11/15 → 15/15). 새 계약이 헛돌지 않는지 네 가지로
확인했다. 사전 실패를 다시 `return 0`으로 되돌리면 systemMessage 케이스가, 엔진 오류를 `EXIT_HIGH`로
합치면 종료코드 3 케이스가, PreToolUse가 medium도 차단하게 하면 라우팅 케이스가, PostToolUse가
high도 보고하게 하면 역방향 라우팅 케이스가 각각 실패한다. 네 경우 모두 확인한 뒤 되돌렸다.

---

## D-17. 성능은 재현 가능한 benchmark로 추적하고 CI 고정 임계값으로 삼지 않는다 (검증됨)

훅은 모든 `Write`·`Edit`마다 새 Python 프로세스로 실행된다. 규칙을 늘리기 전에 기준선을 재지
않으면 전파 확장과 컬럼 길이 파싱이 편집 체감에 미치는 비용을 알 수 없다. 그래서
`tests/benchmark_hooks.py`로 두 계층을 분리해 측정한다.

- 새 프로세스 훅 전체 — 인터프리터 시작, import, 이벤트 처리, 설정·사전 로드, 판정, 출력 포함
- 동일 프로세스 엔진 내부 — 설정 탐색, 사전 로드, `analyze()`를 따로 측정

2026-09-04 arm64 macOS·Python 3.14.6에서 합성 입력을 준비 5회 뒤 50회 측정했다. 작은 기존 합성
fixture는 훅 전체 중앙값 30~31ms, `analyze()` 중앙값 0.7ms 미만이었다. 메모리 생성 합성 2,000줄
Java는 `analyze()` 중앙값 112.195ms, PreToolUse 전체 142.101ms, PostToolUse 전체 143.929ms였다.
Kotlin 2,000줄은 `analyze()` 95.331ms, PreToolUse 전체 126.367ms였다. 전체 표와 환경은
`docs/PERFORMANCE.md`에 둔다. **실제 코드베이스 성능이 아니라 합성 입력 기준**이다. (D-08)

시간은 하드웨어·운영체제·Python 버전의 영향을 크게 받으므로 절대 수치를 CI 고정 임계값으로
삼지 않는다. 같은 환경·입력·표본 조건으로 규칙 확장 전후를 비교한다. Phase 2 규칙은 대형 파일의
주된 비용인 `analyze()`의 파일 전체 순회를 무제한으로 늘리지 않고 기존 전처리 결과를 재사용한다.
회사 코드베이스에서 측정한 결과는 문서나 공개 보고서에 옮기지 않는다. (D-07)

---

## D-18. 암호화 부재는 증거 강도에 따라 차단과 경고를 나눈다 (검증됨)

`K-ENC-001`은 제7조 제2항의 이용자 개인정보 7항목을 처음으로 활성 판정에 연결한다. 기존
`K-ENC-002`는 위험한 알고리즘 사용이라는 **존재**를 찾았지만, 이 규칙은 보호조치의 **부재**를
판정해야 한다. 파일에 `@Convert`가 보이지 않는다는 사실만으로는 서비스 계층에서 이미 암호화한
값을 넣는 경우를 배제할 수 없다. 따라서 구조 증거의 강도에 따라 세 검사로 나눴다.

| 검사 | 신뢰도 | 근거 |
|---|---|---|
| `plaintext-sized-column` | high | 44자 미만의 영속 문자열 컬럼은 IV·인증 태그·암호문을 함께 담을 수 없다 |
| `plaintext-sql-write` | high | 원문 개인정보 식별자가 같은 문장의 SQL INSERT/UPDATE 값 인자로 직접 들어간다 |
| `unprotected-column` | medium | 영속 필드에 암호화 연결이 없지만 파일 밖에서 암호화했을 가능성은 남는다 |

별칭이 weak면 high 검사는 medium으로, medium 검사는 low로 내린다. `accountNo`가 회계 계정번호일
수 있는 경우처럼 항목 의미가 확정되지 않았는데 편집을 막지 않기 위해서다. (D-03, D-15)

보호조치는 이름이 아니라 연결 구조로 인정한다. 암호화 이름의 `@Convert`, 암호 함수를 쓰는
`@ColumnTransformer`, SQL 쓰기 전 실제 `.encrypt()` 호출에서 시작한 얕은 값 전파가 그 신호다.
변수명에 `encrypted`가 붙었다는 사실만으로는 보호된 값으로 인정하지 않는다. Kotlin의
`@field:Convert`·`@field:Column`도 같은 구조로 처리한다.

`.pipa.json.subjectType`을 판정에 처음 연결했다. `user` 또는 알 수 없는 값은 제2항을 적용하고,
`non_user`는 제3항 규칙(`K-ENC-003`)의 범위이므로 `K-ENC-001`에서 제외한다. 훅 계약이 같은
위반 코드가 `user`에서는 차단되고 `non_user`에서는 제2항으로 차단되지 않는 것을 고정한다.

합성 fixture 43건(위반 19·적법 24)과 훅 계약 16건으로 검증했다. C019에서 `@Transient`,
C020에서 Kotlin `@field:Convert`, C022에서 암호화 호출, C023에서 `@ColumnTransformer`를 각각
제거하면 `unprotected-column` 또는 `plaintext-sql-write`가 발생한다. V018은 암호화 컨버터가
있어도 컬럼이 암호문보다 짧으면 `plaintext-sized-column`이 우선함을 고정한다. V019/C024는
같은 SQL 호출에서도 암호화 연결을 식별자별로 판정해, 한 값의 암호화가 다른 원문 값을 숨기지
않으면서 인라인 암호화는 통과시키는 경계를 고정한다.
`subjectType=non_user`이면 V012의 제2항 Finding이 사라지는 것도 별도로 확인했다. 실제 코드베이스 재현율·오탐율은
미측정이다. (D-08)

성능은 동일한 합성 2,000줄·50회 조건에서 Java `analyze()` 중앙값이
112.195ms → 114.636ms(+2.2%), PreToolUse 전체가 142.101ms → 146.429ms(+3.0%)였다.
SQL 쓰기 신호가 없는 파일은 값 전파 수집을 건너뛴다. 전체 표는 `docs/PERFORMANCE.md`에 있다.

---

## D-19. 공개 표준 등재와 차단 신뢰도는 분리하고, 별칭 근거 범위를 기계로 고정한다 (검증됨)

Phase 1에서 별칭의 출처 종류는 적었지만 실제 행정표준·공공데이터 원본과의 전수 대조는 남아
있었다. 2026-09-04 공공데이터포털이 배포한 `공공데이터 공통표준(2025.11월).xlsx`를 직접
내려받아 공통표준단어·공통표준용어 시트를 확인했다. 원본 SHA-256은
`185fe34299e1ed8ccf02837bbe80b23cc21e76f109002c9ef1ab9d83fb3d8b12`다.

원본은 다음 영문명·약어를 공식 표준으로 둔다.

| 항목 | 영문명 | 공식 약어 |
|---|---|---|
| 비밀번호 | Password | `PSWD` |
| 주민등록번호 | Resident Registration Number | `RRNO` |
| 여권번호 | Passport Number | `PNO` |
| 운전면허번호 | Driver's License Number | `DLN` |
| 외국인등록번호 | Foreigner Registration Number | `FRNO` |
| 신용카드번호 | Credit Card Number | `CRCD_NO` |
| 계좌번호 | Account Number | `ACTNO` |

이 중 기존 사전에 없던 `pswd`·`pno`·`dln`·`frno`·`crcdno`·`actno`를 추가했다(`rrno`는
이미 있었다). 그러나 **공공 DB에서 표준 약어라는 사실은 임의의 Java/Kotlin 식별자에서 의미가
유일하다는 뜻이 아니다.** `PNO`·`DLN`·`FRNO`·`ACTNO`는 짧아 다른 번호와 충돌할 수 있으므로
weak다. 반대로 `PSWD`·`RRNO`·`CRCD_NO`는 항목을 충분히 한정하므로 strong이다.

공개 원문 대조에서 기존 경계도 고쳤다.

- PCI SSC는 PIN을 사용자 인증용 비밀 숫자 비밀번호로 정의하지만, 토스페이먼츠 공개 문서는
  PIN을 게임문화상품권 번호에도 쓴다. 단독 `pin`·`pinNo`·`pinCode`·`pinNumber`·`simplePin`은
  weak로 내리고, `authPin`·`loginPin`처럼 인증 문맥이 식별자에 있는 경우만 strong으로 둔다.
- 공개 개인정보 도구는 `KR_RRN`과 `US_SSN`을 별도 국가 식별자로 구분한다. `ssn`·
  `socialSecurityNumber`를 한국 주민등록번호로 차단할 수 없으므로 weak로 내렸다.
  `registration`이 빠진 `residentNumber`·`residentNo`도 weak다.
- `biometricInfo`는 인증·식별 목적이 아닌 일반 생체정보일 수 있고 `faceEmbedding`도 목적이
  식별자만으로 확정되지 않으므로 weak다.
- `secondaryPassword`는 공개 코드에서 보조 데이터스토어 접속 비밀번호로 쓰이는 반례가 확인됐다.
  제2조의 이용자 비밀번호로 단정할 수 없어 사전에서 빼고 `no_match`로 고정했다.

`rules/alias_sources.json`을 추가해 별칭마다 공개 출처와 확인 방식(`direct`, `composed`,
`boundary`)을 연결했다. 공통표준 원본 파일명·시트·해시도 그 파일에 둔다. harness는
`pii_items.json`의 별칭 집합과 근거 파일의 집합이 항목별로 정확히 같은지, 중복 근거가 없는지,
모든 출처에 공개 HTTPS URL·발행자·근거 설명이 있는지 검사한다. 이후 별칭을 추가하면서 근거를
빼먹으면 fixture와 무관하게 실패한다. 임시 복사본에서 `pswd`의 근거 연결만 제거했을 때
harness가 누락을 정확히 실패로 보고하는 것도 확인했다.

합성 fixture는 44건(위반 19·적법 25), 사전 계약은 매칭 46건·비매칭 34건이다. V006·V008은
인증 문맥이 분명한 `rawLoginPin`으로 high 차단을 유지하고, C025는 `giftCardPin`을 암호화해도
비밀번호 일방향 규칙이 발동하지 않는 경계를 고정한다. 실제 코드베이스 재현율·오탐율은
미측정이다. (D-08)

---

## D-20. 내부망 평가 예외는 구조가 완전한 항목별 선언에만 적용한다 (검증됨)

제7조 제3항의 원문과 국가법령정보센터의 현행 고시 제2026-9호(시행 2026-07-01)를 다시
대조했다. 비이용자의 고유식별정보는 인터넷망·DMZ 저장 시 항상 암호화해야 한다. 내부망도
원칙적으로 같고, **주민등록번호 외의 고유식별정보만** 개인정보 영향평가 또는 암호화 미적용 시
위험도 분석 결과에 따라 적용 여부와 범위를 정할 수 있다.

따라서 `.pipa.json.riskAssessment`는 객체가 있다는 사실만으로 보호를 끄지 않는다. 다음 값이
모두 있어야 하고, `exemptItems`에 들어 있는 사전 key에만 내부망 예외를 적용한다.

- `basis`: `privacy_impact_assessment` 또는 `risk_analysis`
- `document`: 결과 문서 참조
- `date`: 실제 달력에 존재하는 `YYYY-MM-DD`
- `conclusion`: `encryption_not_required`
- `exemptItems`: `passportNumber`, `driverLicenseNumber`, `alienRegistrationNumber` 중 결과가
  미적용 범위로 정한 항목

`residentRegistrationNumber`는 목록에 잘못 넣어도 무시한다. 인터넷망·DMZ, 알 수 없는 저장 구간,
누락·오타가 있는 평가 선언도 예외를 인정하지 않는다. 반대로 제3항은 고유식별정보만 규율하므로
비이용자의 신용카드번호·계좌번호까지 이 규칙으로 넓히지 않는다.

이 설정은 결과 문서의 실질적 적정성을 엔진이 심사한다는 뜻이 아니다. 엔진은 네트워크나 LLM을
쓰지 않고 문서 본문도 해석하지 않는다. 개인정보처리자가 완료된 평가 결과를 항목별로 선언한 것을
판정 입력으로 신뢰하며, 불완전한 선언만 보수적으로 거부한다. 실제 영향평가·위험도 분석을 이
도구가 대체하지 않는다.

`K-ENC-003`은 K-ENC-001과 같은 저장 구조의 증거 강도를 재사용한다. 짧은 컬럼과 원문 SQL 쓰기는
high, 일반 영속 필드는 medium이며 weak 별칭은 한 단계 내린다. 합성 fixture 54건(위반 24·적법
30)과 훅 계약 17건으로 정보주체 분기의 중복 부재, 인터넷망 예외 금지, 주민등록번호 예외 금지,
불완전한 설정의 보수적 처리, 항목별 예외, 금융정보 범위 밖을 고정했다. 실제 코드베이스
재현율·오탐율은 미측정이다. (D-08)

같은 합성 benchmark를 다시 실행한 결과 기존 비교 시나리오에서는 측정 가능한 회귀가 없었다.
비이용자·내부망·영향평가 예외 분기를 실제로 타는 19줄 합성 fixture는 새 프로세스 PreToolUse
전체 중앙값 30.544ms, `analyze()` 중앙값 0.331ms였다. 상세 조건과 p95는
`docs/PERFORMANCE.md`에 있다. 실제 코드베이스 성능이 아니다. (D-08, D-17)

---

## D-21. 제4항 초기 차단은 원문 개인정보와 명시적 외부 HTTP 전송이 함께 보일 때만 한다 (검증됨)

현행 개인정보의 안전성 확보조치 기준 제7조 제4항은 개인정보를 정보통신망을 통해 인터넷망
구간으로 송ㆍ수신할 때 안전한 암호 알고리즘으로 암호화하도록 정한다. 이 규칙은 저장 암호화와
달리 `개인정보 후보 × 네트워크 sink × 전송 구간 보호 부재`를 함께 확인해야 한다. 서버가 반환하는
내용 자체의 적법성을 판정하면 `K-LEAK-002`와 겹치므로 초기 범위는 Java·Kotlin HTTP 클라이언트의
송신으로 제한한다.

`K-ENC-004/plaintext-http-transmission`은 다음 조건이 모두 보일 때 high다.

1. 현재 공개 근거 사전 9항목의 strong 식별자가 호출 인자에 있다.
2. RestTemplate·WebClient 등 명시적 HTTP 클라이언트 문맥과 실제 송신 호출이 있다.
3. 직접 URL 또는 얕게 전파한 endpoint 상수가 외부 `http://`다.
4. 실제 암호화 호출에서 시작한 payload가 아니다.

weak 별칭은 medium으로 내린다. endpoint가 설정에서 주입되어 스킴을 확인할 수 없으면
`unverified-network-transmission` medium 경고만 낸다. HTTPS, localhost·사설 IP·명시적 내부
호스트, 실제 양방향 암호화 결과는 검출하지 않는다. Base64와 `encoded`라는 이름은 보호조치가
아니므로 평문 HTTP 차단을 피하지 못한다.

Kotlin WebClient의 줄바꿈 체인이 처음에는 문장별로 끊겨 V026을 놓쳤다. 다음 줄이 점(`.`)으로
시작하면 직전 문장을 다시 꺼내 fluent 호출 하나로 합치도록 `split_statements()`를 고쳤다.
상수 endpoint는 고정 3회 얕은 전파만 하며 판정은 결정적이다. URL 호스트 판정에 무거운 표준
모듈을 import했을 때 새 프로세스 비용이 늘어, 필요한 HTTP·내부 주소 판정만 경량 코드로 바꿨다.

초기 범위에는 명확한 한계가 있다. 현재 사전 9항목 밖의 이름·이메일·전화번호 등 일반 개인정보,
개인정보를 담은 요청 DTO의 값 전파, 지원 목록 밖의 HTTP API, 서버 수신측 TLS 설정, 인증서·호스트명
검증을 무력화한 HTTPS는 아직 판정하지 않는다. 따라서 “제4항 전체 준수”가 아니라 확인 가능한
평문 HTTP 송신 위반을 우선 차단하는 규칙이다. 다음 확장은 이 한계를 fixture로 먼저 고정한다.

합성 fixture 68건(위반 30·적법 38)과 훅 계약 18건으로 평문 HTTP, WebClient 체인, endpoint 상수,
Base64 반례, 비밀번호 대상, 목적지 미확인 경고, HTTPS·내부 주소·암호화 payload 방어선을 고정했다.
평문 HTTP 차단 23줄 합성 fixture는 새 프로세스 PreToolUse 중앙값 32.895ms, `analyze()` 중앙값
0.602ms였다. 직전 합성 측정 대비 기존 시나리오의 중앙값 증가는 최대 4.330ms였다. 실제 코드베이스
재현율·오탐율과 성능은 미측정이다. (D-08, D-17)

---

## D-22. 요청 DTO 전파는 메서드 안으로 제한하고 TLS 검증 우회는 경고로만 낸다 (검증됨)

`K-ENC-004`의 직접 호출 인자만 보면 실제 클라이언트 코드에서 흔한
`원문 개인정보 → 요청 DTO → HTTP sink`를 놓친다. 생성자, setter, builder와 단순 대입을 따라
요청 객체를 표시하되 고정 3회만 반복하고 같은 메서드 범위를 벗어나지 않는다. 파일 전체에서
`request` 같은 흔한 지역 변수명을 공유하면 서로 다른 메서드의 값이 섞여 오탐이 되기 때문이다.
메서드 이름 자체도 개인정보 값으로 보지 않는다. 예를 들어 `setPassportNumber(encryptedValue)`는
setter 이름이 아니라 실제 인자의 보호 여부로 판정한다.

HTTPS URL만으로 안전한 전송을 확정할 수도 없다. `NoopHostnameVerifier.INSTANCE`,
`AllowAllHostnameVerifier`, `TrustAllStrategy`, Netty의 `InsecureTrustManagerFactory`처럼 공개 API상
인증서 또는 호스트명 검증을 무력화하는 명확한 신호를 찾는다. 다만 현재 분석은 그 설정이 실제
송신에 사용한 클라이언트 인스턴스까지 연결됐는지 확정하지 못한다. 따라서 같은 파일에 원문
개인정보 HTTPS 송신과 검증 무력화 신호가 함께 있어도 `tls-verification-disabled` medium 경고만
내고 차단하지 않는다. 이름이 `trustAll`이라는 이유만으로는 신호로 인정하지 않는다.

합성 fixture 80건(위반 35·적법 45)과 훅 계약 19건으로 생성자·setter·Kotlin builder 전파,
목적지 미확인 DTO 경고, TLS 검증 우회 경고, 메서드 간 taint 격리, 암호화된 setter 인자,
일반 HTTPS DTO와 비개인정보 DTO 방어선을 고정했다. DTO 평문 HTTP 차단 24줄 합성 fixture는
새 프로세스 PreToolUse 중앙값 32.914ms, `analyze()` 중앙값 1.031ms였다. 확장 전과 비교한 기존
합성 시나리오의 중앙값 증가는 최대 0.712ms였다. 실제 코드베이스 재현율·오탐율과 성능은
미측정이다. (D-08, D-17)

남은 범위는 지원 목록 밖 HTTP 클라이언트, 서버 수신측 TLS, 사전 9항목 밖 일반 개인정보다.

---

## D-23. HTTP 클라이언트 확장은 공식 송신 구조별로 좁게 판정한다 (검증됨)

Spring Framework 공식 REST 클라이언트 문서는 `RestClient`의 요청 본문을 `body(Object)`로 넣고
`retrieve()` 또는 `exchange()`에서 송신하는 구조를 설명한다. OkHttp 공식 저장소의 예제는
`RequestBody → Request.Builder → client.newCall(request).execute()`를, Apache HttpClient 5 공식
Quick Start는 `ClassicHttpRequest → httpclient.execute(request, ...)`를 사용한다.

- Spring: https://docs.spring.io/spring-framework/reference/integration/rest-clients.html
- OkHttp: https://github.com/square/okhttp
- Apache HttpClient: https://hc.apache.org/httpcomponents-client-5.6.x/quickstart.html

`K-ENC-004`는 이 구조를 그대로 따라 Spring `RestClient`, OkHttp, Apache HttpClient 5를 지원
목록에 추가한다. OkHttp와 Apache는 URL·payload를 담은 요청 객체의 taint와 endpoint 종류를 기존
고정 3회 얕은 전파로 실행 지점까지 전달한다.

`execute()`는 작업 실행기, SQL 실행기 등에도 널리 쓰이므로 파일에 `HttpClient`라는 단어가 있다는
이유만으로 네트워크 sink로 취급하지 않는다. OkHttp는 같은 식의 `newCall(...).execute/enqueue`
형태만 인정하고, Apache는 `CloseableHttpClient` 또는 Apache `HttpClient` 타입으로 선언한 수신자의
`execute()`만 인정한다. Spring `RestClient`의 `retrieve()`는 공식 문서상 그 자체로는 부수효과가
없으므로 뒤에 응답 body·entity terminal operation이 있을 때만 sink로 인정한다. 기존 WebClient
fixture도 실제 terminal 호출까지 포함하도록 보강했다.

합성 fixture 89건(위반 38·적법 51)과 훅 계약 20건으로 세 클라이언트의 외부 평문 HTTP 차단,
HTTPS·사설 주소·암호화 payload 통과, 일반 작업 실행기 `execute()`와 terminal operation 없는
`retrieve()` 오탐 방어를 고정했다. 합성
fixture 기준 `analyze()` 중앙값은 Spring 1.046ms, OkHttp 1.595ms, Apache 1.832ms이고 새 프로세스
PreToolUse 전체는 각각 34.352ms, 33.861ms, 33.892ms였다. 확장 전 기존 합성 시나리오와 비교한
중앙값 증가는 최대 1.887ms였다. 실제 코드베이스 재현율·오탐율과 성능은 미측정이다.
(D-07, D-08, D-17)

아직 HTTP Service proxy·Retrofit·Feign의 선언부와 실제 호출 연결, 서버 수신측 TLS, 사전 9항목 밖
일반 개인정보는 판정하지 않는다.

---

## D-24. 일반 개인정보는 전송 전용 항목으로 분리하고 사람 문맥의 별칭만 차단한다 (검증됨)

개인정보 보호법 제2조 제1호는 성명을 통해 개인을 알아볼 수 있는 정보를 개인정보로 정의한다.
개인정보보호위원회가 등록·공개한 개인정보파일도 성명, 이메일·전자우편·전자우편주소,
전화번호·휴대전화번호를 개인정보 항목으로 명시한다. 별칭 표기는 공공데이터 공통표준 8차
원본 XLSX에서 직접 확인했다.

- 개인정보 보호법 제2조: https://law.go.kr/LSW/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=900040612
- 개인정보보호위원회 개인정보파일: https://pipc.go.kr/np/default/contents.do?cIdx=229&isBlank=true
- 공공데이터 공통표준 8차: https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004434

사전에 `fullName`, `emailAddress`, `mobilePhoneNumber`를 추가하되 `encryption=transmission_only`로
분리한다. 이 세 항목은 제7조 제4항의 전송 판정에는 필요하지만 제7조 제2항·제3항이 열거한 저장
항목은 아니다. 기존 `two_way_allowed`로 넣으면 이름·이메일·휴대전화번호의 일반 영속 필드까지
K-ENC-001이 검사하게 되어 조항 문언을 넘어선다. harness도 세 번째 조치 값을 명시적으로 허용해
오타나 뜻이 불분명한 새 값을 거부한다.

별칭 신뢰도는 공개 표준의 의미 경계를 따른다.

- `fullName`은 공통표준의 성명/Full Name과 뜻이 일치해 strong이다. `FLNM`은 공식 약어지만
  file name 약어와 충돌할 수 있어 weak다. `name`·`nm`은 표준 자체가 사물·단체·현상까지
  포함하므로 등재하지 않는다.
- 일반 `emailAddress`는 기관·업체·회사 대표 주소일 수 있어 weak다. 공통표준이 사람 역할로
  한정한 `userEmailAddress`·`memberEmailAddress`·`customerEmailAddress`만 strong이다.
- 일반 전화번호·휴대전화번호도 대표번호나 공용 단말일 수 있어 weak다. 공통표준의 사용자·회원·
  고객 휴대전화번호에 대응하는 한정 표기만 strong이다. `phone` 단독은 기기 객체와 충돌해
  등재하지 않는다.

사전 확장 중 `encryptedFullName = encryptor.encrypt(fullName)`의 결과가 보호값으로 표시되지 않아
외부 HTTP 전송에서 오탐되는 결함을 C055가 드러냈다. 보호값 전파가 제7조 제2항 저장 항목만
시작점으로 삼고 있었기 때문이다. 실제 암호 호출을 요구하는 조건은 유지하면서 시작점만 사전의
모든 항목으로 넓혔다. 이름에 `encrypted`가 있다는 사실만으로는 여전히 보호조치로 인정하지 않는다.

합성 fixture 99건(위반 42·적법 57), 사전 항목 12개·별칭 114개, 매칭 기대값 56건·비매칭
방어선 49건과 훅 계약 21건으로 신뢰도 라우팅과 반례를 고정했다. 성명 및 사람 문맥의 이메일·
휴대전화번호를 외부 평문 HTTP로 보내면 차단하고, 일반 연락처는 경고, 조직 연락처·HTTPS·실제
암호화 payload는 통과한다. C056·C057은 이 세 항목이 이용자 제2항 저장 규칙과 비이용자 제3항
저장 규칙에 섞이지 않는 것도 고정한다. 실제 코드베이스 재현율·오탐율은 미측정이다.
(D-07, D-08, D-19)

---

## D-25. 선언형 HTTP 클라이언트는 같은 파일의 선언·프록시·실행 호출을 모두 연결한다 (검증됨)

Spring Framework의 HTTP Service는 `@HttpExchange` 인터페이스를 `HttpServiceProxyFactory`로
프록시화하고, Spring Cloud OpenFeign은 `@FeignClient` 인터페이스의 구현을 런타임에 만든다.
Retrofit도 HTTP API 인터페이스를 구현 객체로 바꾼다. 따라서 어노테이션 선언만으로는 해당 코드가
실제로 네트워크 송신을 실행한다고 단정할 수 없다.

- Spring HTTP Service: https://docs.spring.io/spring-framework/reference/integration/rest-clients.html#rest-http-interface
- Spring Cloud OpenFeign: https://docs.spring.io/spring-cloud-openfeign/docs/current/reference/html/
- Retrofit: https://github.com/square/retrofit

의존성이나 AST 파서를 추가하지 않는 범위에서 다음 세 증거가 같은 파일에 있을 때만 선언형 호출을
`K-ENC-004`의 네트워크 sink로 인정한다.

1. HTTP 어노테이션이 붙은 인터페이스 메서드 선언
2. 그 인터페이스 타입의 프록시 수신자 선언 또는 생성
3. 같은 수신자의 해당 메서드를 실제로 실행하는 호출

Spring의 동기 반환형과 OpenFeign은 메서드 호출 자체를 실행으로 본다. Spring의 reactive 반환형은
`block()`·`subscribe()`가 이어져야 하고, Retrofit의 `Call` 반환형은 `execute()`·`enqueue()`가
이어져야 한다. Kotlin `suspend` Retrofit 메서드는 직접 호출을 실행으로 본다. endpoint는 Spring·
Retrofit 프록시 생성식이나 `@FeignClient(url=...)`에서 찾고, 외부 `http://`는 high, 스킴 미확인은
medium이라는 기존 신뢰도 정책을 그대로 적용한다. 다른 파일의 인터페이스나 주입 그래프까지
추정하지 않는다.

fixture를 먼저 추가했을 때 두 오탐이 드러났다. 범용 `.send()`를 JDK HttpClient 송신으로 보던
기존 정규식이 C066의 일반 객체를 오인해, 선언된 `HttpClient` 수신자의 `send()`·`sendAsync()`만
인정하도록 좁혔다. 또 선언형 프록시와 같은 변수명이 다른 타입으로 재선언된 C068이 오인되어,
같은 이름에 후보 밖의 명시적 타입이 함께 보이면 보수적으로 선언형 수신자에서 제외한다.

V043~V049와 C058~C068, 훅 계약 22번째 케이스로 Spring HTTP Service·Retrofit·OpenFeign·Kotlin
`suspend`·Spring reactive·JDK HttpClient와 선언만 존재하는 경우, 동명 일반 메서드, 실행되지 않은
반환값, HTTPS, 암호화 payload, 수신자 shadowing을 고정했다. 합성 fixture 117건(위반 49·적법 68)과
훅 계약 22건이 모두 통과한다. 시나리오별 50회 합성 benchmark에서 선언형 세 경로의 `analyze()`
중앙값은 1.257~1.931ms였고, 2,000줄 Java는 114.944ms였다. 실제 코드베이스 재현율·오탐율과
성능은 미측정이다. (D-07, D-08, D-17, D-21)

---

## D-26. 서버 수신 TLS는 코드 신호와 명시적 배포 경계 계약을 함께 요구한다 (검증됨)

제7조 제4항은 개인정보를 인터넷망 구간으로 **송ㆍ수신**하는 경우의 암호화를 요구한다. Spring
Boot는 `server.ssl.*`로 내장 웹 서버 TLS를 설정할 수 있지만, Kubernetes Ingress와 Tomcat은 외부
TLS를 프록시에서 종단하고 애플리케이션까지 내부 HTTP로 전달하는 구조를 공식적으로 지원한다.
따라서 애플리케이션의 포트 8080, `server.ssl.enabled=false`, `Connector.setSecure(false)`만으로
외부 인터넷망 평문 수신을 단정하면 정상 배포를 차단하게 된다.

- Spring Boot 내장 서버 SSL: https://docs.spring.io/spring-boot/how-to/webserver.html#howto.webserver.configure-ssl
- Spring Security HTTP·HTTPS: https://docs.spring.io/spring-security/reference/servlet/exploits/http.html
- Kubernetes Ingress TLS 종단: https://kubernetes.io/docs/concepts/services-networking/ingress/
- Tomcat 프록시와 connector 보안 속성: https://tomcat.apache.org/tomcat-11.0-doc/security-howto.html

서버 수신 sink는 Spring `@RestController`/`@Controller` 문맥에서 요청 매핑과 `@RequestBody`·
`@RequestParam`·`@RequestHeader`·`@PathVariable`·`@ModelAttribute`·`@CookieValue` 요청 바인딩이
한 메서드 선언에 함께 있고, 직접 인자 또는 같은 파일의 Java record/class·Kotlin data class 요청
DTO에 사전 개인정보 후보가 있을 때만 성립한다. 응답 반환값, DTO 선언만 있는 파일, 요청 바인딩이
없는 메서드는 서버 수신 sink가 아니다.

배포 경계는 `.pipa.json.inboundTransport`의 네 필드를 모두 요구한다.

- `exposure`: `internet` 또는 `internal`
- `tlsTermination`: `application`, `trusted_proxy`, `none`
- `httpsOnly`: 외부 평문 HTTP를 허용하지 않으면 `true`
- `evidence`: 실제 애플리케이션·Ingress·Gateway·네트워크 정책의 비어 있지 않은 근거 경로

`internet + none + false + evidence`이면 `plaintext-server-receive` high다. `internet`에서
`application` 또는 `trusted_proxy`가 HTTPS 전용과 근거를 함께 선언하면 통과한다. 근거 있는
`internal`도 제4항의 인터넷망 구간 밖이므로 통과한다. 설정 누락·오타·모순·근거 누락은 보호를
인정하지 않되 코드만으로 외부 평문을 확정할 수도 없어 `unverified-server-receive-tls` medium이다.
weak 별칭은 기존 정책대로 한 단계 내린다.

Spring Security의 HTTP→HTTPS 리다이렉트는 평문 요청에 대한 응답 동작이다. 개인정보 POST 본문이
이미 HTTP 구간을 통과한 사실을 되돌리지 못하므로, `redirectToHttps()`나 `requiresSecure()`만으로
수신 구간이 암호화됐다고 판정하지 않는다. 실제 TLS 종단과 외부 HTTPS 전용 경계가 필요하다.

V050~V054와 C069~C077, 훅 계약 23번째 케이스로 설정 미확인·명시적 외부 평문·Java 직접 인자·
Java POJO·Kotlin DTO·불완전한 프록시 근거·비개인정보·애플리케이션 TLS·신뢰 프록시 TLS·내부 전용·
응답 전용·내부 HTTP connector·서로 무관한 DTO 타입 반례를 고정했다. 합성 fixture 131건
(위반 54·적법 77)과 훅 계약 23건이 모두
통과한다. 시나리오별 50회 합성 benchmark에서 서버 평문 수신 경로의 `analyze()` 중앙값은
0.364ms, 새 프로세스 PreToolUse 전체는 36.637ms였다. 실제 코드베이스 재현율·오탐율과 성능은
미측정이다. (D-03, D-04, D-05, D-07, D-08, D-17, D-21)

---

## D-27. 로그·API 응답은 출력 목적별 최소화로 판정하고 마스킹 부재만으로는 규칙을 만들지 않는다 (검증됨)

현행 개인정보의 안전성 확보조치 기준 제12조 제1항은 개인정보처리시스템에서 개인정보를
출력할 때 용도를 특정하고, 그 용도에 따라 출력 항목을 최소화하도록 요구한다. 조문은 출력의
예로 인쇄·화면표시·파일생성을 명시한다.

- 현행 고시 제12조: https://www.law.go.kr/LSW/admRulSideInfoP.do?admRulSeq=2100000281400&chrClsCd=010201&dashNo=&docCls=jo&joBrNo=00&joNo=0012&urlMode=admRulScJoRltInfoR
- 개인정보보호위원회 「개인정보의 안전성 확보조치 기준 안내서」(2025.11.): https://www.pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS217&mCode=D010030000&nttId=11641

안내서 106쪽은 용도에 따라 출력 항목을 차등 표시하거나 마스킹하는 방법을 활용할 수 있다고
설명하고, 웹페이지 소스 보기로 불필요한 개인정보가 출력되지 않도록 하는 사례를 든다. FAQ
152쪽은 마스킹을 출력 항목 최소화 조치 중 하나로 설명한다. 따라서 다음 경계를 확정한다.

1. 로그 파일 생성과 API·화면 응답은 제12조 제1항의 출력 최소성 검토 대상이 될 수 있다.
2. 개인정보가 로그나 응답에 포함됐다는 사실, 또는 평문이라는 사실만으로 위반은 아니다.
   업무·응답 용도상 필요한 개인정보 출력도 있기 때문이다.
3. `K-LEAK-001/002`는 출력 용도와 그 용도에 허용된 개인정보 항목을 먼저 특정하고, 코드에서
   확인한 출력 항목이 그 범위를 넘을 때만 high를 만들 수 있다. 정책 증거가 없으면 위반을
   확정하지 않는다.
4. `K-ENC-004`는 인터넷망 구간의 암호화 여부를 판정한다. `K-LEAK-002`는 HTTPS 여부와 무관하게
   출력 목적에 비해 항목이 과도한지를 판정한다. 암호화된 과다 응답과 최소화된 평문 응답은
   각각 별도의 규칙에서 판단한다.
5. 제8조와 제2조 제3호는 접속기록에 처리한 정보주체 정보를 포함하도록 요구한다. 로그 개인정보를
   일률적으로 금지하면 이 의무와 충돌할 수 있으므로 `K-LEAK-001`은 로그 sink 전체 금지 규칙이
   아니다.
6. 현행 제12조는 모든 출력값의 일률적 마스킹을 의무화하지 않는다. `K-LEAK-003`은 독립 규칙으로
   구현하지 않는다. 특정 출력 정책이 마스킹을 최소화 수단으로 선택한 경우에만
   `K-LEAK-001/002`의 보호조치 증거로 인정한다.

이에 따라 `K-LEAK-001`은 "평문 로그 유출"에서 "로그 출력 최소화"로, `K-LEAK-002`는
"개인정보가 응답에 실림"에서 "API 응답 최소화"로 범위를 좁히고 제12조 제1항에 연결한다.
둘 다 출력 목적·허용 항목 계약과 fixture를 먼저 설계할 때까지 `planned`로 유지한다.
`K-LEAK-003`은 `article:null`, `deferred`로 둔다. 독립 의무가 없는 규칙에 원문 인용을 억지로
붙이지 않는다. (D-04, D-05, D-09, D-13, D-26)

---

## D-28. 출력 최소화는 파일#메서드별 명시적 정책과 비교하고 정책 미확인은 경고한다 (검증됨)

D-27에서 제12조 제1항은 개인정보 출력 자체를 금지하지 않고 용도에 따른 항목 최소화를
요구한다고 확정했다. 따라서 코드의 개인정보 후보와 로그·응답 sink만으로 high를 만들 수 없다.
`.pipa.json.outputPolicies`에 다음 다섯 필드를 모두 둔다.

- `sink`: `api` 또는 `log`
- `source`: 프로젝트 상대 파일 경로와 메서드명을 연결한 `path/File.java#method`
- `purpose`: 비어 있지 않은 출력 용도
- `allowedItems`: `rules/pii_items.json`의 key 목록. 빈 목록은 개인정보 출력 불허
- `evidence`: 해당 허용 범위를 정한 정책·설계·처리방침 근거 경로

와일드카드와 상위 경로(`..`)를 허용하지 않고, 같은 파일#메서드에 정책이 중복되면 어느 정책도
적용하지 않는다. `purpose`·`evidence` 누락, 알 수 없는 item key, 중복 allowedItems도 완전한
근거로 인정하지 않는다. 이 경우 용도를 추정해 차단하지 않고
`unverified-*-output-purpose` medium 경고를 낸다. 완전한 정책과 코드 출력이 연결되고,
`allowedItems`에 없는 strong 항목이 확인될 때만 `excessive-*` high로 차단한다. weak 별칭은 기존
정책대로 한 단계 낮춘다.

`K-LEAK-002`의 초기 API 범위는 Spring `@RestController`/`@Controller`의 매핑 메서드다. 직접
반환식과 같은 파일의 Java class/record·Kotlin data class 반환 DTO를 본다. 매핑 메서드의 요청
인자 타입은 반환 DTO로 취급하지 않는다. `K-LEAK-001`의 초기 로그 범위는 코드에서 선언된
SLF4J/JUL/Kotlin logger 수신자와 Lombok `@Slf4j`의 직접 로그 인자다. 파일에 Logger라는 단어가
있다는 이유나 일반 객체의 `info()` 호출은 sink로 보지 않는다. 문자열 포맷 안의 개인정보 항목명도
실제 값 인자가 아니므로 제외한다.

마스킹은 여전히 독립 규칙이 아니다. 이번 계약의 `allowedItems`는 항목 허용 여부만 표현하며,
항목별 `full`/`masked` 표현 수준은 아직 판정하지 않는다. 마스킹 함수 이름만으로 보호를 인정하면
구현을 확인할 수 없어 거짓 음성이 생기므로 별도 fixture와 보호조치 계약 전에는 확장하지 않는다.

V055~V062와 C078~C084가 정책 초과 차단, 정책 부재·근거 누락·항목 오타·중복 정책 경고,
weak 신뢰도 하향, 허용 범위, 비개인정보 응답, 요청 DTO 격리, Kotlin 반환 DTO, 일반 `info()`와
포맷 문자열 반례를 고정한다.
훅 계약 24번째 케이스는 실제 `.pipa.json`을 탐색하는 경로에서 API 차단·로그 경고·허용 로그 통과를
확인한다. 합성 fixture 146건(위반 62·적법 84) 기준이며 실제 코드베이스 재현율·오탐율은
미측정이다. (D-03, D-04, D-05, D-08, D-14, D-27)

---

## D-29. 접속기록 구성요소는 명시적 logger 정책의 직접 인자와 외부 공급 근거로 판정한다 (검증됨)

2026-09-06 국가법령정보센터의 현행 「개인정보의 안전성 확보조치 기준」(개인정보보호위원회고시
제2026-9호, 시행 2026-07-01)을 다시 확인했다. 제2조 제3호는 접속기록을 식별자, 접속일시,
접속지 정보, 처리한 정보주체 정보, 수행업무 등을 전자적으로 기록한 것으로 정의하고, 제8조
제1항은 개인정보처리시스템에 접속한 자의 접속기록을 보관·관리하도록 한다. 개인정보보호위원회
안내서 공개 자료도 신규 메뉴·기능이 접속기록 생성 방식과 연결되지 않아 기록이 생성되지 않는
경우를 필수정보 누락 사례로 든다.

일반 업무 로그를 접속기록으로 추정하면 오탐이므로 `.pipa.json.accessLogPolicies`가 지정한
파일#메서드와 코드에서 선언된 SLF4J/JUL/Kotlin logger 또는 Lombok `@Slf4j` 호출이 함께 있을
때만 판정한다. 정책은 다음 구조를 모두 만족해야 한다.

- `source`: 와일드카드·상위 경로가 없는 프로젝트 상대 파일#메서드. 중복 선택자는 허용하지 않음
- `components`: `actorId`, `accessedAt`, `sourceInfo`, `dataSubjectInfo`, `action` 다섯 키
- 각 구성요소: 코드에서 직접 기록하면 exact 식별자의 `argument`, 코드 밖에서 공급하면 허용된
  `external` 공급자 중 정확히 하나
- `evidence`: logger·MDC·보안 컨텍스트 등 외부 공급과 접속기록 설계를 확인할 비어 있지 않은 근거

허용하는 외부 공급자는 역할별로 제한한다. 식별자는 `security_context`·`mdc`, 접속일시는
`logger_timestamp`·`mdc`, 접속지 정보는 `request_context`·`request_mdc`·`mdc`, 처리한 정보주체
정보는 `request_context`·`request_mdc`·`mdc`, 수행업무는 `framework_event`·`request_context`·
`mdc`다. 알 수 없는 문자열 오타가 보호를 끄지 못하게 한다.

완전한 정책과 실제 logger sink가 연결되고, 한 접속기록 호출에서 정책이 `argument`로 지정한
구성요소가 빠질 때만 `missing-access-log-component` high로 차단한다. 정책의 다섯 구성요소,
공급자 또는 근거가 불완전하면 누락을 단정하지 않고 `unverified-access-log-components` medium으로
경고한다. 정책이 없는 일반 logger는 검사하지 않는다. 메서드명이나 `audit`·`accessLog` 같은
단어만으로는 차단도 경고도 하지 않는다.

현재 초기 범위는 이미 존재하는 단일 logger 호출의 구성요소만 본다. 접속기록이 아예 생성되지
않는 경우, 여러 호출을 하나의 전자 기록으로 결합하는 구조, interceptor·AOP가 기록 전체를
생성하는 구조, 제8조의 보관기간·점검·위변조 방지는 판정하지 않는다. V063~V064와 C085~C087이
처리 정보주체 누락 차단, 정책 불완전 경고, 일반 업무 로그 격리, logger timestamp와 MDC·보안
컨텍스트 근거를 고정한다. 훅 계약 25번째 케이스가 실제 설정 탐색 경로의 차단·경고·통과를
확인한다. 합성 fixture 151건(위반 64·적법 87) 기준이며 실제 코드베이스 재현율·오탐율은
미측정이다. (D-03, D-04, D-05, D-08, D-13, D-27, D-28)

---

## D-30. 단말 파일 저장은 파일#메서드별 위치 계약이 완전할 때만 차단한다 (검증됨)

2026-09-06 국가법령정보센터의 현행 「개인정보의 안전성 확보조치 기준」(개인정보보호위원회고시
제2026-9호, 시행 2026-07-01) 제7조 제5항과 제2조 제14호를 다시 확인했다. 제5항은 이용자의
개인정보 또는 이용자가 아닌 정보주체의 고유식별정보·생체인식정보를 개인정보취급자의 컴퓨터,
모바일 기기 및 보조저장매체 등에 저장할 때 안전한 암호 알고리즘으로 암호화하도록 요구한다.
제2조 제14호는 보조저장매체를 개인정보처리시스템·개인용 컴퓨터 등에 쉽게 연결·분리할 수 있는
이동형 하드디스크·USB 메모리 등의 매체로 정의한다.

- 제7조 제5항: https://www.law.go.kr/LSW/admRulSideInfoP.do?admRulSeq=2100000281400&chrClsCd=010201&dashNo=&docCls=jo&joBrNo=00&joNo=0007&urlMode=admRulScJoRltInfoR
- 제2조 제14호: https://www.law.go.kr/LSW/admRulSideInfoP.do?admRulSeq=2100000281400&chrClsCd=010202&docCls=jo&joBrNo=00&joChgYn=N&joNo=0002&langType=Ko&urlMode=admRulScJoRltInfoR

같은 `Files.write()` 코드도 서버 프로세스에서 실행되는지 개인정보취급자의 노트북에서 실행되는지
소스만으로 알 수 없다. 경로 문자열이 `/tmp`나 `/Volumes`라는 이유로 배포 위치와 실제 매체를
추정하면 정상 서버 코드를 막거나 보조저장매체 저장을 놓친다. 따라서
`.pipa.json.localStoragePolicies`를 파일#메서드별 계약으로 둔다.

- `source`: 와일드카드·상위 경로가 없는 프로젝트 상대 파일#메서드. 중복 선택자는 불완전함
- `target`: `workstation`(개인정보취급자의 컴퓨터), `mobile`(모바일 기기),
  `removable_media`(보조저장매체), `server` 중 하나
- `evidence`: 실제 배포·운영·내보내기 설계의 비어 있지 않은 근거

완전한 정책이 보호 대상 위치를 지정하고 원문 개인정보가 명시적 파일 sink에 도달할 때만
`plaintext-device-storage` high를 만든다. weak 별칭은 medium으로 내린다. 파일 sink는 초기 범위에서
Java `Files.write`·`Files.writeString`, 선언된 `FileOutputStream`·`FileWriter`의 `write`·`append`,
Kotlin `File` 수신자의 `writeText`·`writeBytes`·`appendText`·`appendBytes`다. 일반 객체의
`write()`는 sink가 아니다.

정책 누락·오타·중복·근거 누락은 실제 저장 위치를 확정할 수 없으므로
`unverified-device-storage-target` medium 경고로 남긴다. 근거 있는 `server`는 제5항 범위에서만
제외하며 K-ENC-001/003의 영속 저장 규칙을 끄지 않는다. 이용자는 현재 공개 근거 사전의 모든
개인정보 후보를, 비이용자는 법문이 열거한 고유식별정보·생체인식정보만 대상으로 한다.

보호조치는 실제 암호 호출에서 시작한 얕은 값 전파로 확인한다. 비밀번호는 제7조 제1항 단서가
추가로 적용되므로 선언된 `PasswordEncoder` 수신자의 일방향 결과도 보호값으로 인정하고, 일반
이름의 `encode()`는 인정하지 않는다. 로컬 데이터베이스·Android SharedPreferences·iOS 저장 API,
파일 밖 호출 그래프와 매체 자체의 전체 디스크 암호화는 아직 판정하지 않는다.

V065~V069와 C088~C092가 개인정보취급자 컴퓨터 평문 파일 차단, 위치 미확인·불완전 정책 경고,
Kotlin 보조저장매체, 모바일 FileOutputStream, FileWriter, 서버 범위 제외, AES 결과, 비이용자 대상
범위, 일반 `write()` 격리, PasswordEncoder 결과를 고정한다. 훅 계약 26번째 케이스가 실제 설정
탐색 경로의 차단·경고·통과를 확인한다. 합성 fixture 161건(위반 69·적법 92) 기준이며 실제
코드베이스 재현율·오탐율은 미측정이다.
(D-02, D-03, D-04, D-05, D-08, D-13, D-18)

---

## D-31. 변경분 리뷰는 동적 규칙 원본과 최종 파일을 함께 보고 지원 범위를 분리한다 (검증됨)

`skills/pipa-review/SKILL.md`를 Phase 3의 첫 스킬로 만든다. 특정 시점의 규칙 목록과 조항을 스킬에
복사하면 엔진이 바뀔 때 즉시 낡으므로, 실행할 때마다 `rules/rules.json`의 `status: active`,
`rules/articles.md`의 원문, `rules/pii_items.json`의 후보 사전과 대상 프로젝트의 `.pipa.json`을
읽도록 한다. 규칙 ID·신뢰도·조항을 기억으로 만들지 않는다.

변경분 전체는 `git diff` 하나로 표현되지 않는다. staged·unstaged·untracked를 모두 포함하고,
삭제 파일은 diff에서, 생성·수정 파일은 diff와 최종 파일 내용에서 함께 본다. pipa-guard 엔진은
최종 파일 전체를 검사하므로 기존 Finding과 이번 변경이 만들거나 악화한 Finding을 리뷰에서
구분한다. 사용자가 커밋·브랜치·PR·파일 범위를 지정하면 그 범위를 우선한다.

리뷰는 두 층으로 나눈다.

1. 엔진이 지원하는 활성 규칙은 CLI `--json` 결과를 실제 변경과 대조해 `규칙/check`, 신뢰도,
   개인정보 후보, sink, 보호조치 부재, 조항 원문과 수정 방향을 보고한다.
2. planned·deferred 규칙, 지원하지 않는 프레임워크·파일 밖 호출 그래프·운영 통제는 실제 검사
   ID를 붙이지 않고 `지원 범위 밖 확인사항`으로 분리한다. 미지원 구조를 high 위반처럼 말하지 않는다.

CLI 종료코드 `0/1/2/3`도 각각 high 없음/high 있음/검사 파일 없음/엔진 오류로 구분한다. 엔진 오류를
위반으로 오인하거나 조용히 통과시키지 않는다. 결과는 Finding 우선순위 뒤에 변경 경로 전체의
`개인정보 후보 → sink → 보호조치·정책 → 규칙·조항 → 판정` 대응표를 붙인다. 검출이 없어도 검사
범위와 설정, 현재 지원 경계를 밝혀 전체 법령 준수 보증으로 과장하지 않는다.

리뷰 요청 자체는 코드나 외부 시스템 수정 권한이 아니다. 주민등록번호 전체 값과 비밀값은 근거에
싣지 않고, 회사 코드베이스 결과는 외부 서비스·공개 문서·PR 코멘트·이슈로 전송하거나 게시하지
않는다. 실제 코드베이스 결과로 재현율·오탐율이나 제품 효과 수치를 만들지 않는다. (D-07, D-08)

스킬은 조건부 모드나 반복 자동화가 없어 `SKILL.md` 하나로 유지한다. `skill-creator`의 공식
`quick_validate.py`는 이 환경에 PyYAML이 없어 import 단계에서 실행되지 않았다. 저장소의 의존성
금지 원칙에 따라 설치하지 않고, 검증기와 같은 frontmatter 키·hyphen-case 이름·길이·미완성 TODO
검사를 표준 셸 도구로 실행해 통과했다. 실제 리뷰 품질은 다음 적용 단계에서 관찰하고 구체적 실패가
확인될 때 좁게 보완한다.

---

## D-32. 개인정보 흐름도는 코드 연결과 운영 선언을 분리한 증거 그래프로 만든다 (검증됨)

`skills/pipa-flow-map/SKILL.md`를 Phase 3의 두 번째 스킬로 만든다. 흐름도는 저장소 전체 또는 사용자가
지정한 모듈·변경분에서 개인정보 후보의 시작점, 변환·보호조치와 저장·전송·로그·응답 sink를
연결한다. 결과는 Mermaid 그림 하나로 끝내지 않고 안정적인 흐름 ID를 공유하는 증거표와 끊긴 연결·
미확인 경계 표를 함께 둔다. 큰 범위는 모듈·유스케이스·신뢰 경계별로 나눈다.

코드가 보여 주는 값 이동과 실제 배포·운영 맥락은 같은 종류의 증거가 아니다. 따라서 연결선은
`코드 확인`, `.pipa.json`과 비어 있지 않은 근거가 제공하는 `설정 선언`, 직접 잇지 못한 `추론`,
근거가 없는 `미확인`으로 구분한다. 흐름 전체를 하나의 신뢰도 숫자로 뭉개거나 설정 선언을 코드
확인으로 승격하지 않는다. 메서드 안의 대입·인자·반환을 우선 추적하고, 파일 밖 연결은 명시적 호출과
타입·시그니처 또는 DTO 매핑을 확인했을 때만 잇는다. 같은 식별자 이름이나 메서드명만으로 연결과
sink를 만들지 않는다.

규칙과 후보를 스킬에 고정하지 않고 실행할 때마다 플러그인 루트의 `rules/rules.json`,
`rules/articles.md`, `rules/pii_items.json`과 대상 프로젝트의 `.pipa.json`을 읽는다. pipa-guard
Finding은 흐름의 주석으로 대응하되 Finding 부재를 개인정보 흐름 부재나 전체 준수로 해석하지 않는다.
지원하지 않는 프레임워크,
동적 디스패치·리플렉션·메시지 브로커·파일 밖 호출 그래프와 운영 통제는 실제 검사 ID를 붙이지 않은
추가 근거 필요 항목으로 남긴다. CLI 종료코드 `3`은 위반이 아니라 판정 실패로 표시한다.

흐름도와 표에는 실제 개인정보·주민등록번호 전체 값·비밀번호·토큰·키를 넣지 않는다. 사용자가 로컬
출력 경로를 지정하지 않으면 파일을 만들지 않으며, 회사 코드베이스 결과를 외부 서비스·공개 문서·
PR·이슈에 전송하거나 게시하지 않는다. 실제 결과로 재현율·오탐율이나 제품 효과 수치를 만들지
않는다. 산출물은 코드 기반 검토 초안이며 전체 처리 현황 또는 ISMS-P 인증 적합성 보증이 아니다.
(D-07, D-08)

반복되는 결정적 계산이 아니라 증거 구분과 범위 판단이 핵심이므로 별도 스크립트 없이 `SKILL.md`
하나로 유지한다. `skill-creator`의 공식 `quick_validate.py`는 이 환경에 PyYAML이 없어 import
단계에서 실행되지 않았다. 의존성을 추가하지 않고 검증기와 같은 frontmatter 구조·허용 키·
hyphen-case 이름·길이·미완성 TODO 검사를 표준 셸 도구로 실행해 통과했다. 실제 생성 품질은 적용
단계에서 관찰하고 확인된 실패만 좁게 보완한다.

---

## D-33. 감사 에이전트는 읽기 전용으로 엔진과 두 스킬을 조정한다 (검증됨)

`agents/pipa-auditor.md`를 Phase 3의 플러그인 에이전트로 만든다. Claude Code 공식 플러그인 규격은
플러그인 루트의 `agents/*.md`를 자동 발견하고, 에이전트 frontmatter의 `skills`에 지정한 스킬
본문을 시작 시 주입한다. 기본 경로를 사용하므로 매니페스트에 `agents`를 중복 선언하지 않는다.
설치 후 scoped 이름은 `pipa-guard:pipa-auditor`다.

- 플러그인 에이전트 규격: https://code.claude.com/docs/en/plugins-reference#agents
- 에이전트 frontmatter·도구·스킬 규격: https://code.claude.com/docs/en/sub-agents

감사 요청은 코드 수정 권한이 아니다. 에이전트 도구는 `Read`, `Grep`, `Glob`, `Bash`만 허용하고,
Bash도 Git 조회·파일 검색·pipa-guard CLI처럼 읽기 전용인 명령으로 제한한다. WebSearch·WebFetch·
MCP·커넥터와 Write·Edit를 주지 않는다. 플러그인 에이전트에서 지원되지 않는 `permissionMode`,
`hooks`, `mcpServers`도 frontmatter에 넣지 않는다. 모델은 특정 버전에 고정하지 않고 주 세션을
상속하며, 개인정보 흐름 대조에 필요한 reasoning effort만 high로 지정한다.

`pipa-review`와 `pipa-flow-map`을 미리 불러오되 모든 요청에 두 산출물을 강제하지 않는다. 변경
리뷰는 변경분과 Finding 대응표, 흐름도 요청은 Mermaid와 증거·공백 표, 종합 감사는 엔진 판정과
수동 대조 뒤 흐름도를 만든다. 단일 Finding 설명에는 저장소 전체 흐름도를 만들지 않는다. 엔진
Finding은 흐름의 존재 증명이 아니며, 지원 범위 밖 확인사항과 미확인 운영 경계를 high 위반으로
승격하지 않는다.

에이전트와 스킬 본문의 `${CLAUDE_PLUGIN_ROOT}`는 Claude Code가 설치 디렉터리의 절대 경로로
치환하므로, 캐시 위치가 바뀌어도 포함된 엔진과 규칙을 찾을 수 있다. 대상 프로젝트의 지침과
`.pipa.json`은 현재 작업 디렉터리에서 별도로 읽는다. 주민등록번호 전체 값과 비밀값을 출력하지
않고 회사 코드 결과를 외부로 보내거나 실제 결과 수치를 공개하지 않는 D-07·D-08 경계는 모든
모드에 공통으로 적용한다.

Claude Code 2.1.247에서 `claude plugin validate .`를 실행해 구조 검증이 통과했다. 루트
`CLAUDE.md`는 플러그인 컨텍스트로 자동 로드되지 않는다는 기존 경고 1건이 남지만 에이전트 형식
오류는 아니다. 에이전트가 대상 저장소의 `AGENTS.md`와 하위 지침을 시작 시 직접 읽도록 계약해
플러그인 루트 문서의 자동 로드를 전제하지 않는다. 실제 회사 코드에 대한 동작·오탐 평가는 다음
비공개 적용 단계에서 수행한다.

---

## D-34. 시스템 시크릿 키의 HTTP Basic Base64는 정보주체 비밀번호 규칙에서 제외한다 (검증됨)

토스페이먼츠 공개 API 인증 규격은 서버의 시크릿 키 뒤에 콜론을 붙여 Base64로 인코딩하고 Basic
인증 헤더에 넣도록 요구한다. 이때 시크릿 키는 Basic 인증의 사용자 ID 위치에 들어가고 비밀번호
위치는 비어 있다. `credential`은 비밀번호보다 넓은 인증 수단이라는 기존 사전 경계와도 일치한다.
따라서 이런 시스템 API 크리덴셜은 제2조 제8호의 정보주체·개인정보취급자 비밀번호가 아니며,
`K-ENC-002/encoding-not-encryption` 대상에서 제외한다.

- 토스페이먼츠 API 인증: https://docs.tosspayments.com/reference/using-api/authorization
- 토스페이먼츠 결제 API 개요: https://docs.tosspayments.com/en/api-guide

`secretKey`라는 단어를 Base64 문장의 전역 제외 신호로 추가하지 않는다. 그렇게 하면 사용자
`password`와 시스템 시크릿 키가 같은 문장에 있을 때 실제 비밀번호 인코딩까지 숨는다. 대신
`properties.secretKey()` 또는 `properties.getSecretKey()`에서 값을 받은 명시적 대입문의 좌변이
비밀번호 후보일 때만 파일 범위의 시스템 크리덴셜 식별자로 표시한다. 기존 `@Value`,
`@ConfigurationProperties`, 환경변수 등의 직접 설정 신호는 그대로 유지한다.

C093은 공개 결제 API 방식대로 설정 객체의 시크릿 키를 `credential`에 대입한 뒤 Basic 인증용으로
Base64 인코딩하는 적법 경계를 고정한다. V070은 같은 Base64 문장에 사용자 `password`와
`secretKey()`가 함께 있어도 `encoding-not-encryption` high가 유지됨을 고정한다. 합성 fixture는
위반 70건과 적법 93건, 총 163건이 통과한다. 실제 코드베이스의 적용 결과·건수·분포·코드 조각은
D-07에 따라 이 결정 기록에 남기지 않는다. (D-04, D-05, D-07, D-08, D-11)

---

## D-35. Codex는 apply_patch 명령을 패치 전에 재구성해 같은 판정 계약을 적용한다 (검증됨)

Codex 공식 훅 규격에서 파일 편집의 canonical 도구명은 `apply_patch`이고 패치 전문은
`tool_input.command`로 전달된다. 프로젝트 훅은 `<repo>/.codex/hooks.json`에서 읽으며, 동기
`PreToolUse`는 실행 전 차단할 수 있고 `PostToolUse`의 `additionalContext`는 실행 뒤 모델에
경고를 전달한다. 이 규격에 맞춰 `.codex/hooks.json`의 matcher를 `^apply_patch$`로 두고 기존
Claude Code 훅과 같은 high/medium 라우팅을 유지한다.

- Codex Hooks 공식 문서: https://developers.openai.com/codex/hooks/

PreToolUse에서는 Add·Update 패치를 디스크에 쓰지 않고 메모리에서 재구성한다. 한 번의 패치가 여러
Java·Kotlin 파일을 바꾸면 모두 판정하고, 하나라도 high이면 전체 `apply_patch`를 거부한다. 삭제는
새 위반 코드를 만들지 않으므로 건너뛰고, 이동은 목적지 내용을 판정한다. PostToolUse에서는 실제
적용된 목적지 파일을 다시 읽어 medium 경고를 전달한다. 패치 형식이 불완전하거나 기존 문맥을 찾지
못하면 조용히 통과시키지 않고 `systemMessage`로 판정 실패를 알린다.

`tests/run_hooks.py`에 Codex 신규 파일, 기존 파일 Update, 다중 파일, PostToolUse medium, 재구성
실패, 프로젝트 훅 설정 계약을 추가했다. 합성 임시 Git 저장소와 Codex CLI 0.153.2의 실제 세션에서도
high 패치는 적용 전에 차단되어 파일이 생기지 않았고 medium 패치는 적용 뒤 경고가 모델에 전달됐다.
테스트에서만 일회성 `--dangerously-bypass-hook-trust`를 사용했으며 실제 프로젝트에서는 `/hooks`로
현재 정의를 검토하고 신뢰해야 한다.

이번 범위는 `apply_patch`뿐이다. Bash·다른 도구가 임의로 파일을 쓰는 결과는 실행 전에 결정적으로
재구성할 수 없으므로 같은 차단을 약속하지 않는다. 공식 문서도 일부 특수 도구가 훅 경로를 벗어날
수 있어 도구 훅을 완전한 강제 경계가 아니라 guardrail로 보라고 명시한다. 이 제약은 설치 문서에
드러내고, 근거 없이 Bash 명령 전체를 차단 대상으로 넓히지 않는다. (D-03, D-09, D-16)

---

## D-36. Phase 4 배포 단위는 검증된 Codex 매니페스트와 개인 마켓플레이스다 (검증됨)

소스 루트에 `.codex-plugin/plugin.json`을 추가한다. 이름은 폴더와 같은 `pipa-guard`, 버전은
`0.1.0`이며 작성자·설명·스킬 경로와 사용자 인터페이스 메타데이터를 명시한다. Codex 플러그인
검증 규격이 매니페스트의 `hooks` 필드를 받지 않으므로 그 필드는 넣지 않는다. Codex가 기본 위치인
`hooks/hooks.json`을 발견하고, Codex가 호환을 위해 제공하는 `CLAUDE_PLUGIN_ROOT`를 기존 명령에
주입하므로 Claude Code와 같은 번들 훅을 재사용한다.

`plugin-creator`의 기본 개인 흐름에 따라 개인 마켓플레이스에는 `pipa-guard`를 `AVAILABLE`,
인증 시점 `ON_INSTALL`, 범주 `Productivity`로 등록했다. 설치용 소스는 `~/plugins/pipa-guard`,
카탈로그는 `~/.agents/plugins/marketplace.json`이며 `codex plugin add pipa-guard@personal`로
설치했다. 설치본에만 `0.1.0+codex.<UTC 시각>` cachebuster를 붙이고 저장소의 제품 버전은
`0.1.0`으로 유지한다. 이것은 이 컴퓨터의 개인 카탈로그 등록이지 공개 마켓플레이스 게시가 아니다.

Claude Code의 `claude plugin validate --strict .`는 루트 `CLAUDE.md` 경고를 실패로 처리했다.
그 파일은 `AGENTS.md`를 다시 가리키는 네 줄짜리 중복 진입점이고 플러그인 컨텍스트로 로드되지도
않으므로 제거했다. 작업 규약의 단일 출처는 계속 `AGENTS.md`이고, 이 변경으로 엄격 검증이 경고
없이 통과한다. 이는 D-33에 기록한 기존 경고를 해소하는 후속 결정이다.

Codex 공식 플러그인 검증기는 이 환경에 PyYAML이 없어 import 단계에서 중단됐다. 프로젝트 의존성을
추가하지 않고 현재 두 스킬의 단순 `key: value` frontmatter만 읽는 임시 표준 라이브러리 호환층을
사용해 같은 검증 로직을 소스, 개인 마켓플레이스 소스, Codex 설치 캐시 각각에 실행했고 모두
통과했다. 별도로 `tests/run_hooks.py`가 매니페스트 필수 메타데이터, 지원하지 않는 `hooks` 필드
부재, 번들 훅과 설치 루트 명령 연결을 CI 계약으로 고정한다.

마지막으로 엔진이나 규칙을 복사하지 않은 합성 임시 Git 저장소에서 설치된 플러그인만 활성화했다.
실제 Codex CLI 0.153.2 세션에서 AES 비밀번호 high 패치는 파일 생성 전에 차단됐고, 무염 SHA-256
medium 패치는 적용된 뒤 경고가 모델에 전달됐다. 테스트에서만 훅 신뢰 우회 옵션을 사용했으며 실제
새 세션에서는 `/hooks`에서 설치된 훅 정의를 검토하고 신뢰한다. 합성 저장소는 검증 직후 삭제했다.
(D-03, D-07, D-08, D-16, D-35)

---

## D-37. 팀 배포는 private GitHub 저장소의 Git-backed 마켓플레이스로 한다 (검증됨)

`jjudop11/pipa-guard`를 private GitHub 저장소로 만들고 `main`을 기본 브랜치로 사용한다. 저장소
루트가 플러그인 루트이므로 플러그인을 `plugins/pipa-guard` 아래에 중복 복사하지 않는다. 대신
`.agents/plugins/marketplace.json`의 한 항목이 같은 저장소의 HTTPS Git URL과 `main` ref를
가리키는 Git-backed source를 사용한다. 설치 정책은 `AVAILABLE`, 인증 시점은 `ON_INSTALL`, 범주는
`Productivity`로 고정한다.

접근 권한을 받은 팀원의 설치 계약은 다음 두 명령이다.

```bash
codex plugin marketplace add jjudop11/pipa-guard
codex plugin add pipa-guard@pipa-guard
```

private 저장소이므로 GitHub 인증과 저장소 접근 권한이 없는 사람은 설치할 수 없다. 이것은 팀 내부
배포이고 OpenAI의 공개 플러그인 디렉터리 제출이 아니다. 공개 전환이나 공식 디렉터리 제출은 별도의
승인과 개인정보·지원·법적 메타데이터 검토 뒤에 한다.

소유자 계정에서 원격 마켓플레이스 등록과 `pipa-guard@pipa-guard` 설치가 성공했다. 중복 훅 실행을
피하려고 기존 `pipa-guard@personal` 설치는 제거하되 개인 마켓플레이스 원본은 남겼다. 원격 설치본만
활성화한 합성 임시 Git 저장소에서 AES 비밀번호 high 패치가 파일 생성 전에 차단되고 무염 SHA-256
medium 패치는 적용 뒤 모델에 경고되는 것을 다시 확인했다. 합성 저장소는 즉시 삭제했다. 실제 다른
팀원 계정의 권한·설치는 아직 측정하지 않았으므로 확인됐다고 쓰지 않는다. (D-07, D-08, D-35, D-36)

---

## D-38. public 배포는 비식별 현재 스냅샷과 고정 버전의 별도 저장소로 분리한다 (검증됨)

기존 private 개발 저장소의 Git 이력을 복사하지 않고, 비공개 프로젝트 식별자와 내부 상태 문서를
제외한 현재 스냅샷을 `jjudop11/pipa-guard-public`의 새 초기 커밋으로 배포한다. 공개 저장소의 커밋은
GitHub noreply 작성자 주소를 사용한다. `docs/STATE.md`는 세션 인계와 내부 진행 상태를 담는 private
개발 문서이므로 public 배포물에 포함하지 않는다. 공개 사용자가 필요한 범위·설치·한계는 README와
CHANGELOG에 둔다.

Codex 마켓플레이스 이름은 기존 private 배포와 충돌하지 않는 `pipa-guard-public`으로 정하고,
플러그인 source는 `https://github.com/jjudop11/pipa-guard-public.git`의 `v0.1.0` 태그를 가리킨다.
Claude Code도 같은 마켓플레이스 이름과 버전을 사용하되 공식 스키마에 맞는
`.claude-plugin/marketplace.json`의 HTTPS URL source로 배포한다. `github` source는 실제 설치에서
SSH clone을 선택해 SSH host key가 없는 새 환경에서 실패했으므로 사용하지 않는다. Claude Code는
표준 위치의 `hooks/hooks.json`을 자동으로 읽으므로 매니페스트의 `hooks` 필드로 같은 파일을 다시
등록하지 않는다. 실제 설치에서 중복 훅으로 판정되어 플러그인 로드가 실패하는 것을 확인했기 때문이다.
두 제품의 설치 계약은
`tests/run_hooks.py` 한 케이스에서 매니페스트 이름·버전·저장소·태그·번들 훅과 함께 고정한다.

MIT 라이선스 전문과 SECURITY.md를 공개 배포물에 포함한다. GitHub Actions의 기본 토큰 권한은
`contents: read`로 제한하고, 사용하는 공식 action도 검토한 전체 커밋 SHA에 고정한다. 저장소 공개
전에는 fixture·훅·자기 검사, Claude 엄격 검증, Codex 패키지 검증과 고신뢰 비밀값 패턴 검사를 모두
통과해야 한다. 공개 뒤에는 인증 정보가 없는 새 설치 경로에서 Claude Code와 Codex를 각각 검증한다.
공식 플러그인 디렉터리 게시는 이 결정의 범위가 아니다. (D-07, D-08, D-16, D-35, D-36, D-37)

---

## D-39. README·배포 주장은 판정·입출력과 별도 실행 계약으로 고정한다 (검증됨)

fixture harness는 무엇을 검출하는지, 훅 harness는 어떻게 입력받고 내보내는지를 검증하지만 README의
수치·예제·지원 경계와 설정·안전성 주장은 직접 검증하지 않았다. 특히 “위반 코드는 모두 디스크에
닿기 전에 차단되고 모델이 적법하게 다시 쓴다”는 표현은 실제 지원 범위보다 넓다. 사전 차단이
확인된 경로는 Claude Code의 `Write`·`Edit`와 Codex의 `apply_patch`이며 Bash 등 다른 파일 쓰기
경로는 범위 밖이다. 차단 결과는 결정적이지만 그 뒤 모델이 선택하는 수정은 비결정적이므로 제품
보장으로 두지 않는다.

`tests/run_claims.py`를 별도 harness로 둔다. 합성 데이터만 사용해 README 수치·예제·지원 경계,
`.pipa.json` 여덟 키의 판정 영향, 별칭 114개의 sink 없는 단독 필드 오탐 부재, 근거 비식별화,
반복 실행의 byte-identical JSON, 표준 라이브러리·무네트워크·무LLM import 경계, 설치 메타데이터와
플러그인 구성 파일을 10개 계약으로 검증한다.

CI의 주 환경은 Ubuntu·Python 3.12이고 Python 3.10·3.14 호환 행렬에서 같은 네 명령을 다시 실행한다.
실제 원격 설치와 모델의 수정 선택은 계정·네트워크·호스트 버전과 비결정적 모델 동작을 요구하므로
결정적 CI 계약이 아니라 릴리스 전후 수동 검증으로 남긴다. 공개판의 최초 적용 버전은 `v0.1.1`이다.
(D-07, D-08, D-16, D-35, D-36, D-38)

---

## D-40. 실제 호스트에서 발견한 AES 보조 메서드 흐름을 코드 증거로만 전파한다 (검증됨)

public `v0.1.1`을 실제 Claude Code 합성 저장소에 설치해 README 대표 시나리오를 실행했다. 모델은
`Cipher`로 비밀번호를 처리하되, `doFinal(plaintext)` 결과를 지역 변수에 담아 Base64 문자열로
반환하는 `encrypt()` 보조 메서드와 `this.encryptedPassword = encrypt(rawPassword)` 저장 문장을
분리했다. 기존 엔진은 AES 적용 문장에 비밀번호 별칭이 없고 저장 문장에 암호 API가 없어 high를
놓쳤으며, 뒤의 `equals()`만 medium으로 경고했다. 설치 성공과 실제 차단 성공은 다른 계약이라는
사실을 확인했다.

보조 메서드 이름의 `encrypt`만으로는 판정하지 않는다. 같은 메서드 안에서 실제 양방향 암호 API가
만든 지역값이 반환식에 도달하고, 그 확인된 메서드 호출에 비밀번호 후보가 전달될 때만
`K-ENC-002/two-way`를 만든다. `V071_PasswordAesHelperReturn`이 미검출을 재현하며 수정 전
164/165로 실패했고, `C094_AesHelperDoesNotTaintPassword`는 같은 파일의 AES 보조 메서드가
주민등록번호에만 적용되고 비밀번호는 `PasswordEncoder`로 처리되는 경계를 고정한다. 훅 harness에도
실제 `Write` PreToolUse가 이 형태를 deny하는 34번째 계약을 추가한다.

공개된 `v0.1.1`은 움직이지 않고 이 수정은 새 패치 버전 `v0.1.2`로 배포한다. 실제 호스트 E2E는
fixture·입출력 계약을 대체하지 않고, 새로운 생성 형태를 발견해 재현 fixture로 환원하는 릴리스
후 관찰 단계로 사용한다. 실제 회사 코드 결과는 사용하지 않았고 테스트 입력은 전부 합성이다.
(D-03, D-07, D-08, D-16, D-18, D-39)

---

## D-41. 암호 결과 전파는 메서드 범위·호출 인자 자리로 제한한다 (검증됨)

2026-09-09 독립 합성 검증에서 D-40의 구현이 설명보다 넓다는 사실을 확인했다. 파일 전역의
동명 지역 변수, 다른 객체의 동명 호출, 한 문장 안의 무관한 비밀번호 후보가 양방향 암호화로
오탐됐다. 반대로 `"BCrypt"` 문자열을 덧붙이거나 Java 보조 메서드의 `private`을 없애면
AES 비밀번호 저장이 미검출됐다. 기존 165/165 통과는 이 경계를 보장하지 않았다.

이를 수정하는 계약은 다음과 같다. D-40의 이력은 지우지 않고 이 결정으로 보완한다.

1. 구문에 원본 시작·끝 오프셋을 유지한다. 지역 암호값은 실제 메서드 중괄호 범위 안에서,
   문장 실행 순서대로 전파하고 재대입으로 기존 표식을 지운다. 다음 줄 중괄호도 인식한다.
2. 알고리즘 객체를 반환하는 팩토리와 암호 처리 결과를 반환하는 보조 메서드를 구분한다.
   결과에 도달한 매개변수 자리를 요약하고, 호출부의 그 자리에 비밀번호 후보가 있어야 연결한다.
3. 다른 객체의 호출을 로컬 함수와 이름만으로 연결하지 않는다. 객체 접두어가 없는 호출과
   `this` 호출에 한하며, 같은 이름의 선언이 여러 개이면 타입을 추정해 선택하지 않는다.
4. Java의 수식어 없는 메서드도 반환형·이름 구조로 인식하되 return/new·클래스 선언·대입 등을
   메서드 선언으로 오인하지 않는다. Kotlin은 기존 fun 선언을 유지한다.
5. 안전한 해시를 나타내는 신호에서 문자열 리터럴을 제외한다. 실제 알고리즘 선택 문자열은
   암호화 판정에 필요하므로 모든 판정 입력에서 일괄 삭제하지 않는다.
   `PBKDF2`·`Pbkdf2` 단독 문자열이 강한 해시 신호를 켜 보조 호출 검사를 생략하지 않게 한다.

V072·V073·C095~C097을 먼저 넣어 수정 전 165/170 실패를 확인했다. V074~V076·C098~C099는
처리/미처리 인자 자리, this 호출, Kotlin 문자열, 다음 줄 중괄호 경계를 추가로 고정한다.
합성 fixture 175건과 별도 훅 계약 36건을 사용하며, 새 훅 계약은 10개 fixture 각각에
Write·Edit·apply_patch PreToolUse를 적용하고 적법 5개에는 PostToolUse 출력도 없어야 한다.
안전 알고리즘명 리터럴 변형 6개도 세 편집 도구에서 추가로 차단을 확인한다.
기존 기대값을 낮추지 않는다.

이것은 완전한 AST·타입·제어 흐름 분석이 아니다. 다른 객체·동명 선언·파일 밖 호출·임의의
반환값 변환 및 복잡한 분기까지 정확하다고 주장하지 않는다. 로컬 코드 수정과 공개판 배포·설치본
호스트 E2E는 별개이므로, 이번 수정은 공개된 v0.1.2 태그나 캐시를 직접 덮어쓰지 않는다.
(D-03, D-04, D-05, D-08, D-11, D-16, D-40)

---

## D-42. README는 초보자의 설치 안내와 개발자의 보안 설정을 분리한다 (검증됨)

처음 읽는 사람에게는 도구의 역할, 준비물, 사용하는 호스트별 공개 설치, 작동 확인과 지원 한계를
먼저 제공한다. 터미널 명령과 AI 대화창 입력을 구분하며, 마켓플레이스는 공개 배포 저장소이지
공식 추천 등록을 뜻하지 않는다고 설명한다. 기존 기술 설명과 검증 근거는 접힌 상세 안내로
보존하고, 공개 설치본과 미배포 로컬 수정의 차이를 첫 화면에 표시한다.

설치 확인은 실제 프로젝트가 아닌 빈 폴더의 합성 코드로 한다. 파일이 없다는 사실만으로는
성공이 아니며 실제 지원 도구 호출과 플러그인 차단 메시지를 함께 확인해야 한다. 한 예제의
성공을 전체 규칙의 정확성이나 법령 준수로 확대하지 않는다.

`.pipa.json`의 저장 위치·예외·제외·출력 정책은 개발·보안 담당자가 실제 근거로 작성한다.
비개발자에게 예제 설정을 그대로 복사하게 하거나 경고를 없애는 목적으로 보호조치를 낮추게 하지
않는다. Codex 훅 신뢰 승인은 설치와 별개이며, 문서에는 우회 플래그 대신 검토·승인 절차를 둔다.

`tests/run_claims.py` 기존 계약에 앞부분의 안내 구성과 GuardDemo 합성 예제의 high 판정을
추가했다. 기존 정량 수치·두 SHA-1 예제·억제 예제·설정 키 계약은 그대로 유지한다. 설명을 쉽게
바꾸는 것을 이유로 판정 기대값이나 기존 검증 범위를 낮추지 않는다. (D-08, D-16, D-39, D-41)

---

## D-43. 암호 전파는 필요할 때 계산하고 구문만 재사용한다 (검증됨)

D-41의 메서드·인자 경계 수정 후 동일 조건 ABBA 측정에서 대형 입력의 훅 비용 증가가 반복돼
배포를 보류했다. 판정의 정확성을 되돌리지 않고 다음 비용만 줄인다.

1. 비밀번호 규칙에서 실제 전파 조회가 필요한 문장이 처음 나타날 때 파일 전체를 한 번 분석한다.
   호출부 뒤의 팩토리·상수와 지역 범위는 기존과 같이 확인한다.
2. 최초 표식의 기존 패턴(RECEIVER_BINDINGS·TWO_WAY_CRYPTO·GET_INSTANCE_ARG_RE) 합집합이
   정규화된 구문에 없으면 전파가 시작될 수 없으므로 빈 결과를 돌려준다. 별칭을 따로 열거하거나
   알고리즘 선택 문자열을 지워 빠른 경로를 만들지 않는다.
3. 같은 표현식의 호출·리터럴·식별자 해석만 파일 안에서 재사용한다. 팩토리·수신자·입력 의존은
   매 라운드와 메서드 범위에서 다시 조회한다. 전역 캐시나 판정 결과 캐시는 만들지 않는다.
4. 메서드 이름마다 새 정규식을 컴파일하지 않고 기존 호출 토큰 패턴을 재사용한다.

fixture harness에 시간 대신 분석 횟수 계약을 추가했다. 대상 없는 입력은 0회, 암호 시작점 없는
필드는 범위 분석 0회, 기존 상수·팩토리·D-41 경계 fixture는 필요한 분석 1회와 판정 보존을 검사한다.
처음 추가한 계약은 수정 전 합성 Java·Kotlin 2개에서 실패했으며 기존 fixture 기대값은 유지했다.
독립 대조에서도 175개 fixture와 350개 구문 변형의 Finding 전체 필드가 최적화 전과 같았다.

`tests/benchmark_release.py`는 기존 39개 측정에 비밀번호 필드·암호 보조 메서드가 섞인 대형 Java의
훅·analyze 4개를 추가한다. 준비 5회·측정 50회의 ABBA 재측정에서 v0.1.2 대비 대형 기본 입력
PreToolUse 중앙값은 약 36%, 암호 보조 메서드 입력은 약 4% 감소했다. 작은 훅 시간의 일부 증가는
감추지 않고 PERFORMANCE와 전체 JSON에 기록한다. 고정 시간 임계값을 CI 합격선으로 만들지 않는다.

이 검증을 근거로 새 패치 v0.1.3 배포를 준비한다. 기존 태그는 이동하지 않으며 public main 반영은
별도 브랜치의 필수 CI를 확인한 뒤 PR로 진행한다. 설치 캐시 갱신과 실제 호스트 재검증은 별개다.
(D-08, D-16, D-17, D-38, D-41)
