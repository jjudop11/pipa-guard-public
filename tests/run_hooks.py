#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""훅·CLI 계약 harness.

`tests/run_fixtures.py`는 **판정**을 고정한다. `pipa_check.analyze()`를 직접 부르므로
진입점의 입출력 계약은 하나도 검사하지 않는다. 그 틈에서 실제로 문제가 생겼다.
사전이 깨지면 훅은 아무 신호 없이 통과시키고(보호가 사라진 것을 아무도 모른다), CLI는
traceback + 종료코드 1로 죽어서 "위반을 찾았다"와 구별되지 않았다.

그래서 이 harness는 엔진을 **하위 프로세스로 실행한다.** stdin에 훅 이벤트 JSON을 넣고
stdout·stderr·종료코드를 본다. 판정 결과가 아니라 계약이 검사 대상이다.

고정하는 계약

  훅 모드 (인자 없음, stdin에 이벤트 JSON)
    종료코드는 언제나 0이다. 훅이 편집 흐름 자체를 깨뜨리지 않는다. 차단은 stdout JSON의
    permissionDecision=deny 로만 표현한다. (D-03)
      PreToolUse  + high        → permissionDecision=deny + 조항 원문
      PreToolUse  + medium/low  → 출력 없음 (차단하지 않는다)
      PostToolUse + medium/low  → additionalContext
      PostToolUse + high        → 출력 없음 (차단은 PreToolUse의 일이다)
      검사 대상 아님             → 출력 없음
      판정 실패                  → systemMessage (정상 통과와 구별되어야 한다)

  CLI 모드 (인자 있음)
      0  위반 없음
      1  high 위반 있음
      2  사용법 오류 — 검사할 파일이 없다
      3  엔진 오류 — 판정하지 못했다 (1과 구별되어야 한다. CI가 오진한다)
    오류 메시지는 stderr에 `pipa-guard: ` 로 시작한다. traceback을 노출하지 않는다.

  $ python3 tests/run_hooks.py
  종료코드 0 = 전체 통과
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "bin", "pipa_check.py")
CODEX_HOOKS = os.path.join(ROOT, ".codex", "hooks.json")
CODEX_PLUGIN_MANIFEST = os.path.join(ROOT, ".codex-plugin", "plugin.json")
CLAUDE_PLUGIN_MANIFEST = os.path.join(ROOT, ".claude-plugin", "plugin.json")
CLAUDE_MARKETPLACE = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
PLUGIN_HOOKS = os.path.join(ROOT, "hooks", "hooks.json")
REPO_MARKETPLACE = os.path.join(ROOT, ".agents", "plugins", "marketplace.json")

# 반복 실행하므로 .pyc 를 남기지 않는다. 남은 바이트코드가 오래된 엔진으로 판정한 적이 있다.
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

CASES: list[tuple[str, object]] = []


def case(title: str):
    def deco(fn):
        CASES.append((title, fn))
        return fn
    return deco


# --------------------------------------------------------------------------- #
# 도구
# --------------------------------------------------------------------------- #

def engine(argv: list[str], stdin_text: str = "", exe: str = ENGINE):
    """엔진을 하위 프로세스로 실행한다. -> (종료코드, stdout, stderr)"""
    proc = subprocess.run(
        [sys.executable, exe] + argv,
        input=stdin_text, capture_output=True, text=True, env=ENV, cwd=ROOT,
    )
    return proc.returncode, proc.stdout, proc.stderr


def event(name: str, tool: str, **tool_input) -> str:
    return json.dumps(
        {"hook_event_name": name, "tool_name": tool, "tool_input": tool_input},
        ensure_ascii=False,
    )


def codex_event(name: str, cwd: str, command: str) -> str:
    """Codex apply_patch 훅의 공식 입력 형태를 만든다."""
    return json.dumps({
        "session_id": "pipa-hook-test",
        "turn_id": "pipa-hook-test-turn",
        "transcript_path": None,
        "cwd": cwd,
        "hook_event_name": name,
        "model": "test-model",
        "permission_mode": "default",
        "tool_name": "apply_patch",
        "tool_use_id": "pipa-hook-test-tool",
        "tool_input": {"command": command},
    }, ensure_ascii=False)


def codex_add_file_patch(path: str, content: str) -> str:
    added = "\n".join("+" + line for line in content.splitlines())
    return "*** Begin Patch\n*** Add File: %s\n%s\n*** End Patch" % (path, added)


def fixture(kind: str, name: str) -> str:
    """fixture 내용을 재사용한다. 위반 샘플을 여기에 또 적으면 반드시 어긋난다."""
    with open(os.path.join(ROOT, "fixtures", kind, name), "r", encoding="utf-8") as fp:
        return fp.read()


