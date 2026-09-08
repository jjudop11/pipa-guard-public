#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""README와 배포 설명의 검증 가능한 주장을 실행 계약으로 고정한다.

판정 정확도는 run_fixtures.py, 훅 입출력은 run_hooks.py가 담당한다. 이 harness는 그 결과를
README의 수치·예제·지원 범위와 연결하고, 설정·비식별화·결정성·무의존성처럼 문서에만 남기
쉬운 약속을 별도로 확인한다. 네트워크나 LLM을 호출하지 않으며 합성 데이터만 사용한다.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "bin", "pipa_check.py")
README = os.path.join(ROOT, "README.md")
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(ROOT, "bin"))

import pipa_check  # noqa: E402


CASES: list[tuple[str, object]] = []


def case(title: str):
    def deco(fn):
        CASES.append((title, fn))
        return fn
    return deco


def load(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fp:
        return fp.read()


def load_json(path: str):
    return json.loads(load(path))


def fixture(kind: str, name: str) -> tuple[str, str]:
    path = os.path.join(ROOT, "fixtures", kind, name)
    return path, load(path)


def merged_config(**updates) -> dict:
    config = dict(pipa_check.DEFAULT_CONFIG)
    config.update(updates)
    return config


def finding_confidences(path: str, text: str, config: dict) -> dict[str, str]:
    dic = pipa_check.load_dictionary()
    return {finding.rule_id: finding.confidence
            for finding in pipa_check.analyze(path, text, dic, config)}


def want(problems: list[str], condition: bool, message: str) -> None:
    if not condition:
        problems.append(message)


@case("README 정량 정보 → 규칙·fixture·사전·계약의 실제 개수")
def _() -> list[str]:
    problems: list[str] = []
    readme = load(README)
    rules = load_json(os.path.join(ROOT, "rules", "rules.json"))["rules"]
    active = [rule for rule in rules if rule.get("status") == "active"]
    checks = [check for rule in active for check in rule.get("checks", [])]
    violation_count = len([
        name for name in os.listdir(os.path.join(ROOT, "fixtures", "violation"))
        if name.endswith(pipa_check.SUPPORTED_EXT)
    ])
    compliant_paths = [
        os.path.join(ROOT, "fixtures", "compliant", name)
        for name in os.listdir(os.path.join(ROOT, "fixtures", "compliant"))
        if name.endswith(pipa_check.SUPPORTED_EXT)
    ]
    clean_count = sum("pipa-fixture-expect-clean" in load(path)
                      for path in compliant_paths)
    fixture_count = violation_count + len(compliant_paths)
    hook_count = len(re.findall(
        r'^@case\(', load(os.path.join(ROOT, "tests", "run_hooks.py")), re.MULTILINE,
    ))
    items = load_json(os.path.join(ROOT, "rules", "pii_items.json"))["items"]
    alias_count = sum(len(item.get("aliases_strong", [])) +
                      len(item.get("aliases_weak", [])) for item in items)

    want(problems, re.search(
        r"활성 규칙은\s*%d개 중\s*\*\*%d개\*\*" % (len(rules), len(active)), readme,
    ) is not None, "README의 활성 규칙 수가 rules.json과 다르다")
    want(problems, "합계 %d/%d 통과" % (fixture_count, fixture_count) in readme,
         "README의 fixture 합계가 실제 파일 수와 다르다")
    want(problems, "합계 %d/%d 통과" % (hook_count, hook_count) in readme,
         "README의 훅 계약 수가 run_hooks.py와 다르다")
    want(problems, "위반 fixture %d건" % violation_count in readme,
         "README의 위반 fixture 수가 실제 파일 수와 다르다")
    want(problems, "적법 fixture %d건" % len(compliant_paths) in readme,
         "README의 적법 fixture 수가 실제 파일 수와 다르다")
    want(problems, "그중 %d건" % clean_count in readme,
         "README의 clean fixture 수가 실제 선언 수와 다르다")
    want(problems, "별칭 %d개" % alias_count in readme,
         "README의 사전 별칭 수가 실제 개수와 다르다")
    want(problems, len(checks) == 25,
         "활성 하위 검사 수가 문서 기준 25개와 다르다: %d" % len(checks))
    return problems


@case("README 첫 설명 → 실제 훅 범위와 모델 재작성 비보장 명시")
def _() -> list[str]:
    problems: list[str] = []
    readme = load(README)
    for marker in (
        "Claude Code의 `Write`·`Edit`",
        "Codex의 `apply_patch`",
        "Bash 등 다른 파일 쓰기 경로는 사전 차단 범위 밖",
        "항상 같은 재작성을 보장하지 않는다",
    ):
        want(problems, marker in readme, "README에 지원 경계 문구가 없다: %s" % marker)
    for overclaim in (
        "위반 코드는 디스크에 닿기 전에 차단되고",
        "에이전트가 스스로 적법한 코드로 다시 쓰게 만든다",
    ):
        want(problems, overclaim not in readme, "README에 무조건적 표현이 남아 있다: %s" % overclaim)
    return problems


@case("README 코드·설정 예제 → 엔진 판정과 JSON 템플릿")
def _() -> list[str]:
    problems: list[str] = []
    readme = load(README)
    java_blocks = re.findall(r"```java\n(.*?)```", readme, re.DOTALL)
    weak_hash_blocks = [block for block in java_blocks if "MessageDigest" in block]
    want(problems, len(weak_hash_blocks) == 2,
         "README의 SHA-1 Java 예제 두 개를 찾을 수 없다")
    for index, block in enumerate(weak_hash_blocks, start=1):
        findings = finding_confidences(
            os.path.join(ROOT, "README_WeakHash%d.java" % index),
            block,
            merged_config(),
        )
        want(problems, findings.get("K-ENC-002/weak-hash") == "high",
             "README SHA-1 예제 %d가 high로 검출되지 않는다" % index)

    ignored = [block for block in java_blocks if "pipa-guard:ignore" in block]
    want(problems, len(ignored) == 1, "README의 억제 Java 예제를 하나로 식별할 수 없다")
    if len(ignored) == 1:
        findings = finding_confidences(
            os.path.join(ROOT, "README_Ignored.java"), ignored[0], merged_config(),
        )
        want(problems, not findings, "README의 이유 있는 억제 예제가 실제로 억제되지 않는다")

    json_blocks = re.findall(r"```json\n(.*?)```", readme, re.DOTALL)
    want(problems, len(json_blocks) == 1, "README의 .pipa.json 예제를 하나로 식별할 수 없다")
    if len(json_blocks) == 1:
        try:
            readme_config = json.loads(json_blocks[0])
        except ValueError:
            problems.append("README의 .pipa.json 예제가 올바른 JSON이 아니다")
        else:
            example = load_json(os.path.join(ROOT, ".pipa.json.example"))
            expected = {key for key in example if not key.startswith("//")}
            want(problems, set(readme_config) == expected,
                 "README 설정 키가 .pipa.json.example과 다르다")
    return problems


@case(".pipa.json 여덟 키 → 각각 실제 판정 입력으로 사용")
def _() -> list[str]:
    problems: list[str] = []
    example = load_json(os.path.join(ROOT, ".pipa.json.example"))
    keys = {key for key in example if not key.startswith("//")}
    expected_keys = {
        "exclude", "subjectType", "storageZone", "riskAssessment",
        "inboundTransport", "outputPolicies", "accessLogPolicies",
        "localStoragePolicies",
    }
    want(problems, keys == expected_keys,
         ".pipa.json.example의 실제 설정 키가 여덟 키 계약과 다르다")

    project_root = os.path.join(ROOT, "claim-project")
    want(problems, pipa_check.is_excluded(
        os.path.join(project_root, "build", "Generated.java"), project_root,
        {"exclude": ["build/"]},
    ), "exclude가 대상 경로를 제외하지 않는다")
    want(problems, not pipa_check.is_excluded(
        os.path.join(project_root, "src", "Member.java"), project_root,
        {"exclude": ["build/"]},
    ), "exclude가 범위 밖 경로까지 제외한다")

    path, text = fixture("violation", "V012_ResidentNumberPlainColumn.java")
    user = finding_confidences(path, text, merged_config(subjectType="user"))
    non_user = finding_confidences(
        path, text, merged_config(subjectType="non_user", storageZone="internet"),
    )
    want(problems, "K-ENC-001/plaintext-sized-column" in user and
         "K-ENC-003/plaintext-sized-column" not in user,
         "subjectType=user가 이용자 저장 규칙을 선택하지 않는다")
    want(problems, "K-ENC-003/plaintext-sized-column" in non_user and
         "K-ENC-001/plaintext-sized-column" not in non_user,
         "subjectType=non_user가 비이용자 저장 규칙을 선택하지 않는다")

    path, text = fixture("compliant", "C026_NonUserInternalPassportAssessmentExemption.java")
    assessment = {
        "basis": "privacy_impact_assessment",
        "document": "docs/privacy/impact-assessment-2026.md",
        "date": "2026-08-31",
        "conclusion": "encryption_not_required",
        "exemptItems": ["passportNumber"],
    }
    internal = finding_confidences(path, text, merged_config(
        subjectType="non_user", storageZone="internal", riskAssessment=assessment,
    ))
    internet = finding_confidences(path, text, merged_config(
        subjectType="non_user", storageZone="internet", riskAssessment=assessment,
    ))
    no_assessment = finding_confidences(path, text, merged_config(
        subjectType="non_user", storageZone="internal", riskAssessment=None,
    ))
    want(problems, "K-ENC-003/plaintext-sized-column" not in internal,
         "유효한 내부망 평가 예외가 적용되지 않는다")
    want(problems, "K-ENC-003/plaintext-sized-column" in internet,
         "storageZone=internet에서도 내부망 평가 예외가 적용된다")
    want(problems, "K-ENC-003/plaintext-sized-column" in no_assessment,
         "riskAssessment가 없어도 내부망 평가 예외가 적용된다")

    path, text = fixture("violation", "V051_PlainSpringServerPiiReceive.java")
    insecure = finding_confidences(path, text, merged_config(inboundTransport={
        "exposure": "internet", "tlsTermination": "none", "httpsOnly": False,
        "evidence": "deploy/public-http.md",
    }))
    secure = finding_confidences(path, text, merged_config(inboundTransport={
        "exposure": "internet", "tlsTermination": "trusted_proxy", "httpsOnly": True,
        "evidence": "deploy/ingress.yaml",
    }))
    want(problems, "K-ENC-004/plaintext-server-receive" in insecure,
         "외부 평문 inboundTransport가 차단되지 않는다")
    want(problems, not any(key.startswith("K-ENC-004/") for key in secure),
         "신뢰 프록시 TLS inboundTransport가 통과하지 않는다")

    path, text = fixture("violation", "V055_ExcessiveSpringApiResponse.java")
    excessive = finding_confidences(path, text, merged_config(outputPolicies=[{
        "sink": "api", "source": os.path.basename(path) + "#profile",
        "purpose": "회원 이름 조회", "allowedItems": ["fullName"],
        "evidence": "docs/privacy/member-profile.md",
    }]))
    allowed = finding_confidences(path, text, merged_config(outputPolicies=[{
        "sink": "api", "source": os.path.basename(path) + "#profile",
        "purpose": "회원 신원 조회", "allowedItems": ["fullName", "passportNumber"],
        "evidence": "docs/privacy/member-profile.md",
    }]))
    want(problems, "K-LEAK-002/excessive-api-response" in excessive,
         "outputPolicies 초과 항목이 차단되지 않는다")
    want(problems, "K-LEAK-002/excessive-api-response" not in allowed,
         "outputPolicies 허용 항목까지 차단한다")

    path, text = fixture("violation", "V063_MissingAccessLogSubject.java")
    components = {
        "actorId": {"argument": "operatorId"},
        "accessedAt": {"external": "logger_timestamp"},
        "sourceInfo": {"argument": "clientIp"},
        "dataSubjectInfo": {"argument": "memberId"},
        "action": {"argument": "action"},
    }
    missing = finding_confidences(path, text, merged_config(accessLogPolicies=[{
        "source": os.path.basename(path) + "#recordAccess",
        "components": components, "evidence": "config/logback-access.xml",
    }]))
    external_components = dict(components)
    external_components["dataSubjectInfo"] = {"external": "request_mdc"}
    supplied = finding_confidences(path, text, merged_config(accessLogPolicies=[{
        "source": os.path.basename(path) + "#recordAccess",
        "components": external_components, "evidence": "config/logback-access.xml",
    }]))
    want(problems, "K-LOG-001/missing-access-log-component" in missing,
         "accessLogPolicies의 직접 인자 누락이 차단되지 않는다")
    want(problems, "K-LOG-001/missing-access-log-component" not in supplied,
         "accessLogPolicies의 허용된 외부 공급 근거가 적용되지 않는다")

    path, text = fixture("violation", "V065_WorkstationPlaintextFile.java")
    workstation = finding_confidences(path, text, merged_config(localStoragePolicies=[{
        "source": os.path.basename(path) + "#exportProfile", "target": "workstation",
        "evidence": "docs/privacy/operator-export.md",
    }]))
    server = finding_confidences(path, text, merged_config(localStoragePolicies=[{
        "source": os.path.basename(path) + "#exportProfile", "target": "server",
        "evidence": "deploy/export-service.yaml",
    }]))
    want(problems, "K-ENC-005/plaintext-device-storage" in workstation,
         "localStoragePolicies의 취급자 단말 저장이 차단되지 않는다")
    want(problems, "K-ENC-005/plaintext-device-storage" not in server,
         "localStoragePolicies의 서버 저장까지 제7조 제5항으로 차단한다")
    return problems


@case("필드명 단독 → 사전 별칭 전부 차단·경고 없음")
def _() -> list[str]:
    problems: list[str] = []
    items = load_json(os.path.join(ROOT, "rules", "pii_items.json"))["items"]
    aliases = sorted({alias for item in items
                      for field in ("aliases_strong", "aliases_weak")
                      for alias in item.get(field, [])})
    dic = pipa_check.load_dictionary()
    leaked = []
    for alias in aliases:
        text = "public class Candidate { private String %s; }\n" % alias
        findings = pipa_check.analyze("Candidate.java", text, dic, merged_config())
        if findings:
            leaked.append(alias)
    want(problems, len(aliases) == 114,
         "검사한 사전 별칭 수가 기대값 114개와 다르다: %d" % len(aliases))
    want(problems, not leaked,
         "sink 없는 필드명만으로 Finding이 생긴다: %s" % ", ".join(leaked[:5]))
    return problems


@case("근거 비식별화 → 합성 주민번호·카드번호·긴 숫자열·긴 문자열 마스킹")
def _() -> list[str]:
    problems: list[str] = []
    resident = "900101" + "-" + "1234567"
    card = "1234" + "-" + "5678" + "-" + "9012" + "-" + "3456"
    long_number = "12" + "34567890"
    long_literal = "x" * 50
    evidence = 'resident=%s card=%s seq=%s value="%s"' % (
        resident, card, long_number, long_literal,
    )
    redacted = pipa_check.redact(evidence)
    want(problems, resident not in redacted, "주민등록번호 전체 값이 근거에 남는다")
    want(problems, card not in redacted, "카드번호 전체 값이 근거에 남는다")
    want(problems, long_number not in redacted, "8자리 이상 숫자열 전체 값이 근거에 남는다")
    want(problems, long_literal not in redacted, "긴 문자열 리터럴 전체 값이 근거에 남는다")
    want(problems, "900101-*******" in redacted, "주민등록번호 마스킹 형식이 계약과 다르다")
    want(problems, "****-****-****-****" in redacted, "카드번호 마스킹 형식이 계약과 다르다")
    want(problems, len(redacted) <= pipa_check.MAX_EVIDENCE,
         "근거가 MAX_EVIDENCE를 초과한다")
    return problems


@case("결정적 판정 → 반복·해시 시드 변경에도 byte-identical JSON")
def _() -> list[str]:
    problems: list[str] = []
    _fixture_path, text = fixture("violation", "V001_PasswordAesEntity.java")
    with tempfile.TemporaryDirectory(prefix="pipa-claims-") as tmp:
        path = os.path.join(tmp, "Member.java")
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)
        outputs = []
        for seed in ("0", "1", "42", "random"):
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED=seed)
            proc = subprocess.run(
                [sys.executable, ENGINE, path, "--json"],
                capture_output=True, text=True, cwd=ROOT, env=env,
            )
            want(problems, proc.returncode == pipa_check.EXIT_HIGH,
                 "해시 시드 %s에서 high CLI 종료코드가 아니다" % seed)
            want(problems, not proc.stderr,
                 "해시 시드 %s에서 예상하지 않은 stderr가 생겼다" % seed)
            try:
                json.loads(proc.stdout)
            except ValueError:
                problems.append("해시 시드 %s의 stdout이 JSON이 아니다" % seed)
            outputs.append(proc.stdout)
        want(problems, len(set(outputs)) == 1,
             "PYTHONHASHSEED에 따라 JSON 출력이 달라진다")
    return problems


