# pipa-guard 작업 규약

이 파일은 이 저장소에서 작업하는 모든 에이전트(Claude Code, Codex, 그 외)의 공통 진입점이다.
**세션을 이어받았다면 이 파일 → `docs/DECISIONS.md` 순서로 읽고 시작한다.**

## 이 프로젝트가 무엇인가

개인정보 보호 관련 한국 법령·고시를 **지원하는 코드 편집 도구가 실행되는 순간에** 적용하는
에디터 훅 플러그인이다. Claude Code의 `Write`·`Edit`와 Codex의 `apply_patch`에서 high 위반을
디스크 기록 전에 차단하고, 차단 이유로 조항 원문과 수정 방향을 돌려준다. Bash 등 다른 파일
쓰기 경로와 모델의 구체적인 재작성 결과는 보장 범위가 아니다.

사용자 소개용 설명은 `README.md`에 있다. 이 파일은 **작업 규약**만 담는다.

## 첫 명령

```bash
python3 tests/run_fixtures.py     # 판정.        종료코드 0 = 전체 통과. 현재 163/163.
python3 tests/run_hooks.py        # 입출력·패키지 계약. 종료코드 0 = 전체 통과. 현재 33/33.
python3 tests/run_claims.py       # README·배포 주장. 종료코드 0 = 전체 통과. 현재 10/10.
python3 bin/pipa_check.py .       # 자기 검사.    차단 0 / 경고 0. exclude 회귀 방어.
```

이 네 명령이 이 프로젝트의 상태를 기계가 읽을 수 있게 표현한 것이고, CI가 도는 것과 같다.
문서와 harness가 어긋나면 **harness가 옳다.** 문서를 고쳐라.

앞의 세 harness는 보는 계층이 다르다. `run_fixtures.py`는 `analyze()`를 직접 불러 **무엇을
검출하는가**를, `run_hooks.py`는 엔진을 하위 프로세스로 실행해 **어떻게 내보내는가**(stdout
JSON·종료코드·실패 신호)와 Codex 프로젝트 훅·플러그인 패키지 연결을 고정한다. `run_claims.py`는
README 수치·예제·지원 경계와 설정·비식별화·결정성·무의존성 주장을 실제 구현에 연결한다. 하나라도
통과하지 않으면 깨진 상태다. (D-16, D-35, D-36, D-39)
네 번째는 저장소 자신을 훑어 `.pipa.json`의 `exclude`가 fixture를 계속 제외하는지 본다.

## 절대 규칙

1. **fixture 없는 규칙 추가 금지.** 규칙을 만들면 `fixtures/violation/`에 검출되어야 하는
   케이스와 `fixtures/compliant/`에 검출되면 안 되는 케이스를 같은 커밋에 넣는다.
   적법 fixture가 없는 규칙은 오탐 방어가 없는 규칙이다.
   **medium 검사도 예외가 아니다.** 차단하지 않는 검사는 위반 쪽에
   `// pipa-fixture-expect-warn: <rule>/<check>`(경고로 나와야 하고 high로 올라가면 실패),
   적법 쪽에 `// pipa-fixture-expect-clean`(경고도 0건)으로 고정한다. 신뢰도가 곧 차단
   여부이므로 신뢰도까지 계약이다. (D-03)

2. **harness 목표를 낮춰서 통과시키지 않는다.** 실패하면 엔진을 고친다.
   기대값을 지우거나 fixture를 쉽게 바꾸는 것은 실패를 숨기는 것이다.

3. **필드명만으로 차단하지 않는다.** 차단은 세 조건이 모두 성립할 때만 한다.
   (개인정보 후보) AND (보호 대상 sink 도달) AND (보호 장치 부재).
   근거는 `docs/DECISIONS.md` D-04, D-05.

4. **사전 별칭은 공개 출처만.** 행정안전부 행정표준용어, 공공데이터포털 표준 데이터 항목,
   공개된 본인확인·PG API 규격, 공개 저장소, 일반 약어 관행. 출처를 명시할 수 없는 항목은
   등재하지 않는다. **특정 조직의 내부 스키마를 옮겨 적지 않는다.** (D-07)
   별칭을 추가하면 `tests/dictionary_cases.json`에 `match` 케이스를 넣고, 등재하지 않기로
   한 유사 식별자는 `no_match`에 넣는다. 활성 규칙의 코드 fixture가 모든 별칭을 실행하지는
   않으므로 사전은 별도 계약으로 검증한다. (D-15)

