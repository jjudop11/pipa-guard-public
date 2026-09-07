#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fixture harness.

  fixtures/violation/  — 파일마다 `// pipa-fixture-expect: <rule>/<check>` 로 선언한
                         검사가 high 신뢰도로 검출되어야 한다. (재현율)
                         `// pipa-fixture-expect-warn: <rule>/<check>` 는 medium/low로
                         검출되어야 한다. high로 올라가면 실패다. 차단 여부가 곧 동작
                         계약이므로 신뢰도까지 고정한다. (D-03)
  fixtures/compliant/  — high 신뢰도 검출이 하나도 없어야 한다. (오탐율 0)
                         `// pipa-fixture-expect-clean` 을 선언하면 경고도 하나도 없어야
                         한다. medium 검사의 오탐 방어선을 고정할 때 쓴다.
  rules/rules.json     — 규칙 ID 레지스트리가 엔진·조항 문서와 어긋나지 않아야 한다.
  rules/pii_items.json — 항목 사전의 별칭 형식·필수 필드·매칭 기대값. 기대값은
                         tests/dictionary_cases.json, 공개 근거 전수 연결은
                         rules/alias_sources.json 에 있다. (D-15, D-19)

harness-first 원칙을 따른다. 실패를 숨기기 위해 목표를 낮추지 않는다.

  $ python3 tests/run_fixtures.py
  종료코드 0 = 전체 통과