def put(tmp: str, rel: str, text: str) -> str:
    path = os.path.join(tmp, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(text)
    return path


def broken_engine(tmp: str, mode: str) -> str:
    """사전을 읽을 수 없는 엔진 사본을 만든다.

    PLUGIN_ROOT 를 __file__ 기준으로 잡으므로 사본을 <tmp>/bin/ 에 두면 사전 경로가
    <tmp>/rules/pii_items.json 이 된다. 테스트용 우회 스위치를 엔진에 넣지 않으려고
    이 방식을 쓴다. 실제 실패 경로를 그대로 탄다.
    """
    dst = os.path.join(tmp, "bin", "pipa_check.py")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(ENGINE, dst)
    if mode == "invalid":            # 파일은 있지만 JSON이 깨졌다 -> ValueError
        put(tmp, "rules/pii_items.json", "{ this is not json")
    # mode == "missing" 이면 rules/ 자체를 만들지 않는다 -> OSError
    return dst


def want(problems: list[str], cond: bool, msg: str) -> None:
    if not cond:
        problems.append(msg)


def parsed(problems: list[str], out: str):
    """stdout 이 단일 JSON 객체인지 확인하고 파싱한다."""
    try:
        data = json.loads(out)
    except ValueError:
        problems.append("stdout이 JSON이 아니다: %r" % out[:120])
        return {}
    if not isinstance(data, dict):
        problems.append("stdout이 객체가 아니다: %r" % out[:120])
        return {}
    return data


def hook_specific(problems: list[str], out: str, expect_event: str):
    data = parsed(problems, out)
    hso = data.get("hookSpecificOutput") or {}
    want(problems, isinstance(hso, dict) and bool(hso), "hookSpecificOutput 이 없다")
    if isinstance(hso, dict):
        want(problems, hso.get("hookEventName") == expect_event,
             "hookEventName 이 %s 가 아니다: %r" % (expect_event, hso.get("hookEventName")))
    return hso if isinstance(hso, dict) else {}


VIOLATION_HIGH = "V001_PasswordAesEntity.java"     # cipher.doFinal(rawPassword...) — high
VIOLATION_WARN = "V010_PasswordUnsaltedSha256.java"  # salt·반복 없는 SHA-256 — medium
COMPLIANT = "C001_BCrypt.java"
VIOLATION_USER_STORAGE = "V012_ResidentNumberPlainColumn.java"
VIOLATION_NON_USER_RESIDENT = "V020_NonUserInternalResidentPlainColumn.java"
COMPLIANT_NON_USER_ASSESSMENT = "C026_NonUserInternalPassportAssessmentExemption.java"
VIOLATION_PLAIN_HTTP = "V025_PlainHttpResidentTransmission.java"
VIOLATION_UNKNOWN_TRANSPORT = "V027_UnknownTransportDriverLicense.java"
COMPLIANT_HTTPS = "C031_HttpsResidentTransmission.java"
VIOLATION_PLAIN_HTTP_DTO = "V031_PlainHttpRequestDtoConstructor.java"
VIOLATION_TLS_BYPASS = "V035_HttpsNoopHostnameVerifier.java"
COMPLIANT_HTTPS_DTO = "C041_HttpsRequestDto.java"
COMPLIANT_ENCRYPTED_SETTER = "C045_EncryptedValueInRequestSetter.java"
VIOLATION_SPRING_REST_CLIENT = "V036_PlainHttpSpringRestClient.java"
VIOLATION_OKHTTP = "V037_PlainHttpOkHttpRequest.java"
VIOLATION_APACHE_HTTP = "V038_PlainHttpApacheClient.java"
COMPLIANT_GENERIC_EXECUTE = "C049_GenericExecuteIsNotHttpSend.java"
VIOLATION_GENERAL_NAME = "V039_PlainHttpFullName.java"
VIOLATION_AMBIGUOUS_CONTACT = "V042_PlainHttpAmbiguousContact.java"
COMPLIANT_ORGANIZATION_CONTACT = "C053_OrganizationContactsOverHttp.java"
VIOLATION_SPRING_HTTP_SERVICE = "V043_PlainHttpSpringHttpService.java"
VIOLATION_RETROFIT = "V044_PlainHttpRetrofitCall.java"
VIOLATION_FEIGN = "V045_PlainHttpFeignClient.java"
VIOLATION_UNKNOWN_HTTP_SERVICE = "V046_UnknownSpringHttpServiceEndpoint.java"
VIOLATION_JDK_HTTP_CLIENT = "V047_PlainHttpJdkHttpClient.java"
VIOLATION_KOTLIN_RETROFIT = "V048_PlainHttpKotlinRetrofitSuspend.kt"
VIOLATION_SPRING_REACTIVE = "V049_PlainHttpSpringReactiveSubscribed.java"
COMPLIANT_DECLARATIONS_ONLY = "C058_DeclarativeClientDeclarationsOnly.java"
COMPLIANT_SAME_METHOD = "C059_SameMethodNameOnNonHttpObject.java"
COMPLIANT_HTTPS_SPRING_HTTP_SERVICE = "C060_HttpsSpringHttpService.java"
COMPLIANT_HTTPS_RETROFIT = "C061_HttpsRetrofitCall.java"
COMPLIANT_HTTPS_FEIGN = "C062_HttpsFeignClient.java"
COMPLIANT_RETROFIT_NOT_EXECUTED = "C063_RetrofitCallNotExecuted.java"
COMPLIANT_REACTIVE_NOT_SUBSCRIBED = "C064_SpringReactiveCallNotSubscribed.java"
COMPLIANT_ENCRYPTED_FEIGN = "C065_EncryptedFeignPayload.java"
COMPLIANT_GENERIC_SEND = "C066_GenericSendIsNotJdkHttpClient.java"
COMPLIANT_HTTPS_KOTLIN_RETROFIT = "C067_HttpsKotlinRetrofitSuspend.kt"
COMPLIANT_DECLARATIVE_SHADOWING = "C068_DeclarativeReceiverShadowing.java"
VIOLATION_UNVERIFIED_SERVER_RECEIVE = "V050_UnverifiedSpringServerPiiReceive.java"
VIOLATION_PLAIN_SERVER_RECEIVE = "V051_PlainSpringServerPiiReceive.java"
COMPLIANT_PROXY_TLS_SERVER = "C071_TrustedProxyTlsSpringServer.java"
VIOLATION_EXCESSIVE_API_RESPONSE = "V055_ExcessiveSpringApiResponse.java"
VIOLATION_UNVERIFIED_LOG_OUTPUT = "V058_UnverifiedSlf4jLog.java"
COMPLIANT_ALLOWED_LOG_OUTPUT = "C080_AllowedAuditLog.java"
VIOLATION_MISSING_ACCESS_LOG_SUBJECT = "V063_MissingAccessLogSubject.java"
VIOLATION_INCOMPLETE_ACCESS_LOG_POLICY = "V064_IncompleteAccessLogPolicy.java"
COMPLIANT_COMPLETE_ACCESS_LOG = "C085_CompleteAccessLog.java"
VIOLATION_WORKSTATION_FILE = "V065_WorkstationPlaintextFile.java"
VIOLATION_UNVERIFIED_LOCAL_STORAGE = "V066_UnverifiedLocalStorageTarget.java"
COMPLIANT_SERVER_FILE_STORAGE = "C088_ServerFileStorage.java"


# --------------------------------------------------------------------------- #
# 훅 모드 — 라우팅
# --------------------------------------------------------------------------- #

@case("PreToolUse + high → deny, 종료코드 0")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", "Member.java"),
        content=fixture("violation", VIOLATION_HIGH),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    want(problems, hso.get("permissionDecision") == "deny",
         "permissionDecision 이 deny 가 아니다: %r" % hso.get("permissionDecision"))

    reason = hso.get("permissionDecisionReason") or ""
    # 규약 9 — 차단 이유에는 조항 원문이 그대로 실린다. 요약하면 근거로서의 가치가 없다.
    want(problems, "제7조" in reason, "차단 이유에 조항 번호가 없다")
    want(problems, "일방향 암호화" in reason, "차단 이유에 조항 원문이 없다")
    # 억제 지시자는 의도적으로 안내하지 않는다. 에이전트가 고치는 대신 도망가는 것을 막는다.
    want(problems, "pipa-guard:ignore" not in reason, "차단 이유가 억제 지시자를 안내한다")
    want(problems, err == "", "stderr 에 출력이 있다: %r" % err[:120])
    return problems


@case("PreToolUse + medium → 출력 없음 (차단하지 않는다)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", "Member.java"),
        content=fixture("violation", VIOLATION_WARN),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "medium 인데 PreToolUse 가 출력했다: %r" % out[:160])
    return problems


@case("PostToolUse + medium → additionalContext")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    # PostToolUse 는 디스크의 파일을 읽는다.
    path = put(tmp, "src/Member.java", fixture("violation", VIOLATION_WARN))
    code, out, err = engine([], event("PostToolUse", "Write", file_path=path))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PostToolUse")
    want(problems, bool(hso.get("additionalContext")), "additionalContext 가 비어 있다")
    want(problems, "permissionDecision" not in hso,
         "PostToolUse 가 permissionDecision 을 냈다")
    return problems


@case("PostToolUse + high → 출력 없음 (차단은 PreToolUse의 일이다)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    path = put(tmp, "src/Member.java", fixture("violation", VIOLATION_HIGH))
    code, out, err = engine([], event("PostToolUse", "Write", file_path=path))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "high 를 PostToolUse 가 다시 보고했다: %r" % out[:160])
    return problems


@case("PreToolUse + 적법 → 출력 없음")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", "Member.java"),
        content=fixture("compliant", COMPLIANT),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "적법한데 출력이 있다: %r" % out[:160])
    want(problems, err == "", "stderr 에 출력이 있다: %r" % err[:120])
    return problems