5. **회사 코드베이스에 대한 실행 결과를 어떤 형태로도 공개하지 않는다.**
   검출 건수, 규칙 분포, 익명화한 코드 조각 모두 포함이다. (D-07)

6. **측정하지 않은 수치를 만들지 않는다.** fixture 기준 수치는 반드시
   "합성 fixture N건 기준"으로 표기한다. 실제 코드베이스 재현율·오탐율은 측정 전까지
   존재하지 않는 것으로 다룬다. (D-08)

7. **주민등록번호 전체 값을 로그·문서·보고서에 남기지 않는다.** 검출기 자신도 지킨다.
   보고서에 실리는 근거 코드는 `redact()`를 통과해야 한다. fixture는 전부 합성 데이터다.

8. **의존성 추가 금지.** 훅은 모든 편집마다 실행된다. Python 3 표준 라이브러리만 쓴다.
   네트워크 호출도, LLM 호출도 하지 않는다. 판정은 결정적이어야 한다.

9. **조항 원문을 요약하거나 의역하지 않는다.** `rules/articles.md`에 원문 그대로 두고,
   Finding의 `quote`는 그것을 그대로 인용한다. 법령 원문은 저작권법 제7조 제1호에 따라
   자유롭게 인용할 수 있다. 요약하는 순간 근거로서의 가치가 사라진다.

10. **한국어로 쓴다.** 코드 주석, Finding 메시지, 문서 전부. 조항 용어를 그대로 써야
    개발자가 고시를 찾아볼 수 있다.

## 구조

```
.claude-plugin/plugin.json   플러그인 매니페스트
.claude-plugin/marketplace.json  public GitHub 배포용 Claude Code 마켓플레이스
.codex-plugin/plugin.json    Codex 플러그인 매니페스트. hooks 필드는 기본 발견을 사용해 생략
.agents/plugins/marketplace.json  public GitHub 배포용 Codex 마켓플레이스
hooks/hooks.json             PreToolUse(차단) + PostToolUse(경고), matcher "Write|Edit"
.codex/hooks.json            Codex 프로젝트 훅. apply_patch 전 차단 + 이후 경고
bin/pipa_check.py            엔진. 훅 모드와 CLI 모드를 겸한다. 표준 라이브러리만.
rules/articles.md            조항 원문 + 출처 메타데이터 + 해석 메모 + 규칙↔조항 대응표
rules/rules.json             규칙 ID·조항 연결의 단일 출처. harness가 엔진과의 정합을 검사한다.
rules/pii_items.json         개인정보 항목 사전. _meta.source_policy 를 반드시 지킨다.
rules/alias_sources.json     사전 별칭별 공개 근거. harness가 pii_items와 전수 정합을 검사한다.
tests/dictionary_cases.json  사전 매칭 기대값(match)과 비매칭 방어선(no_match).
fixtures/violation/          검출되어야 하는 코드. 헤더에 // pipa-fixture-expect: <rule>/<check>
fixtures/compliant/          검출되면 안 되는 코드. 오탐 방어선.
tests/run_fixtures.py        판정 harness. 재현율 100% / 오탐 0 을 확인한다.
tests/run_hooks.py           계약 harness. 훅 stdin/stdout·CLI 종료코드·Codex 패키지를 고정한다.
tests/run_claims.py          README 수치·예제·지원 경계와 설정·안전성·배포 주장을 고정한다.
tests/benchmark_hooks.py     합성 입력 훅 성능 기준선. CI 합격 조건이 아니라 전후 비교용이다.
skills/pipa-review/SKILL.md  변경분 전체를 활성 규칙·조항 원문과 대응해 리뷰한다.
skills/pipa-flow-map/SKILL.md  코드·설정 증거를 구분해 개인정보 흐름도와 공백 표를 만든다.
agents/pipa-auditor.md       두 스킬과 엔진 판정을 조정하는 읽기 전용 감사 에이전트다.
.github/workflows/fixtures.yml  push·PR마다 위 네 명령. 자기 검사는 종료코드별로 진단한다.
.pipa.json                   이 저장소 자신의 설정. fixtures/ 를 제외해 자기 차단을 막는다.
.pipa.json.example           사용자용 템플릿. 각 키의 법적 근거를 주석으로 달아 두었다.
docs/DECISIONS.md            확정된 판단과 근거. append-only. 뒤집을 때는 지우지 말고 추가한다.
docs/PERFORMANCE.md          합성 입력 기준 훅 성능 측정 방법과 기준선. 실제 회사 결과는 기록 금지.
```