@case("엔진 실행 경계 → Python 표준 라이브러리만 사용하고 네트워크·LLM import 없음")
def _() -> list[str]:
    problems: list[str] = []
    tree = ast.parse(load(ENGINE), filename=ENGINE)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    imports.discard("__future__")
    stdlib = getattr(sys, "stdlib_module_names", {
        "dataclasses", "datetime", "fnmatch", "json", "os", "re", "sys",
    })
    external = sorted(imports - set(stdlib))
    forbidden = sorted(imports & {
        "anthropic", "http", "openai", "requests", "socket", "subprocess", "urllib",
    })
    want(problems, not external,
         "엔진에 외부 패키지 import가 있다: %s" % ", ".join(external))
    want(problems, not forbidden,
         "엔진에 네트워크·LLM 실행 가능 import가 있다: %s" % ", ".join(forbidden))
    return problems


@case("설치 설명 → 매니페스트·마켓플레이스 이름·버전·저장소와 일치")
def _() -> list[str]:
    problems: list[str] = []
    readme = load(README)
    claude_manifest = load_json(os.path.join(ROOT, ".claude-plugin", "plugin.json"))
    codex_manifest = load_json(os.path.join(ROOT, ".codex-plugin", "plugin.json"))
    marketplace = load_json(os.path.join(ROOT, ".agents", "plugins", "marketplace.json"))
    entries = marketplace.get("plugins", [])
    want(problems, claude_manifest.get("name") == codex_manifest.get("name"),
         "Claude·Codex 플러그인 이름이 다르다")
    want(problems, claude_manifest.get("version") == codex_manifest.get("version"),
         "Claude·Codex 플러그인 버전이 다르다")
    want(problems, "hooks" not in claude_manifest,
         "Claude가 자동 발견하는 hooks/hooks.json을 매니페스트가 중복 등록한다")
    want(problems, "hooks" not in codex_manifest,
         "Codex 매니페스트에 지원하지 않는 hooks 필드가 있다")
    want(problems, isinstance(entries, list) and len(entries) == 1,
         "Codex 마켓플레이스 항목이 정확히 하나가 아니다")
    if isinstance(entries, list) and len(entries) == 1:
        entry = entries[0]
        source = entry.get("source", {})
        match = re.fullmatch(
            r"https://github\.com/([^/]+/[^/]+)\.git", str(source.get("url", "")),
        )
        want(problems, entry.get("name") == codex_manifest.get("name"),
             "Codex 마켓플레이스와 매니페스트 이름이 다르다")
        want(problems, source.get("source") == "url" and match is not None,
             "Codex 마켓플레이스 source가 GitHub HTTPS URL이 아니다")
        if match is not None:
            slug = match.group(1)
            want(problems, "codex plugin marketplace add %s" % slug in readme,
                 "README의 Codex 마켓플레이스 등록 명령이 source와 다르다")
        want(problems, "codex plugin add %s@%s" % (
            entry.get("name"), marketplace.get("name"),
        ) in readme, "README의 Codex 플러그인 설치 명령이 마켓플레이스와 다르다")
        ref = source.get("ref")
        version = codex_manifest.get("version")
        if isinstance(ref, str) and ref.startswith("v"):
            want(problems, ref == "v" + str(version),
                 "Codex source 태그와 플러그인 버전이 다르다")

    claude_marketplace_path = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
    if os.path.isfile(claude_marketplace_path):
        claude_marketplace = load_json(claude_marketplace_path)
        claude_entries = claude_marketplace.get("plugins", [])
        want(problems, isinstance(claude_entries, list) and len(claude_entries) == 1,
             "Claude 마켓플레이스 항목이 정확히 하나가 아니다")
        if isinstance(claude_entries, list) and len(claude_entries) == 1:
            entry = claude_entries[0]
            want(problems, entry.get("version") == claude_manifest.get("version"),
                 "Claude 마켓플레이스와 매니페스트 버전이 다르다")
            want(problems, "claude plugin install %s@%s" % (
                entry.get("name"), claude_marketplace.get("name"),
            ) in readme, "README의 Claude 설치 명령이 마켓플레이스와 다르다")
    return problems