@case("PreToolUse + Edit → 패치 결과를 검사한다 (D-09)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    path = put(tmp, "src/Member.java", fixture("compliant", COMPLIANT))
    with open(path, "r", encoding="utf-8") as fp:
        current = fp.read()
    old = "passwordEncoder.encode(rawPassword)"
    want(problems, old in current, "%s 에 %r 가 없다 — 케이스가 낡았다" % (COMPLIANT, old))
    if problems:
        return problems
    code, out, err = engine([], event(
        "PreToolUse", "Edit", file_path=path,
        old_string=old, new_string="aesUtil.encrypt(rawPassword)",
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    want(problems, hso.get("permissionDecision") == "deny",
         "패치 결과가 위반인데 차단하지 않았다: %r" % out[:160])
    return problems


@case("Codex PreToolUse + apply_patch 신규 파일 → deny")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    patch = codex_add_file_patch("src/Member.java", fixture("violation", VIOLATION_HIGH))
    code, out, err = engine([], codex_event("PreToolUse", tmp, patch))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    want(problems, hso.get("permissionDecision") == "deny",
         "Codex 신규 파일 위반을 차단하지 않았다: %r" % out[:160])
    return problems


@case("Codex PreToolUse + apply_patch 기존 파일 → 패치 결과 deny")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    path = put(tmp, "src/Member.java", fixture("compliant", COMPLIANT))
    old = "        member.applyPassword(passwordEncoder.encode(rawPassword));"
    new = "        member.applyPassword(Base64.getEncoder().encodeToString(rawPassword.getBytes()));"
    patch = "\n".join([
        "*** Begin Patch",
        "*** Update File: src/Member.java",
        "@@",
        "-" + old,
        "+" + new,
        "*** End Patch",
    ])
    code, out, err = engine([], codex_event("PreToolUse", tmp, patch))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    want(problems, hso.get("permissionDecision") == "deny",
         "Codex 기존 파일의 패치 결과를 차단하지 않았다: %r" % out[:160])
    with open(path, "r", encoding="utf-8") as fp:
        want(problems, fp.read() == fixture("compliant", COMPLIANT),
             "PreToolUse가 검사 중 실제 파일을 바꿨다")
    return problems


@case("Codex apply_patch 다중 파일 중 위반 하나라도 → deny")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    clean = codex_add_file_patch("src/Clean.java", fixture("compliant", COMPLIANT))
    violation = codex_add_file_patch("src/Violation.java", fixture("violation", VIOLATION_HIGH))
    patch = clean.removesuffix("\n*** End Patch") + "\n" + violation.removeprefix("*** Begin Patch\n")
    code, out, err = engine([], codex_event("PreToolUse", tmp, patch))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    want(problems, hso.get("permissionDecision") == "deny",
         "Codex 다중 파일 위반을 차단하지 않았다: %r" % out[:160])
    return problems


@case("Codex PostToolUse + apply_patch medium → additionalContext")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    put(tmp, "src/Digest.java", fixture("violation", VIOLATION_WARN))
    patch = "\n".join([
        "*** Begin Patch",
        "*** Update File: src/Digest.java",
        "@@",
        "-// before",
        "+// after",
        "*** End Patch",
    ])
    code, out, err = engine([], codex_event("PostToolUse", tmp, patch))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-ENC-002/unsalted-hash" in context,
         "Codex PostToolUse 경고가 없다: %r" % out[:160])
    return problems


@case("Codex apply_patch 재구성 실패 → systemMessage")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    put(tmp, "src/Member.java", fixture("compliant", COMPLIANT))
    patch = "\n".join([
        "*** Begin Patch",
        "*** Update File: src/Member.java",
        "@@",
        "-존재하지 않는 원문",
        "+대체할 수 없는 새 내용",
        "*** End Patch",
    ])
    code, out, err = engine([], codex_event("PreToolUse", tmp, patch))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    data = parsed(problems, out) if out else {}
    want(problems, bool(data.get("systemMessage")),
         "Codex 패치 재구성 실패가 정상 통과와 구별되지 않는다: %r" % out[:160])
    return problems


@case("Codex 프로젝트 훅 설정 → apply_patch Pre/Post 연결")
def _(tmp: str) -> list[str]:
    del tmp
    problems: list[str] = []
    try:
        with open(CODEX_HOOKS, "r", encoding="utf-8") as fp:
            config = json.load(fp)
    except (OSError, ValueError) as exc:
        return [".codex/hooks.json을 읽을 수 없다: %s" % type(exc).__name__]

    hooks = config.get("hooks") if isinstance(config, dict) else None
    want(problems, isinstance(hooks, dict), "hooks 객체가 없다")
    if not isinstance(hooks, dict):
        return problems
    for event_name in ("PreToolUse", "PostToolUse"):
        groups = hooks.get(event_name)
        want(problems, isinstance(groups, list) and len(groups) == 1,
             "%s matcher 그룹이 정확히 하나가 아니다" % event_name)
        if not isinstance(groups, list) or len(groups) != 1:
            continue
        group = groups[0]
        matcher = group.get("matcher") if isinstance(group, dict) else None
        want(problems, isinstance(matcher, str) and re.search(matcher, "apply_patch") is not None,
             "%s가 apply_patch와 매칭되지 않는다" % event_name)
        handlers = group.get("hooks") if isinstance(group, dict) else None
        want(problems, isinstance(handlers, list) and len(handlers) == 1,
             "%s command handler가 정확히 하나가 아니다" % event_name)
        if not isinstance(handlers, list) or len(handlers) != 1:
            continue
        handler = handlers[0]
        want(problems, handler.get("type") == "command", "%s handler가 command가 아니다" % event_name)
        command = handler.get("command") or ""
        want(problems, "git rev-parse --show-toplevel" in command and "bin/pipa_check.py" in command,
             "%s command가 저장소 루트의 엔진을 가리키지 않는다" % event_name)
        want(problems, handler.get("async") is not True,
             "%s가 비동기라 차단·경고 시점이 보장되지 않는다" % event_name)
    return problems


@case("Claude·Codex 플러그인 패키지 → public 마켓플레이스·번들 훅 연결")
def _(tmp: str) -> list[str]:
    del tmp
    problems: list[str] = []
    try:
        with open(CODEX_PLUGIN_MANIFEST, "r", encoding="utf-8") as fp:
            manifest = json.load(fp)
        with open(PLUGIN_HOOKS, "r", encoding="utf-8") as fp:
            hook_config = json.load(fp)
        with open(REPO_MARKETPLACE, "r", encoding="utf-8") as fp:
            marketplace = json.load(fp)
        with open(CLAUDE_PLUGIN_MANIFEST, "r", encoding="utf-8") as fp:
            claude_manifest = json.load(fp)
        with open(CLAUDE_MARKETPLACE, "r", encoding="utf-8") as fp:
            claude_marketplace = json.load(fp)
    except (OSError, ValueError) as exc:
        return ["Claude·Codex 플러그인 패키지를 읽을 수 없다: %s" % type(exc).__name__]

    want(problems, manifest.get("name") == "pipa-guard", "플러그인 이름이 pipa-guard가 아니다")
    version = manifest.get("version") or ""
    want(problems, bool(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version)),
         "플러그인 버전이 semver가 아니다: %r" % version)
    want(problems, manifest.get("skills") == "./skills/", "skills 경로가 기본 디렉터리가 아니다")
    want(problems, "hooks" not in manifest,
         "Codex 매니페스트에 지원하지 않는 hooks 필드를 넣었다")
    interface = manifest.get("interface")
    want(problems, isinstance(interface, dict), "interface 객체가 없다")
    if isinstance(interface, dict):
        for field in ("displayName", "shortDescription", "longDescription",
                      "developerName", "category", "capabilities", "defaultPrompt"):
            want(problems, bool(interface.get(field)), "interface.%s가 비어 있다" % field)
    want(problems, "[TODO:" not in json.dumps(manifest, ensure_ascii=False),
         "매니페스트에 미완성 TODO가 남아 있다")
    want(problems, manifest.get("repository") ==
         "https://github.com/jjudop11/pipa-guard-public",
         "Codex 매니페스트가 public 저장소를 가리키지 않는다")

    want(problems, marketplace.get("name") == "pipa-guard-public",
         "Codex 마켓플레이스 이름이 pipa-guard-public이 아니다")
    entries = marketplace.get("plugins")
    want(problems, isinstance(entries, list) and len(entries) == 1,
         "저장소 마켓플레이스 항목이 정확히 하나가 아니다")
    if isinstance(entries, list) and len(entries) == 1 and isinstance(entries[0], dict):
        entry = entries[0]
        source = entry.get("source")
        policy = entry.get("policy")
        want(problems, entry.get("name") == manifest.get("name"),
             "마켓플레이스와 매니페스트의 플러그인 이름이 다르다")
        want(problems, isinstance(source, dict) and source.get("source") == "url" and
             source.get("url") == "https://github.com/jjudop11/pipa-guard-public.git" and
             source.get("ref") == "v0.1.0",
             "Codex 마켓플레이스가 public Git 저장소 v0.1.0을 가리키지 않는다")
        want(problems, isinstance(policy, dict) and
             policy.get("installation") == "AVAILABLE" and
             policy.get("authentication") == "ON_INSTALL",
             "마켓플레이스 설치·인증 정책이 기본 계약과 다르다")
        want(problems, entry.get("category") == "Productivity",
             "마켓플레이스 category가 없다")

    want(problems, claude_manifest.get("name") == manifest.get("name"),
         "Claude·Codex 매니페스트의 플러그인 이름이 다르다")
    want(problems, claude_manifest.get("version") == version,
         "Claude·Codex 매니페스트 버전이 다르다")
    want(problems, claude_manifest.get("repository") == manifest.get("repository"),
         "Claude·Codex 매니페스트의 저장소 URL이 다르다")
    want(problems, claude_marketplace.get("name") == "pipa-guard-public",
         "Claude 마켓플레이스 이름이 pipa-guard-public이 아니다")
    claude_entries = claude_marketplace.get("plugins")
    want(problems, isinstance(claude_entries, list) and len(claude_entries) == 1,
         "Claude 마켓플레이스 항목이 정확히 하나가 아니다")
    if (isinstance(claude_entries, list) and len(claude_entries) == 1 and
            isinstance(claude_entries[0], dict)):
        claude_entry = claude_entries[0]
        claude_source = claude_entry.get("source")
        want(problems, claude_entry.get("name") == manifest.get("name"),
             "Claude 마켓플레이스와 매니페스트의 플러그인 이름이 다르다")
        want(problems, claude_entry.get("version") == version,
             "Claude 마켓플레이스와 매니페스트 버전이 다르다")
        want(problems, isinstance(claude_source, dict) and
             claude_source.get("source") == "url" and
             claude_source.get("url") ==
             "https://github.com/jjudop11/pipa-guard-public.git" and
             claude_source.get("ref") == "v0.1.0",
             "Claude 마켓플레이스가 HTTPS public Git 저장소 v0.1.0을 가리키지 않는다")

    hooks = hook_config.get("hooks") if isinstance(hook_config, dict) else None
    want(problems, isinstance(hooks, dict), "번들 hooks 객체가 없다")
    if isinstance(hooks, dict):
        for event_name in ("PreToolUse", "PostToolUse"):
            groups = hooks.get(event_name)
            if not isinstance(groups, list) or not groups:
                problems.append("번들 %s 훅이 없다" % event_name)
                continue
            group = groups[0]
            matcher = group.get("matcher") if isinstance(group, dict) else ""
            want(problems, isinstance(matcher, str) and
                 (re.search(matcher, "apply_patch") is not None or
                  re.search(matcher, "Write") is not None or
                  re.search(matcher, "Edit") is not None),
                 "번들 %s가 Codex apply_patch 별칭과 매칭되지 않는다" % event_name)
            handlers = group.get("hooks") if isinstance(group, dict) else None
            command = handlers[0].get("command", "") if isinstance(handlers, list) and handlers else ""
            want(problems, "CLAUDE_PLUGIN_ROOT" in command and "bin/pipa_check.py" in command,
                 "번들 %s가 설치된 플러그인의 엔진을 가리키지 않는다" % event_name)
    return problems


@case("대상 확장자가 아니면 출력 없음")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "docs", "note.md"),
        content=fixture("violation", VIOLATION_HIGH),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", ".md 인데 출력이 있다: %r" % out[:160])
    return problems