## 엔진을 만질 때

`bin/pipa_check.py`의 판정 흐름은 이렇다.

```
훅 stdin / CLI 인자
  → resulting_text()      Write는 content, Edit는 패치 후 파일을 재구성 (D-09)
  → find_config()         위로 올라가며 .pipa.json 탐색, 없으면 가장 보수적 기본값
  → is_excluded()         exclude 패턴에 걸리면 종료
  → strip_comments()      오프셋·행번호 보존. 문자열 리터럴 내용은 남긴다.
  → split_statements()    ;{}\n 로 자르고 미완결이면 재병합. Kotlin(세미콜론 없음) 대응.
  → collect_ignores()     pipa-guard:ignore. 이유 필수. 범위는 구문 단위 (D-10)
  → RULES 각각            Finding 생성
  → analyze()             억제 적용, (신뢰도 내림, 행 오름) 정렬
  → high 있으면 deny / 아니면 PostToolUse 경고 (D-03)
```

새 규칙은 `rule_*(src, dic) -> list[Finding]` 함수로 만들고 `RULES`에 등록한다.
`Finding`에는 `article`과 `quote`를 반드시 채운다. 근거 없는 차단은 하지 않는다.

**규칙 ID는 `rules/rules.json`에 먼저 등재한다.** 규칙 ID를 문서 여러 곳에 손으로 적으면
반드시 어긋난다. harness가 (1) `status: active` 규칙의 검사 목록과 엔진이 실제로 생성하는
`(rule, check)` 집합 (2) `rules/articles.md`에 등장하는 규칙 ID (3) 근거 조항이 확정된
규칙의 문서 등재를 검사한다. 근거 조항이 확정되지 않은 규칙은 `article: null`로 두고
구현하지 않는다. 규칙 9 때문에 원문 인용 없이는 Finding을 만들 수 없다.

**파일 범위 얕은 전파**가 두 곳에 있다. 문장 하나만 보면 판정할 수 없는 경우를 위한 것이다.
- `_config_credential_idents()` — 설정 주입 크리덴셜 식별자를 표시해 대상에서 뺀다
- `_crypto_receivers()` — 알고리즘을 담은 변수를 표시해 적용 문장에서 판정한다

전파를 넓힐 때는 반드시 적법 fixture를 먼저 추가해서 새지 않는지 확인한다. `C011`이 그 예다.

**규칙이 사전에서 대상을 고를 때는 분류(`category`)가 아니라 조항이 요구하는 조치로 고른다.**
`K-ENC-002`는 제7조 제1항 단서 규칙이므로 `encryption == "one_way_only"` 항목만 본다.
분류로 고르면 생체인식정보(제2조 제11호의 인증정보이지만 양방향 암호화가 적법하다)가 걸려
오탐이 된다. 방어선은 `C015`다.

**진입점의 실패는 조용할 수 없다.** 훅 모드의 종료코드는 언제나 0이다(편집 흐름을 깨뜨리지
않는다). 그래서 판정하지 못한 경우 `undetermined()`로 `systemMessage`를 내보낸다. 적법한 코드가
통과할 때도 출력이 없으므로, 신호가 없으면 "검사해서 문제없음"과 "검사하지 못함"이 구별되지
않는다. 다만 "검사 대상이 아님"(확장자·`exclude`·검사할 텍스트 없음)은 정상 통과이므로 조용하다.

CLI 종료코드는 `0` 위반 없음 / `1` high 위반 / `2` 검사할 파일 없음 / `3` 엔진 오류다.
**3을 1과 합치지 않는다.** CI가 "위반을 찾았다"와 "엔진이 깨졌다"를 구별해야 한다. 실제로
합쳐져 있어서 사전이 깨진 것을 exclude 설정 문제로 오진했다. (D-16)

예외 메시지를 사용자에게 그대로 싣지 않는다. 소스 조각이 섞일 수 있으므로 종류
(`type(exc).__name__`)만 싣는다. (규약 7)

## 커밋

한 커밋 = 한 가지 변경. 규칙 추가는 fixture와 함께. 커밋 전에 harness를 돌린다.
커밋 메시지는 한국어로, 무엇을 왜 바꿨는지 쓴다. 조항이 근거면 조항 번호를 적는다.