@case("README 플러그인 구성 → 스킬·에이전트·훅 파일이 실제로 존재")
def _() -> list[str]:
    problems: list[str] = []
    readme = load(README)
    paths = {
        "pipa-review": os.path.join(ROOT, "skills", "pipa-review", "SKILL.md"),
        "pipa-flow-map": os.path.join(ROOT, "skills", "pipa-flow-map", "SKILL.md"),
        "pipa-auditor": os.path.join(ROOT, "agents", "pipa-auditor.md"),
    }
    for name, path in paths.items():
        want(problems, os.path.isfile(path), "README가 설명하는 구성 파일이 없다: %s" % name)
        want(problems, name in readme, "README가 플러그인 구성을 설명하지 않는다: %s" % name)
    for rel in ("hooks/hooks.json", ".codex/hooks.json"):
        path = os.path.join(ROOT, rel)
        want(problems, os.path.isfile(path), "훅 설정 파일이 없다: %s" % rel)
        if os.path.isfile(path):
            try:
                hooks = load_json(path).get("hooks", {})
            except ValueError:
                problems.append("훅 설정이 올바른 JSON이 아니다: %s" % rel)
            else:
                want(problems, "PreToolUse" in hooks and "PostToolUse" in hooks,
                     "훅 설정에 PreToolUse·PostToolUse가 모두 없다: %s" % rel)
    return problems


def main() -> int:
    failed: list[str] = []
    print("=== README·배포 주장 계약")
    for title, fn in CASES:
        try:
            problems = fn()
        except Exception as exc:  # 예외 원문에는 경로·입력이 섞일 수 있어 종류만 출력한다.
            problems = ["검사 중 예외: %s" % type(exc).__name__]
        if problems:
            print("  FAIL %s" % title)
            for problem in problems:
                print("       %s" % problem)
            failed.extend("%s — %s" % (title, problem) for problem in problems)
        else:
            print("  PASS %s" % title)
    print()
    print("합계 %d/%d 통과" % (len(CASES) - len({line.split(" — ", 1)[0]
                                               for line in failed}), len(CASES)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