@case("exclude 에 걸리면 출력 없음")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    put(tmp, ".pipa.json", json.dumps({"exclude": ["generated/"]}))
    target = os.path.join(tmp, "generated", "Member.java")
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target,
        content=fixture("violation", VIOLATION_HIGH),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "exclude 인데 출력이 있다: %r" % out[:160])

    # 제외 대상은 엔진의 다른 구성요소가 깨져 있어도 검사하지 않는다. 사전을 먼저
    # 읽으면 정상적인 exclude가 "검사 실패" 경고로 바뀌는 회귀가 생긴다.
    broken = broken_engine(tmp, "missing")
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target,
        content=fixture("violation", VIOLATION_HIGH),
    ), exe=broken)
    want(problems, code == 0, "깨진 엔진의 exclude 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "exclude가 사전 오류보다 먼저 적용되지 않았다: %r" % out[:160])

    # 같은 내용을 exclude 밖에 쓰면 차단되어야 한다. exclude 가 규칙 자체를 끄는 것이
    # 아니라는 것을 확인한다.
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=os.path.join(tmp, "src", "Member.java"),
        content=fixture("violation", VIOLATION_HIGH),
    ))
    want(problems, "deny" in out, "exclude 밖인데 차단되지 않았다: %r" % out[:160])
    return problems


@case("subjectType 이 제7조 제2항·제3항 규칙을 중복 없이 분기한다 (D-02)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    target = os.path.join(tmp, "src", "MemberIdentity.java")
    content = fixture("violation", VIOLATION_USER_STORAGE)

    # 이용자가 아닌 정보주체는 제3항 규칙만 적용해야 한다.
    put(tmp, ".pipa.json", json.dumps({"subjectType": "non_user"}))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target, content=content,
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "non_user 제3항 위반을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-ENC-003" in reason, "non_user 결과에 제3항 규칙이 없다")
    want(problems, "K-ENC-001" not in reason, "non_user 결과에 제2항 규칙이 중복됐다")
    want(problems, "이용자가 아닌 정보주체의 개인정보" in reason,
         "제3항 차단 이유에 조항 원문 본문이 없다")
    want(problems, "암호화 미적용시 위험도 분석에 따른 결과" in reason,
         "제3항 차단 이유에 조항 원문 단서가 없다")

    # 같은 코드는 이용자 맥락에서는 제2항에 따라 차단되어야 한다.
    put(tmp, ".pipa.json", json.dumps({"subjectType": "user"}))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target, content=content,
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "user 인데 제2항 위반을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-ENC-001" in reason, "user 결과에 제2항 규칙이 없다")
    want(problems, "K-ENC-003" not in reason, "user 결과에 제3항 규칙이 중복됐다")

    # 오타나 알 수 없는 값으로 보호가 꺼지면 안 된다. non_user만 명시적 예외로 인정한다.
    put(tmp, ".pipa.json", json.dumps({"subjectType": "알_수_없는_값"}))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target, content=content,
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, "deny" in out, "알 수 없는 subjectType이 보호를 껐다: %r" % out[:160])
    return problems