"""

from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 엔진을 고치면서 harness를 반복 실행하게 되므로 .pyc 를 남기지 않는다. 남은 바이트코드가
# 오래된 엔진으로 판정해 실패를 만든 적이 있다.
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(ROOT, "bin"))

import pipa_check  # noqa: E402

EXPECT_RE = re.compile(r"pipa-fixture-expect:\s*(\S+)")
EXPECT_WARN_RE = re.compile(r"pipa-fixture-expect-warn:\s*(\S+)")
EXPECT_CLEAN_RE = re.compile(r"pipa-fixture-expect-clean\b")
FIXTURE_CONFIG_RE = re.compile(r"pipa-fixture-config:\s*(\{[^\r\n]*\})")

# 엔진 소스에서 Finding(rule=..., check=...) 쌍을 뽑는다. 실행 경로를 타지 않는 검사도
# 레지스트리에 등재되어야 하므로 정적으로 읽는다.
ENGINE_PAIR_RE = re.compile(r'rule="([^"]+)",\s*check="([^"]+)"')
RULE_ID_RE = re.compile(r"\bK-[A-Z]+-\d{3}\b")


def load(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fp:
        return fp.read()


def files(kind: str) -> list[str]:
    base = os.path.join(ROOT, "fixtures", kind)
    if not os.path.isdir(base):
        return []
    return [os.path.join(base, n) for n in sorted(os.listdir(base))
            if n.endswith(pipa_check.SUPPORTED_EXT)]


def fixture_config(text: str) -> tuple[dict | None, str | None]:
    """fixture 헤더의 한 줄 JSON 설정을 읽는다.

    같은 코드도 정보주체·저장 구간·위험도 분석 결과에 따라 판정이 달라지므로(D-02),
    파일명이나 harness 내부 예외 목록이 아니라 fixture 자체가 맥락을 선언하게 한다.
    """
    matches = FIXTURE_CONFIG_RE.findall(text)
    if not matches:
        return None, None
    if len(matches) != 1:
        return None, "pipa-fixture-config 선언이 하나가 아니다"
    try:
        config = json.loads(matches[0])
    except ValueError:
        return None, "pipa-fixture-config가 올바른 한 줄 JSON이 아니다"
    if not isinstance(config, dict):
        return None, "pipa-fixture-config가 JSON 객체가 아니다"
    return config, None


def check_registry() -> list[str]:
    """rules/rules.json 이 엔진과 조항 문서의 규칙 ID 단일 출처인지 확인한다.

    문서 세 곳에 규칙 ID를 손으로 적어 두면 반드시 어긋난다. 실제로 어긋났었다.
    (articles.md는 제7조 제2항/제3항을 K-ENC-001/K-ENC-003으로 나눴는데 상태 문서와
    README.md는 K-ENC-001 하나로 합쳐 썼고, K-LOG-001은 articles.md에만 있었다.)
    """
    problems: list[str] = []

    registry = json.loads(load(os.path.join(ROOT, "rules", "rules.json")))
    rules = registry["rules"]

    ids = [r["id"] for r in rules]
    for rid in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append("rules.json — 규칙 ID 중복: %s" % rid)

    # (1) active 규칙의 checks == 엔진이 실제로 생성하는 (rule, check) 집합
    declared = {
        "%s/%s" % (r["id"], c["check"])
        for r in rules if r.get("status") == "active"
        for c in r.get("checks", [])
    }
    engine_src = load(os.path.join(ROOT, "bin", "pipa_check.py"))
    actual = {"%s/%s" % (m[0], m[1]) for m in ENGINE_PAIR_RE.findall(engine_src)}

    for rid in sorted(declared - actual):
        problems.append("rules.json — active로 선언했으나 엔진에 없는 검사: %s" % rid)
    for rid in sorted(actual - declared):
        problems.append("엔진이 생성하지만 rules.json에 없는 검사: %s" % rid)

    # active가 아닌 규칙이 엔진에서 도는 것도 어긋남이다.
    engine_rule_ids = {rid.split("/", 1)[0] for rid in actual}
    for r in rules:
        if r.get("status") != "active" and r["id"] in engine_rule_ids:
            problems.append("rules.json — status=%s 인데 엔진이 Finding을 만든다: %s"
                            % (r.get("status"), r["id"]))

    # (2) articles.md 에 등장하는 규칙 ID는 모두 레지스트리에 있어야 한다 (고아 방지)
    articles = load(os.path.join(ROOT, "rules", "articles.md"))
    known = set(ids)
    for rid in sorted(set(RULE_ID_RE.findall(articles)) - known):
        problems.append("articles.md — rules.json에 없는 규칙 ID: %s" % rid)

    # (3) 근거 조항이 확정된 규칙은 articles.md 에 조항과 함께 있어야 한다
    for r in rules:
        if r.get("article") and r["id"] not in articles:
            problems.append("rules.json — article=%s 인데 articles.md에 없는 규칙: %s"
                            % (r["article"], r["id"]))

    return problems


ALIAS_FORM_RE = re.compile(r"^[a-z0-9]+$")
ITEM_REQUIRED = ("key", "label", "category", "article", "article_quote",
                 "definition", "encryption", "source")
ENCRYPTION_KINDS = ("one_way_only", "two_way_allowed", "transmission_only")


def check_dictionary(dic) -> list[str]:
    """항목 사전을 계약으로 고정한다.

    활성 규칙의 코드 fixture는 사전 별칭 전체를 실행하지 않는다. 사용되지 않은 별칭의
    오타·중복·과잉 매칭과 공개 근거 누락은 규칙 fixture만으로 드러나지 않으므로 사전 자체를
    검사한다. (D-15, D-19)
    """
    problems: list[str] = []

    data = json.loads(load(os.path.join(ROOT, "rules", "pii_items.json")))
    items = data["items"]

    owner: dict[str, str] = {}
    for item in items:
        key = item.get("key", "(key 없음)")

        for field in ITEM_REQUIRED:
            if not item.get(field):
                problems.append("pii_items.json — %s 에 %s 가 비어 있다" % (key, field))
        # 규약 4·5(D-07): 출처 없는 별칭은 등재하지 않는다. 기계로 강제한다.
        if item.get("encryption") not in ENCRYPTION_KINDS:
            problems.append("pii_items.json — %s 의 encryption 값이 정의되지 않았다: %r"
                            % (key, item.get("encryption")))
        if not item.get("aliases_strong"):
            problems.append("pii_items.json — %s 에 aliases_strong 이 없다" % key)

        for strength in ("aliases_strong", "aliases_weak"):
            for alias in item.get(strength, []):
                # 별칭은 정규화된 형태로만 적는다. 대문자·밑줄·비ASCII 오타를 잡는다.
                if not ALIAS_FORM_RE.match(alias):
                    problems.append("pii_items.json — %s 의 별칭이 정규화 형태가 아니다: %r"
                                    % (key, alias))
                    continue
                if alias in owner and owner[alias] != key:
                    problems.append("pii_items.json — 별칭 %s 가 %s 와 %s 에 중복 등재됐다"
                                    % (alias, owner[alias], key))
                owner[alias] = key

    cases = json.loads(load(os.path.join(ROOT, "tests", "dictionary_cases.json")))

    covered = set()
    for case in cases["match"]:
        ident, key, strength = case["ident"], case["key"], case["strength"]
        item, got = dic.match(ident)
        got_key = item.get("key") if item else None
        if got_key != key or got != strength:
            problems.append("사전 매칭 — %s 는 (%s, %s) 여야 하는데 (%s, %s) 다"
                            % (ident, key, strength, got_key, got))
        covered.add(key)

    for ident in cases["no_match"]:
        item, got = dic.match(ident)
        if item is not None:
            problems.append("사전 매칭 — %s 는 매칭되면 안 되는데 (%s, %s) 로 걸렸다"
                            % (ident, item.get("key"), got))

    for item in items:
        if item.get("key") not in covered:
            problems.append("dictionary_cases.json — %s 에 대한 match 케이스가 없다"
                            % item.get("key"))

    evidence = json.loads(load(os.path.join(ROOT, "rules", "alias_sources.json")))
    sources = evidence.get("sources", {})
    for source_id, source in sources.items():
        if not str(source.get("url", "")).startswith("https://"):
            problems.append("alias_sources.json — %s 의 공개 https URL이 없다" % source_id)
        if not source.get("publisher") or not source.get("evidence"):
            problems.append("alias_sources.json — %s 의 발행자 또는 근거 설명이 비어 있다"
                            % source_id)

    evidence_items = {item.get("key"): item for item in evidence.get("items", [])}
    item_keys = {item.get("key") for item in items}
    if set(evidence_items) != item_keys:
        problems.append("alias_sources.json — 항목 집합이 pii_items.json과 다르다: %s"
                        % sorted(set(evidence_items) ^ item_keys))

    for item in items:
        key = item.get("key")
        expected = set(item.get("aliases_strong", []) + item.get("aliases_weak", []))
        listed: list[str] = []
        audit = evidence_items.get(key, {})
        for group in audit.get("groups", []):
            source_id = group.get("source")
            if source_id not in sources:
                problems.append("alias_sources.json — %s 가 없는 출처 %r 을 참조한다"
                                % (key, source_id))
            if not group.get("method"):
                problems.append("alias_sources.json — %s 의 근거 방식이 비어 있다" % key)
            listed.extend(group.get("aliases", []))

        for source_field in ("boundary_sources", "additional_sources"):
            for source_id in audit.get(source_field, []):
                if source_id not in sources:
                    problems.append("alias_sources.json — %s 가 없는 보조 출처 %r 을 참조한다"
                                    % (key, source_id))

        duplicates = sorted(alias for alias in set(listed) if listed.count(alias) > 1)
        if duplicates:
            problems.append("alias_sources.json — %s 의 별칭 근거가 중복됐다: %s"
                            % (key, duplicates))
        if set(listed) != expected:
            problems.append("alias_sources.json — %s 의 별칭 근거 범위가 다르다: 누락=%s 초과=%s"
                            % (key, sorted(expected - set(listed)),
                               sorted(set(listed) - expected)))

    return problems


def main() -> int:
    dic = pipa_check.load_dictionary()
    passed = 0
    failed: list[str] = []

    print("=== fixtures/violation — 검출되어야 한다")
    for path in files("violation"):
        name = os.path.basename(path)
        text = load(path)
        expected = EXPECT_RE.findall(text)
        expected_warn = EXPECT_WARN_RE.findall(text)
        # expect-warn 선언은 expect 정규식에도 걸리므로 뺀다.
        expected = [e for e in expected if e not in expected_warn]
        config, config_problem = fixture_config(text)
        findings = pipa_check.analyze(path, text, dic, config)
        high = [f for f in findings if f.confidence == "high"]
        warn = [f for f in findings if f.confidence != "high"]
        got = {f.rule_id for f in high}
        got_warn = {f.rule_id for f in warn}

        problems = []
        if config_problem:
            problems.append(config_problem)
        if not expected and not expected_warn:
            problems.append("expect 선언 없음")
        for e in expected:
            if e not in got:
                problems.append("high 미검출 %s" % e)
        for e in expected_warn:
            if e in got:
                # 경고로 선언한 것이 차단으로 올라가면 동작 계약이 바뀐다.
                problems.append("%s 가 경고가 아니라 high로 검출됨" % e)
            elif e not in got_warn:
                problems.append("경고 미검출 %s" % e)

        if problems:
            detail = ", ".join(problems)
            failed.append("%s — %s (high: %s / 경고: %s)"
                          % (name, detail, sorted(got) or "없음", sorted(got_warn) or "없음"))
            print("  FAIL %-38s %s" % (name, detail))
        else:
            passed += 1
            shown = sorted(got) + ["%s(경고)" % r for r in sorted(got_warn)]
            extra = sorted((got - set(expected)) | (got_warn - set(expected_warn)))
            note = "  (추가 검출: %s)" % extra if extra else ""
            print("  PASS %-38s %s%s" % (name, shown, note))

    print()
    print("=== fixtures/compliant — 검출되면 안 된다")
    for path in files("compliant"):
        name = os.path.basename(path)
        text = load(path)
        config, config_problem = fixture_config(text)
        findings = pipa_check.analyze(path, text, dic, config)
        high = [f for f in findings if f.confidence == "high"]
        warn = [f for f in findings if f.confidence != "high"]
        wants_clean = bool(EXPECT_CLEAN_RE.search(text))

        if config_problem:
            failed.append("%s — %s" % (name, config_problem))
            print("  FAIL %-38s %s" % (name, config_problem))
        elif high:
            detail = ", ".join("%s:%d %s" % (name, f.line, f.rule_id) for f in high)
            failed.append("%s — 오탐 %d건 (%s)" % (name, len(high), detail))
            print("  FAIL %-38s 오탐 %d건 — %s" % (name, len(high), detail))
        elif wants_clean and warn:
            detail = ", ".join("%s:%d %s" % (name, f.line, f.rule_id) for f in warn)
            failed.append("%s — expect-clean 인데 경고 %d건 (%s)" % (name, len(warn), detail))
            print("  FAIL %-38s expect-clean 인데 경고 %d건 — %s" % (name, len(warn), detail))
        else:
            passed += 1
            if warn:
                note = "  (경고 %d건: %s)" % (len(warn), sorted({f.rule_id for f in warn}))
            else:
                note = "  (clean 확인)" if wants_clean else ""
            print("  PASS %-38s%s" % (name, note))

    print()
    print("=== rules/pii_items.json — 항목 사전")
    dic_problems = check_dictionary(dic)
    if dic_problems:
        for line in dic_problems:
            print("  FAIL %s" % line)
        failed.extend(dic_problems)
    else:
        items = json.loads(load(os.path.join(ROOT, "rules", "pii_items.json")))["items"]
        cases = json.loads(load(os.path.join(ROOT, "tests", "dictionary_cases.json")))
        print("  PASS 항목 %d개 / 매칭 기대값 %d건 / 비매칭 방어선 %d건"
              % (len(items), len(cases["match"]), len(cases["no_match"])))

    print()
    print("=== rules/rules.json — 규칙 ID 레지스트리 정합")
    registry_problems = check_registry()
    if registry_problems:
        for line in registry_problems:
            print("  FAIL %s" % line)
        failed.extend(registry_problems)
    else:
        print("  PASS 엔진·articles.md와 규칙 ID가 일치한다")

    total = len(files("violation")) + len(files("compliant"))
    print()
    print("합계 %d/%d 통과" % (passed, total))
    if failed:
        print()
        print("실패 %d건:" % len(failed))
        for line in failed:
            print("  - %s" % line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