@case("제7조 제3항 내부망 평가 예외는 명시한 항목에만 적용된다 (D-20)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    target = os.path.join(tmp, "src", "AssessedPassportRecord.java")
    passport = fixture("compliant", COMPLIANT_NON_USER_ASSESSMENT)
    valid_assessment = {
        "basis": "privacy_impact_assessment",
        "document": "docs/privacy/impact-assessment-2026.md",
        "date": "2026-08-31",
        "conclusion": "encryption_not_required",
        "exemptItems": ["passportNumber"],
    }

    # 내부망 + 완전한 평가 결과 + 명시된 여권번호 범위에서만 조용히 통과한다.
    put(tmp, ".pipa.json", json.dumps({
        "subjectType": "non_user",
        "storageZone": "internal",
        "riskAssessment": valid_assessment,
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target, content=passport,
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "유효한 내부망 평가 범위인데 출력했다: %r" % out[:160])

    # 같은 결과라도 인터넷망에서는 제1호에 따라 예외가 없다.
    put(tmp, ".pipa.json", json.dumps({
        "subjectType": "non_user",
        "storageZone": "internet",
        "riskAssessment": valid_assessment,
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target, content=passport,
    ))
    want(problems, "deny" in out, "인터넷망에서 평가 결과가 보호를 껐다: %r" % out[:160])

    # 알 수 없는 저장 구간도 internal 예외로 해석하지 않는다.
    put(tmp, ".pipa.json", json.dumps({
        "subjectType": "non_user",
        "storageZone": "알_수_없는_값",
        "riskAssessment": valid_assessment,
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target, content=passport,
    ))
    want(problems, "deny" in out, "알 수 없는 저장 구간이 보호를 껐다: %r" % out[:160])

    # 결론·항목별 범위가 없는 문서 참조만으로는 예외를 인정하지 않는다.
    put(tmp, ".pipa.json", json.dumps({
        "subjectType": "non_user",
        "storageZone": "internal",
        "riskAssessment": {
            "document": "docs/privacy/impact-assessment-2026.md",
            "date": "2026-08-31",
        },
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target, content=passport,
    ))
    want(problems, "deny" in out, "불완전한 평가 설정이 보호를 껐다: %r" % out[:160])

    # 형식만 닮고 실제 달력에 없는 날짜도 완전한 평가 선언이 아니다.
    invalid_date_assessment = dict(valid_assessment)
    invalid_date_assessment["date"] = "2026-02-30"
    put(tmp, ".pipa.json", json.dumps({
        "subjectType": "non_user",
        "storageZone": "internal",
        "riskAssessment": invalid_date_assessment,
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target, content=passport,
    ))
    want(problems, "deny" in out, "존재하지 않는 평가 날짜가 보호를 껐다: %r" % out[:160])

    # 주민등록번호는 제2호 단서에서 명시적으로 제외되므로 평가 범위에 넣어도 차단한다.
    resident_assessment = dict(valid_assessment)
    resident_assessment["exemptItems"] = ["residentRegistrationNumber"]
    put(tmp, ".pipa.json", json.dumps({
        "subjectType": "non_user",
        "storageZone": "internal",
        "riskAssessment": resident_assessment,
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=os.path.join(tmp, "src", "EmployeeIdentity.java"),
        content=fixture("violation", VIOLATION_NON_USER_RESIDENT),
    ))
    want(problems, "deny" in out, "주민등록번호에 내부망 평가 예외가 적용됐다: %r" % out[:160])
    return problems


@case("제7조 제4항 HTTP 전송은 차단하고 목적지 미확인은 경고한다 (D-21)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []

    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", "IdentityPartnerClient.java"),
        content=fixture("violation", VIOLATION_PLAIN_HTTP),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "외부 평문 HTTP 전송을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-ENC-004" in reason, "제4항 전송 규칙 ID가 없다")
    want(problems, "정보통신망을 통하여 인터넷망 구간으로 송ㆍ수신" in reason,
         "제4항 차단 이유에 조항 원문이 없다")

    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", "SecureIdentityPartnerClient.java"),
        content=fixture("compliant", COMPLIANT_HTTPS),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "HTTPS 전송인데 출력했다: %r" % out[:160])

    # 스킴을 알 수 없는 전송은 PreToolUse에서 막지 않고 PostToolUse에서만 경고한다.
    unknown_path = put(
        tmp, "src/LicenseVerificationClient.java",
        fixture("violation", VIOLATION_UNKNOWN_TRANSPORT),
    )
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=unknown_path,
        content=fixture("violation", VIOLATION_UNKNOWN_TRANSPORT),
    ))
    want(problems, out == "", "목적지 미확인 전송을 PreToolUse가 차단했다: %r" % out[:160])

    code, out, err = engine([], event("PostToolUse", "Write", file_path=unknown_path))
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-ENC-004/unverified-network-transmission" in context,
         "목적지 미확인 전송 경고가 없다: %r" % out[:160])
    return problems


@case("요청 DTO 전파는 차단하고 TLS 검증 우회는 경고한다 (D-22)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []

    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", "IdentityPartnerClient.java"),
        content=fixture("violation", VIOLATION_PLAIN_HTTP_DTO),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "요청 DTO의 외부 평문 HTTP 전송을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-ENC-004/plaintext-http-transmission" in reason,
         "요청 DTO 차단 이유에 하위 검사 ID가 없다")

    # TLS 검증 우회는 같은 파일의 설정과 송신이 연결됐다는 보장이 약하므로 경고만 한다.
    tls_path = put(
        tmp, "src/InsecureIdentityPartnerClient.java",
        fixture("violation", VIOLATION_TLS_BYPASS),
    )
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=tls_path,
        content=fixture("violation", VIOLATION_TLS_BYPASS),
    ))
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "TLS 검증 우회 경고를 PreToolUse가 차단했다: %r" % out[:160])

    code, out, err = engine([], event("PostToolUse", "Write", file_path=tls_path))
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-ENC-004/tls-verification-disabled" in context,
         "TLS 검증 우회 경고가 없다: %r" % out[:160])

    for name in (COMPLIANT_HTTPS_DTO, COMPLIANT_ENCRYPTED_SETTER):
        code, out, err = engine([], event(
            "PreToolUse", "Write",
            file_path=os.path.join(tmp, "src", name),
            content=fixture("compliant", name),
        ))
        want(problems, code == 0, "%s 종료코드가 0이 아니다: %d" % (name, code))
        want(problems, out == "", "%s 적법 코드인데 출력했다: %r" % (name, out[:160]))
    return problems


@case("추가 HTTP 클라이언트는 차단하되 일반 execute는 제외한다 (D-23)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []

    for name in (
        VIOLATION_SPRING_REST_CLIENT,
        VIOLATION_OKHTTP,
        VIOLATION_APACHE_HTTP,
    ):
        code, out, err = engine([], event(
            "PreToolUse", "Write",
            file_path=os.path.join(tmp, "src", name),
            content=fixture("violation", name),
        ))
        want(problems, code == 0, "%s 종료코드가 0이 아니다: %d" % (name, code))
        hso = hook_specific(problems, out, "PreToolUse")
        reason = hso.get("permissionDecisionReason") or ""
        want(problems, hso.get("permissionDecision") == "deny",
             "%s 외부 평문 HTTP 전송을 차단하지 않았다: %r" % (name, out[:160]))
        want(problems, "K-ENC-004/plaintext-http-transmission" in reason,
             "%s 차단 이유에 하위 검사 ID가 없다" % name)

    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", COMPLIANT_GENERIC_EXECUTE),
        content=fixture("compliant", COMPLIANT_GENERIC_EXECUTE),
    ))
    want(problems, code == 0, "일반 execute 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "일반 execute를 HTTP 송신으로 오인했다: %r" % out[:160])
    return problems


@case("일반 개인정보는 사람 문맥만 차단하고 모호한 연락처는 경고한다 (D-24)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []

    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", VIOLATION_GENERAL_NAME),
        content=fixture("violation", VIOLATION_GENERAL_NAME),
    ))
    want(problems, code == 0, "성명 전송 종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "성명 외부 평문 HTTP 전송을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-ENC-004/plaintext-http-transmission" in reason,
         "성명 차단 이유에 하위 검사 ID가 없다")
    want(problems, "성명" in reason, "성명 차단 이유에 개인정보 항목명이 없다")

    ambiguous_path = put(
        tmp, "src/AmbiguousContact.java",
        fixture("violation", VIOLATION_AMBIGUOUS_CONTACT),
    )
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=ambiguous_path,
        content=fixture("violation", VIOLATION_AMBIGUOUS_CONTACT),
    ))
    want(problems, code == 0, "모호한 연락처 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "모호한 연락처를 PreToolUse가 차단했다: %r" % out[:160])

    code, out, err = engine([], event("PostToolUse", "Write", file_path=ambiguous_path))
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-ENC-004/plaintext-http-transmission" in context,
         "모호한 연락처 전송 경고가 없다: %r" % out[:160])

    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", COMPLIANT_ORGANIZATION_CONTACT),
        content=fixture("compliant", COMPLIANT_ORGANIZATION_CONTACT),
    ))
    want(problems, code == 0, "조직 연락처 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "조직 연락처를 개인정보로 오인했다: %r" % out[:160])
    return problems


@case("선언형 HTTP 클라이언트는 실제 프록시 호출만 판정한다 (D-25)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []

    for name in (
        VIOLATION_SPRING_HTTP_SERVICE,
        VIOLATION_RETROFIT,
        VIOLATION_FEIGN,
        VIOLATION_JDK_HTTP_CLIENT,
        VIOLATION_KOTLIN_RETROFIT,
        VIOLATION_SPRING_REACTIVE,
    ):
        code, out, err = engine([], event(
            "PreToolUse", "Write",
            file_path=os.path.join(tmp, "src", name),
            content=fixture("violation", name),
        ))
        want(problems, code == 0, "%s 종료코드가 0이 아니다: %d" % (name, code))
        hso = hook_specific(problems, out, "PreToolUse")
        reason = hso.get("permissionDecisionReason") or ""
        want(problems, hso.get("permissionDecision") == "deny",
             "%s 외부 평문 HTTP 전송을 차단하지 않았다: %r" % (name, out[:160]))
        want(problems, "K-ENC-004/plaintext-http-transmission" in reason,
             "%s 차단 이유에 하위 검사 ID가 없다" % name)

    unknown_path = put(
        tmp, "src/UnknownSpringHttpService.java",
        fixture("violation", VIOLATION_UNKNOWN_HTTP_SERVICE),
    )
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=unknown_path,
        content=fixture("violation", VIOLATION_UNKNOWN_HTTP_SERVICE),
    ))
    want(problems, code == 0, "목적지 미확인 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "목적지 미확인 선언형 호출을 차단했다: %r" % out[:160])

    code, out, err = engine([], event("PostToolUse", "Write", file_path=unknown_path))
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-ENC-004/unverified-network-transmission" in context,
         "목적지 미확인 선언형 호출 경고가 없다: %r" % out[:160])

    for name in (
        COMPLIANT_DECLARATIONS_ONLY,
        COMPLIANT_SAME_METHOD,
        COMPLIANT_HTTPS_SPRING_HTTP_SERVICE,
        COMPLIANT_HTTPS_RETROFIT,
        COMPLIANT_HTTPS_FEIGN,
        COMPLIANT_RETROFIT_NOT_EXECUTED,
        COMPLIANT_REACTIVE_NOT_SUBSCRIBED,
        COMPLIANT_ENCRYPTED_FEIGN,
        COMPLIANT_GENERIC_SEND,
        COMPLIANT_HTTPS_KOTLIN_RETROFIT,
        COMPLIANT_DECLARATIVE_SHADOWING,
    ):
        code, out, err = engine([], event(
            "PreToolUse", "Write",
            file_path=os.path.join(tmp, "src", name),
            content=fixture("compliant", name),
        ))
        want(problems, code == 0, "%s 종료코드가 0이 아니다: %d" % (name, code))
        want(problems, out == "", "%s 적법 코드인데 출력했다: %r" % (name, out[:160]))
    return problems


@case("서버 수신 TLS는 배포 경계 근거에 따라 차단·경고한다 (D-26)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    target = os.path.join(tmp, "src", "PublicMemberController.java")

    # 인터넷망에서 TLS가 없다고 완전하게 선언한 경우에만 high로 차단한다.
    put(tmp, ".pipa.json", json.dumps({
        "inboundTransport": {
            "exposure": "internet",
            "tlsTermination": "none",
            "httpsOnly": False,
            "evidence": "deploy/public-http.md",
        }
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target,
        content=fixture("violation", VIOLATION_PLAIN_SERVER_RECEIVE),
    ))
    want(problems, code == 0, "평문 수신 종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "외부 평문 서버 수신을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-ENC-004/plaintext-server-receive" in reason,
         "서버 수신 차단 이유에 하위 검사 ID가 없다")

    # 수신 경계 설정이 없으면 단정하지 않고 PostToolUse 경고로 보낸다.
    put(tmp, ".pipa.json", json.dumps({}))
    unknown_path = put(
        tmp, "src/MemberLookupController.java",
        fixture("violation", VIOLATION_UNVERIFIED_SERVER_RECEIVE),
    )
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=unknown_path,
        content=fixture("violation", VIOLATION_UNVERIFIED_SERVER_RECEIVE),
    ))
    want(problems, code == 0, "수신 경계 미확인 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "수신 경계 미확인을 차단했다: %r" % out[:160])

    code, out, err = engine([], event("PostToolUse", "Write", file_path=unknown_path))
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-ENC-004/unverified-server-receive-tls" in context,
         "수신 경계 미확인 경고가 없다: %r" % out[:160])

    # 외부 HTTPS 전용 신뢰 프록시 근거가 있으면 내부 HTTP connector가 있어도 통과한다.
    put(tmp, ".pipa.json", json.dumps({
        "inboundTransport": {
            "exposure": "internet",
            "tlsTermination": "trusted_proxy",
            "httpsOnly": True,
            "evidence": "deploy/k8s/member-ingress.yaml",
        }
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=target,
        content=fixture("compliant", COMPLIANT_PROXY_TLS_SERVER),
    ))
    want(problems, code == 0, "프록시 TLS 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "신뢰 프록시 TLS 수신을 오인했다: %r" % out[:160])
    return problems


@case("출력 정책 초과는 차단하고 정책 미확인은 경고한다 (D-28)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []

    # 완전한 API 출력 정책에서 허용하지 않은 여권번호 응답은 high다.
    api_path = os.path.join(tmp, "src", VIOLATION_EXCESSIVE_API_RESPONSE)
    put(tmp, ".pipa.json", json.dumps({
        "outputPolicies": [{
            "sink": "api",
            "source": "%s#profile" % VIOLATION_EXCESSIVE_API_RESPONSE,
            "purpose": "회원 이름 조회",
            "allowedItems": ["fullName"],
            "evidence": "docs/privacy/member-profile.md",
        }]
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=api_path,
        content=fixture("violation", VIOLATION_EXCESSIVE_API_RESPONSE),
    ))
    want(problems, code == 0, "과다 API 응답 종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "출력 정책을 넘은 API 응답을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-LEAK-002/excessive-api-response" in reason,
         "API 응답 차단 이유에 하위 검사 ID가 없다")

    # 로그 목적 정책이 없으면 위반으로 단정하지 않고 PostToolUse 경고만 한다.
    put(tmp, ".pipa.json", json.dumps({}))
    log_path = put(
        tmp, "src/%s" % VIOLATION_UNVERIFIED_LOG_OUTPUT,
        fixture("violation", VIOLATION_UNVERIFIED_LOG_OUTPUT),
    )
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=log_path,
        content=fixture("violation", VIOLATION_UNVERIFIED_LOG_OUTPUT),
    ))
    want(problems, code == 0, "로그 정책 미확인 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "로그 정책 미확인을 차단했다: %r" % out[:160])

    code, out, err = engine([], event("PostToolUse", "Write", file_path=log_path))
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-LEAK-001/unverified-log-output-purpose" in context,
         "로그 출력 목적 미확인 경고가 없다: %r" % out[:160])

    # 완전한 로그 정책의 허용 항목 안이면 출력하지 않는다.
    allowed_path = os.path.join(tmp, "src", COMPLIANT_ALLOWED_LOG_OUTPUT)
    put(tmp, ".pipa.json", json.dumps({
        "outputPolicies": [{
            "sink": "log",
            "source": "%s#recordFailure" % COMPLIANT_ALLOWED_LOG_OUTPUT,
            "purpose": "계정 탈취 조사용 로그인 실패 감사",
            "allowedItems": ["emailAddress"],
            "evidence": "docs/privacy/login-audit.md",
        }]
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=allowed_path,
        content=fixture("compliant", COMPLIANT_ALLOWED_LOG_OUTPUT),
    ))
    want(problems, code == 0, "허용 로그 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "허용된 로그 항목을 오인했다: %r" % out[:160])
    return problems


@case("접속기록 구성요소 누락은 차단하고 정책 불완전은 경고한다 (D-29)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []

    complete_components = {
        "actorId": {"argument": "operatorId"},
        "accessedAt": {"external": "logger_timestamp"},
        "sourceInfo": {"argument": "clientIp"},
        "dataSubjectInfo": {"argument": "memberId"},
        "action": {"argument": "action"},
    }

    # 완전한 정책이 직접 인자로 지정한 처리 정보주체가 실제 접속기록 호출에서 빠지면 high다.
    missing_path = os.path.join(tmp, "src", VIOLATION_MISSING_ACCESS_LOG_SUBJECT)
    put(tmp, ".pipa.json", json.dumps({
        "accessLogPolicies": [{
            "source": "%s#recordAccess" % VIOLATION_MISSING_ACCESS_LOG_SUBJECT,
            "components": complete_components,
            "evidence": "config/logback-access.xml",
        }]
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=missing_path,
        content=fixture("violation", VIOLATION_MISSING_ACCESS_LOG_SUBJECT),
    ))
    want(problems, code == 0, "접속기록 누락 종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "접속기록 구성요소 누락을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-LOG-001/missing-access-log-component" in reason,
         "접속기록 차단 이유에 하위 검사 ID가 없다")
    want(problems, "처리한 정보주체 정보" in reason,
         "접속기록 차단 이유에 누락한 법정 구성요소가 없다")

    # 접속일시 공급 방식이 빠진 정책은 위반으로 단정하지 않고 경고한다.
    incomplete_components = dict(complete_components)
    incomplete_components.pop("accessedAt")
    incomplete_path = put(
        tmp, "src/%s" % VIOLATION_INCOMPLETE_ACCESS_LOG_POLICY,
        fixture("violation", VIOLATION_INCOMPLETE_ACCESS_LOG_POLICY),
    )
    put(tmp, ".pipa.json", json.dumps({
        "accessLogPolicies": [{
            "source": "%s#recordAccess" % VIOLATION_INCOMPLETE_ACCESS_LOG_POLICY,
            "components": incomplete_components,
            "evidence": "docs/privacy/access-log.md",
        }]
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=incomplete_path,
        content=fixture("violation", VIOLATION_INCOMPLETE_ACCESS_LOG_POLICY),
    ))
    want(problems, code == 0, "접속기록 정책 미확인 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "불완전한 접속기록 정책을 차단했다: %r" % out[:160])
    code, out, err = engine([], event("PostToolUse", "Write", file_path=incomplete_path))
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-LOG-001/unverified-access-log-components" in context,
         "접속기록 정책 불완전 경고가 없다: %r" % out[:160])

    # 완전한 정책과 네 직접 인자, logger timestamp 근거가 모두 있으면 통과한다.
    clean_path = os.path.join(tmp, "src", COMPLIANT_COMPLETE_ACCESS_LOG)
    put(tmp, ".pipa.json", json.dumps({
        "accessLogPolicies": [{
            "source": "%s#recordAccess" % COMPLIANT_COMPLETE_ACCESS_LOG,
            "components": complete_components,
            "evidence": "config/logback-access.xml",
        }]
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=clean_path,
        content=fixture("compliant", COMPLIANT_COMPLETE_ACCESS_LOG),
    ))
    want(problems, code == 0, "완전한 접속기록 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "완전한 접속기록을 오인했다: %r" % out[:160])
    return problems


@case("단말 파일 평문 저장은 차단하고 위치 미확인은 경고한다 (D-30)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []

    # 개인정보취급자 컴퓨터라고 근거와 함께 선언한 메서드의 평문 파일 저장은 high다.
    workstation_path = os.path.join(tmp, "src", VIOLATION_WORKSTATION_FILE)
    put(tmp, ".pipa.json", json.dumps({
        "localStoragePolicies": [{
            "source": "%s#exportProfile" % VIOLATION_WORKSTATION_FILE,
            "target": "workstation",
            "evidence": "docs/privacy/operator-export.md",
        }]
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=workstation_path,
        content=fixture("violation", VIOLATION_WORKSTATION_FILE),
    ))
    want(problems, code == 0, "단말 파일 저장 종료코드가 0이 아니다: %d" % code)
    hso = hook_specific(problems, out, "PreToolUse")
    reason = hso.get("permissionDecisionReason") or ""
    want(problems, hso.get("permissionDecision") == "deny",
         "개인정보취급자 컴퓨터의 평문 파일 저장을 차단하지 않았다: %r" % out[:160])
    want(problems, "K-ENC-005/plaintext-device-storage" in reason,
         "단말 저장 차단 이유에 하위 검사 ID가 없다")
    want(problems, "개인정보취급자의 컴퓨터, 모바일 기기 및 보조저장매체" in reason,
         "단말 저장 차단 이유에 제7조 제5항 원문이 없다")

    # 파일 저장은 보이지만 위치 계약이 없으면 PreToolUse에서 막지 않고 PostToolUse로 경고한다.
    put(tmp, ".pipa.json", json.dumps({}))
    unverified_path = put(
        tmp, "src/%s" % VIOLATION_UNVERIFIED_LOCAL_STORAGE,
        fixture("violation", VIOLATION_UNVERIFIED_LOCAL_STORAGE),
    )
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=unverified_path,
        content=fixture("violation", VIOLATION_UNVERIFIED_LOCAL_STORAGE),
    ))
    want(problems, code == 0, "저장 위치 미확인 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "저장 위치 미확인을 차단했다: %r" % out[:160])
    code, out, err = engine([], event("PostToolUse", "Write", file_path=unverified_path))
    hso = hook_specific(problems, out, "PostToolUse")
    context = hso.get("additionalContext") or ""
    want(problems, "K-ENC-005/unverified-device-storage-target" in context,
         "저장 위치 미확인 경고가 없다: %r" % out[:160])

    # 근거 있는 서버 저장 선언은 제7조 제5항의 단말·보조저장매체 범위가 아니다.
    server_path = os.path.join(tmp, "src", COMPLIANT_SERVER_FILE_STORAGE)
    put(tmp, ".pipa.json", json.dumps({
        "localStoragePolicies": [{
            "source": "%s#writeReport" % COMPLIANT_SERVER_FILE_STORAGE,
            "target": "server",
            "evidence": "deploy/report-service.yaml",
        }]
    }))
    code, out, err = engine([], event(
        "PreToolUse", "Write", file_path=server_path,
        content=fixture("compliant", COMPLIANT_SERVER_FILE_STORAGE),
    ))
    want(problems, code == 0, "서버 파일 저장 종료코드가 0이 아니다: %d" % code)
    want(problems, out == "", "서버 파일 저장을 단말 저장으로 오인했다: %r" % out[:160])
    return problems


# --------------------------------------------------------------------------- #
# 훅 모드 — 실패 신호
# --------------------------------------------------------------------------- #

@case("사전을 읽을 수 없으면 systemMessage — 조용히 통과하지 않는다")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    exe = broken_engine(tmp, "invalid")
    code, out, err = engine([], event(
        "PreToolUse", "Write",
        file_path=os.path.join(tmp, "src", "Member.java"),
        content=fixture("violation", VIOLATION_HIGH),
    ), exe=exe)
    # 편집을 막지는 않는다. 판정하지 못한 것을 근거로 차단하면 조항 없는 차단이 된다.
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    want(problems, out != "", "판정 실패가 정상 통과와 구별되지 않는다 (출력 없음)")
    if out:
        data = parsed(problems, out)
        msg = data.get("systemMessage") or ""
        want(problems, bool(msg), "systemMessage 가 없다: %r" % out[:160])
        want(problems, "pipa-guard" in msg, "systemMessage 에 발신자가 없다: %r" % msg[:120])
        want(problems, "hookSpecificOutput" not in data,
             "판정하지 못했는데 판정 결과를 냈다: %r" % out[:160])
    want(problems, "Traceback" not in err, "traceback 이 노출됐다")
    return problems


@case("stdin 이 JSON 이 아니면 systemMessage")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    code, out, err = engine([], "이건 JSON이 아니다")
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    data = parsed(problems, out) if out else {}
    want(problems, bool(data.get("systemMessage")),
         "stdin 이 깨졌는데 신호가 없다: %r" % out[:160])
    return problems


# --------------------------------------------------------------------------- #
# CLI 모드
# --------------------------------------------------------------------------- #

@case("CLI + high → 종료코드 1")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    path = put(tmp, "src/Member.java", fixture("violation", VIOLATION_HIGH))
    code, out, err = engine([path])
    want(problems, code == 1, "종료코드가 1이 아니다: %d" % code)
    want(problems, "차단" in out, "요약 줄이 없다: %r" % out[-160:])
    return problems


@case("CLI + 적법 → 종료코드 0")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    path = put(tmp, "src/Member.java", fixture("compliant", COMPLIANT))
    code, out, err = engine([path])
    want(problems, code == 0, "종료코드가 0이 아니다: %d" % code)
    return problems


@case("CLI + --json → 파싱 가능한 JSON 배열")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    path = put(tmp, "src/Member.java", fixture("violation", VIOLATION_HIGH))
    code, out, err = engine([path, "--json"])
    want(problems, code == 1, "종료코드가 1이 아니다: %d" % code)
    try:
        data = json.loads(out)
    except ValueError:
        problems.append("--json 출력이 JSON 이 아니다: %r" % out[:160])
        return problems
    want(problems, isinstance(data, list) and bool(data), "--json 이 빈 배열이다")
    if isinstance(data, list) and data:
        keys = set(data[0])
        for required in ("rule", "check", "confidence", "line", "article", "quote"):
            want(problems, required in keys, "--json 항목에 %s 가 없다" % required)
    return problems


@case("CLI + 대상 없음 → 종료코드 2")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    code, out, err = engine([os.path.join(tmp, "empty")])
    want(problems, code == 2, "종료코드가 2가 아니다: %d" % code)
    want(problems, err.startswith("pipa-guard:"),
         "stderr 가 pipa-guard: 로 시작하지 않는다: %r" % err[:120])
    return problems


@case("CLI + 사전 없음 → 종료코드 3 (high 검출과 구별된다)")
def _(tmp: str) -> list[str]:
    problems: list[str] = []
    exe = broken_engine(tmp, "missing")
    path = put(tmp, "src/Member.java", fixture("violation", VIOLATION_HIGH))
    code, out, err = engine([path], exe=exe)
    # CI 가 "위반을 찾았다"(1)와 "엔진이 깨졌다"를 구별해야 한다. 같은 코드면 오진한다.
    want(problems, code == 3, "종료코드가 3이 아니다: %d" % code)
    want(problems, err.startswith("pipa-guard:"),
         "stderr 가 pipa-guard: 로 시작하지 않는다: %r" % err[:120])
    want(problems, "Traceback" not in err, "traceback 이 노출됐다")
    return problems


# --------------------------------------------------------------------------- #

def main() -> int:
    passed = 0
    failed: list[str] = []

    print("=== 훅·CLI 계약")
    for title, fn in CASES:
        with tempfile.TemporaryDirectory(prefix="pipa-hooks-") as tmp:
            problems = fn(tmp)
        if problems:
            detail = ", ".join(problems)
            failed.append("%s — %s" % (title, detail))
            print("  FAIL %-52s %s" % (title, detail))
        else:
            passed += 1
            print("  PASS %s" % title)

    print()
    print("합계 %d/%d 통과" % (passed, len(CASES)))
    if failed:
        print()
        print("실패 %d건:" % len(failed))
        for line in failed:
            print("  - %s" % line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
