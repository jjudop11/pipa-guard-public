#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipa-guard 훅 실행 시간 측정 도구.

이 파일은 합격/불합격을 판정하는 harness가 아니다. 실행 환경에 따라 달라지는 시간을 CI
임계값으로 고정하지 않고, 같은 입력과 방법으로 기준선을 다시 측정하기 위한 benchmark다.

두 계층을 나눠 잰다.

  1) 훅 전체: 매 표본마다 새 Python 하위 프로세스를 실행한다. 인터프리터 시작, 모듈 import,
     이벤트 JSON 처리, 설정·사전 로드, 판정과 출력 직렬화를 모두 포함한다.
  2) 엔진 내부: 모듈을 한 번 import한 뒤 설정 탐색, 사전 로드, analyze()를 각각 잰다.

기본 입력은 기존 적법·위반 fixture와 이 스크립트가 메모리에서 만드는 합성 대형 소스다.
실제 코드베이스 수치가 아니며 회사 코드나 실행 결과를 사용하지 않는다. (D-07, D-08)

  $ python3 tests/benchmark_hooks.py
  $ python3 tests/benchmark_hooks.py --samples 100 --large-lines 4000
  $ python3 tests/benchmark_hooks.py --json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from typing import Callable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "bin", "pipa_check.py")
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


@dataclass
class Result:
    name: str
    layer: str
    input_label: str
    median_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float


def fixture(kind: str, name: str) -> str:
    path = os.path.join(ROOT, "fixtures", kind, name)
    with open(path, "r", encoding="utf-8") as fp:
        return fp.read()


def event(name: str, tool: str, **tool_input) -> str:
    return json.dumps(
        {"hook_event_name": name, "tool_name": tool, "tool_input": tool_input},
        ensure_ascii=False,
    )


def large_java(line_target: int) -> str:
    lines = [
        "package benchmark;",
        "public class LargeProfileService {",
    ]
    for index in range(max(0, line_target - 3)):
        lines.append(
            "    public String normalize%04d(String value%04d) { return value%04d.trim(); }"
            % (index, index, index)
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def large_kotlin(line_target: int) -> str:
    lines = [
        "package benchmark",
        "class LargeProfileService {",
    ]
    for index in range(max(0, line_target - 3)):
        lines.append(
            "    fun normalize%04d(value%04d: String): String = value%04d.trim()"
            % (index, index, index)
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def percentile95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def measure(
    name: str,
    layer: str,
    input_label: str,
    fn: Callable[[], None],
    warmups: int,
    samples: int,
) -> Result:
    for _ in range(warmups):
        fn()

    elapsed_ms: list[float] = []
    for _ in range(samples):
        started = time.perf_counter_ns()
        fn()
        elapsed_ms.append((time.perf_counter_ns() - started) / 1_000_000)

    return Result(
        name=name,
        layer=layer,
        input_label=input_label,
        median_ms=statistics.median(elapsed_ms),
        p95_ms=percentile95(elapsed_ms),
        min_ms=min(elapsed_ms),
        max_ms=max(elapsed_ms),
    )


def run_hook(stdin_text: str, expected: str) -> None:
    proc = subprocess.run(
        [sys.executable, ENGINE],
        input=stdin_text,
        capture_output=True,
        text=True,
        env=ENV,
        cwd=ROOT,
    )
    if proc.returncode != 0 or proc.stderr:
        raise RuntimeError("훅 실행 계약이 깨져 있어 시간을 측정할 수 없습니다")
    if expected == "quiet" and proc.stdout:
        raise RuntimeError("조용히 통과해야 할 입력에서 훅 출력이 발생했습니다")
    if expected == "deny":
        try:
            data = json.loads(proc.stdout)
            decision = data["hookSpecificOutput"]["permissionDecision"]
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("차단 훅 출력이 계약과 다릅니다") from exc
        if decision != "deny":
            raise RuntimeError("위반 입력이 차단되지 않아 시간을 측정할 수 없습니다")


def load_engine():
    spec = importlib.util.spec_from_file_location("pipa_check_benchmark", ENGINE)
    if spec is None or spec.loader is None:
        raise RuntimeError("엔진 모듈을 불러올 수 없습니다")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def benchmark(args: argparse.Namespace) -> tuple[dict, list[Result]]:
    java_small_clean = fixture("compliant", "C001_BCrypt.java")
    java_small_deny = fixture("violation", "V001_PasswordAesEntity.java")
    java_plain_http = fixture("violation", "V025_PlainHttpResidentTransmission.java")
    java_plain_http_dto = fixture("violation", "V031_PlainHttpRequestDtoConstructor.java")
    java_spring_rest_client = fixture("violation", "V036_PlainHttpSpringRestClient.java")
    java_okhttp = fixture("violation", "V037_PlainHttpOkHttpRequest.java")
    java_apache_http = fixture("violation", "V038_PlainHttpApacheClient.java")
    java_general_pii = fixture("violation", "V039_PlainHttpFullName.java")
    java_spring_http_service = fixture(
        "violation", "V043_PlainHttpSpringHttpService.java"
    )
    java_retrofit = fixture("violation", "V044_PlainHttpRetrofitCall.java")
    java_feign = fixture("violation", "V045_PlainHttpFeignClient.java")
    java_plain_server_receive = fixture(
        "violation", "V051_PlainSpringServerPiiReceive.java"
    )
    java_excessive_api_response = fixture(
        "violation", "V055_ExcessiveSpringApiResponse.java"
    )
    java_missing_access_log_subject = fixture(
        "violation", "V063_MissingAccessLogSubject.java"
    )
    java_non_user_assessed = fixture(
        "compliant", "C026_NonUserInternalPassportAssessmentExemption.java"
    )
    kotlin_small_clean = fixture("compliant", "C007_BCryptKotlin.kt")
    java_large = large_java(args.large_lines)
    kotlin_large = large_kotlin(args.large_lines)

    results: list[Result] = []
    with tempfile.TemporaryDirectory(prefix="pipa-benchmark-") as tmp:
        project = os.path.join(tmp, "project")
        source_dir = os.path.join(project, "src", "main", "java", "benchmark")
        os.makedirs(source_dir)
        with open(os.path.join(project, ".pipa.json"), "w", encoding="utf-8") as fp:
            json.dump({"exclude": []}, fp)

        non_user_source_dir = os.path.join(project, "non-user", "src")
        os.makedirs(non_user_source_dir)
        non_user_config = {
            "exclude": [],
            "subjectType": "non_user",
            "storageZone": "internal",
            "riskAssessment": {
                "basis": "privacy_impact_assessment",
                "document": "docs/privacy/impact-assessment-2026.md",
                "date": "2026-08-31",
                "conclusion": "encryption_not_required",
                "exemptItems": ["passportNumber"],
            },
        }
        with open(os.path.join(project, "non-user", ".pipa.json"), "w", encoding="utf-8") as fp:
            json.dump(non_user_config, fp)

        server_source_dir = os.path.join(project, "public-server", "src")
        os.makedirs(server_source_dir)
        server_config = {
            "exclude": [],
            "inboundTransport": {
                "exposure": "internet",
                "tlsTermination": "none",
                "httpsOnly": False,
                "evidence": "deploy/public-http.md",
            },
        }
        with open(os.path.join(project, "public-server", ".pipa.json"), "w", encoding="utf-8") as fp:
            json.dump(server_config, fp)

        output_source_dir = os.path.join(project, "output-api", "src")
        os.makedirs(output_source_dir)
        output_config = {
            "exclude": [],
            "outputPolicies": [
                {
                    "sink": "api",
                    "source": "V055_ExcessiveSpringApiResponse.java#profile",
                    "purpose": "회원 이름 조회",
                    "allowedItems": ["fullName"],
                    "evidence": "docs/privacy/member-profile.md",
                }
            ],
        }
        with open(os.path.join(project, "output-api", ".pipa.json"), "w", encoding="utf-8") as fp:
            json.dump(output_config, fp)

        access_log_source_dir = os.path.join(project, "access-log", "src")
        os.makedirs(access_log_source_dir)
        access_log_config = {
            "exclude": [],
            "accessLogPolicies": [
                {
                    "source": "V063_MissingAccessLogSubject.java#recordAccess",
                    "components": {
                        "actorId": {"argument": "operatorId"},
                        "accessedAt": {"external": "logger_timestamp"},
                        "sourceInfo": {"argument": "clientIp"},
                        "dataSubjectInfo": {"argument": "memberId"},
                        "action": {"argument": "action"},
                    },
                    "evidence": "config/logback-access.xml",
                }
            ],
        }
        with open(os.path.join(project, "access-log", ".pipa.json"), "w", encoding="utf-8") as fp:
            json.dump(access_log_config, fp)

        small_java_path = os.path.join(source_dir, "MemberPasswordService.java")
        large_java_path = os.path.join(source_dir, "LargeProfileService.java")
        kotlin_path = os.path.join(source_dir, "LargeProfileService.kt")
        non_user_path = os.path.join(non_user_source_dir, "AssessedPassportRecord.java")
        server_path = os.path.join(server_source_dir, "PublicMemberController.java")
        output_path = os.path.join(
            output_source_dir, "V055_ExcessiveSpringApiResponse.java"
        )
        access_log_path = os.path.join(
            access_log_source_dir, "V063_MissingAccessLogSubject.java"
        )
        with open(small_java_path, "w", encoding="utf-8") as fp:
            fp.write(java_small_clean)
        with open(large_java_path, "w", encoding="utf-8") as fp:
            fp.write(java_large)
        with open(kotlin_path, "w", encoding="utf-8") as fp:
            fp.write(kotlin_large)
        with open(non_user_path, "w", encoding="utf-8") as fp:
            fp.write(java_non_user_assessed)
        with open(output_path, "w", encoding="utf-8") as fp:
            fp.write(java_excessive_api_response)
        with open(access_log_path, "w", encoding="utf-8") as fp:
            fp.write(java_missing_access_log_subject)

        scenarios = [
            (
                "PreToolUse Write 적법 Java",
                "기존 합성 fixture %d줄" % len(java_small_clean.splitlines()),
                event("PreToolUse", "Write", file_path=small_java_path, content=java_small_clean),
                "quiet",
            ),
            (
                "PostToolUse Write 적법 Java",
                "기존 합성 fixture %d줄" % len(java_small_clean.splitlines()),
                event("PostToolUse", "Write", file_path=small_java_path),
                "quiet",
            ),
            (
                "PreToolUse Write 차단 Java",
                "기존 합성 fixture %d줄" % len(java_small_deny.splitlines()),
                event("PreToolUse", "Write", file_path=small_java_path, content=java_small_deny),
                "deny",
            ),
            (
                "PreToolUse Write 평문 HTTP 전송 차단",
                "합성 fixture %d줄" % len(java_plain_http.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_plain_http,
                ),
                "deny",
            ),
            (
                "PreToolUse Write 요청 DTO 평문 HTTP 전송 차단",
                "합성 fixture %d줄" % len(java_plain_http_dto.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_plain_http_dto,
                ),
                "deny",
            ),
            (
                "PreToolUse Write Spring RestClient 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_spring_rest_client.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_spring_rest_client,
                ),
                "deny",
            ),
            (
                "PreToolUse Write OkHttp 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_okhttp.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_okhttp,
                ),
                "deny",
            ),
            (
                "PreToolUse Write Apache HttpClient 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_apache_http.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_apache_http,
                ),
                "deny",
            ),
            (
                "PreToolUse Write 일반 개인정보 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_general_pii.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_general_pii,
                ),
                "deny",
            ),
            (
                "PreToolUse Write Spring HTTP Service 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_spring_http_service.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_spring_http_service,
                ),
                "deny",
            ),
            (
                "PreToolUse Write Retrofit 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_retrofit.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_retrofit,
                ),
                "deny",
            ),
            (
                "PreToolUse Write Feign 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_feign.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=small_java_path,
                    content=java_feign,
                ),
                "deny",
            ),
            (
                "PreToolUse Write 서버 평문 HTTP 수신 차단",
                "합성 fixture %d줄" % len(java_plain_server_receive.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=server_path,
                    content=java_plain_server_receive,
                ),
                "deny",
            ),
            (
                "PreToolUse Write API 출력 정책 초과 차단",
                "합성 fixture %d줄" % len(java_excessive_api_response.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=output_path,
                    content=java_excessive_api_response,
                ),
                "deny",
            ),
            (
                "PreToolUse Write 접속기록 구성요소 누락 차단",
                "합성 fixture %d줄" % len(java_missing_access_log_subject.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=access_log_path,
                    content=java_missing_access_log_subject,
                ),
                "deny",
            ),
            (
                "PreToolUse Write 적법 Kotlin",
                "기존 합성 fixture %d줄" % len(kotlin_small_clean.splitlines()),
                event("PreToolUse", "Write", file_path=kotlin_path, content=kotlin_small_clean),
                "quiet",
            ),
            (
                "PreToolUse Write 비이용자 내부망 평가 예외",
                "합성 fixture %d줄" % len(java_non_user_assessed.splitlines()),
                event(
                    "PreToolUse", "Write", file_path=non_user_path,
                    content=java_non_user_assessed,
                ),
                "quiet",
            ),
            (
                "PreToolUse Edit 대형 Java",
                "메모리 생성 합성 소스 %d줄" % len(java_large.splitlines()),
                event(
                    "PreToolUse", "Edit", file_path=large_java_path,
                    old_string="return value0000.trim();",
                    new_string="return value0000.strip();",
                ),
                "quiet",
            ),
            (
                "PostToolUse Edit 대형 Java",
                "메모리 생성 합성 소스 %d줄" % len(java_large.splitlines()),
                event("PostToolUse", "Edit", file_path=large_java_path),
                "quiet",
            ),
            (
                "PreToolUse Write 대형 Kotlin",
                "메모리 생성 합성 소스 %d줄" % len(kotlin_large.splitlines()),
                event("PreToolUse", "Write", file_path=kotlin_path, content=kotlin_large),
                "quiet",
            ),
        ]

        for name, label, stdin_text, expected in scenarios:
            results.append(measure(
                name, "새 프로세스 훅 전체", label,
                lambda data=stdin_text, want=expected: run_hook(data, want),
                args.warmups, args.samples,
            ))

        engine = load_engine()
        dictionary = engine.load_dictionary()
        internal = [
            (
                "설정 탐색",
                "프로젝트 루트에서 4단계 아래",
                lambda: engine.find_config(source_dir),
            ),
            (
                "항목 사전 로드",
                "항목 %d개 사전" % len(dictionary.raw.get("items", [])),
                engine.load_dictionary,
            ),
            (
                "analyze 적법 Java",
                "기존 합성 fixture %d줄" % len(java_small_clean.splitlines()),
                lambda: engine.analyze(small_java_path, java_small_clean, dictionary),
            ),
            (
                "analyze 차단 Java",
                "기존 합성 fixture %d줄" % len(java_small_deny.splitlines()),
                lambda: engine.analyze(small_java_path, java_small_deny, dictionary),
            ),
            (
                "analyze 평문 HTTP 전송 차단",
                "합성 fixture %d줄" % len(java_plain_http.splitlines()),
                lambda: engine.analyze(small_java_path, java_plain_http, dictionary),
            ),
            (
                "analyze 요청 DTO 평문 HTTP 전송 차단",
                "합성 fixture %d줄" % len(java_plain_http_dto.splitlines()),
                lambda: engine.analyze(
                    small_java_path, java_plain_http_dto, dictionary
                ),
            ),
            (
                "analyze Spring RestClient 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_spring_rest_client.splitlines()),
                lambda: engine.analyze(
                    small_java_path, java_spring_rest_client, dictionary
                ),
            ),
            (
                "analyze OkHttp 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_okhttp.splitlines()),
                lambda: engine.analyze(small_java_path, java_okhttp, dictionary),
            ),
            (
                "analyze Apache HttpClient 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_apache_http.splitlines()),
                lambda: engine.analyze(small_java_path, java_apache_http, dictionary),
            ),
            (
                "analyze 일반 개인정보 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_general_pii.splitlines()),
                lambda: engine.analyze(small_java_path, java_general_pii, dictionary),
            ),
            (
                "analyze Spring HTTP Service 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_spring_http_service.splitlines()),
                lambda: engine.analyze(
                    small_java_path, java_spring_http_service, dictionary
                ),
            ),
            (
                "analyze Retrofit 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_retrofit.splitlines()),
                lambda: engine.analyze(small_java_path, java_retrofit, dictionary),
            ),
            (
                "analyze Feign 평문 HTTP 차단",
                "합성 fixture %d줄" % len(java_feign.splitlines()),
                lambda: engine.analyze(small_java_path, java_feign, dictionary),
            ),
            (
                "analyze 서버 평문 HTTP 수신 차단",
                "합성 fixture %d줄" % len(java_plain_server_receive.splitlines()),
                lambda: engine.analyze(
                    server_path, java_plain_server_receive, dictionary, server_config
                ),
            ),
            (
                "analyze API 출력 정책 초과 차단",
                "합성 fixture %d줄" % len(java_excessive_api_response.splitlines()),
                lambda: engine.analyze(
                    output_path,
                    java_excessive_api_response,
                    dictionary,
                    output_config,
                ),
            ),
            (
                "analyze 접속기록 구성요소 누락 차단",
                "합성 fixture %d줄" % len(java_missing_access_log_subject.splitlines()),
                lambda: engine.analyze(
                    access_log_path,
                    java_missing_access_log_subject,
                    dictionary,
                    access_log_config,
                ),
            ),
            (
                "analyze 비이용자 내부망 평가 예외",
                "합성 fixture %d줄" % len(java_non_user_assessed.splitlines()),
                lambda: engine.analyze(
                    non_user_path, java_non_user_assessed, dictionary, non_user_config
                ),
            ),
            (
                "analyze 대형 Java",
                "메모리 생성 합성 소스 %d줄" % len(java_large.splitlines()),
                lambda: engine.analyze(large_java_path, java_large, dictionary),
            ),
            (
                "analyze 대형 Kotlin",
                "메모리 생성 합성 소스 %d줄" % len(kotlin_large.splitlines()),
                lambda: engine.analyze(kotlin_path, kotlin_large, dictionary),
            ),
        ]
        for name, label, fn in internal:
            results.append(measure(
                name, "동일 프로세스 엔진 내부", label, fn, args.warmups, args.samples,
            ))

    metadata = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "samples": args.samples,
        "warmups": args.warmups,
        "large_lines": args.large_lines,
        "note": "모두 합성 fixture 또는 메모리 생성 합성 소스 기준",
    }
    return metadata, results


def print_text(metadata: dict, results: list[Result]) -> None:
    print("=== pipa-guard 훅 성능 기준선")
    print("측정: %(measured_at)s / %(platform)s / Python %(python)s" % metadata)
    print("표본: 준비 실행 %(warmups)d회 + 측정 %(samples)d회 / 대형 입력 %(large_lines)d줄" % metadata)
    print("주의: %s" % metadata["note"])
    print()

    current_layer = None
    for result in results:
        if result.layer != current_layer:
            current_layer = result.layer
            print("--- %s" % current_layer)
            print("%-34s %10s %10s %10s %10s" % ("시나리오", "중앙값", "p95", "최소", "최대"))
        print("%-34s %9.3fms %9.3fms %9.3fms %9.3fms" % (
            result.name,
            result.median_ms,
            result.p95_ms,
            result.min_ms,
            result.max_ms,
        ))
        print("  입력: %s" % result.input_label)


def main() -> int:
    parser = argparse.ArgumentParser(description="pipa-guard 훅 실행 시간 기준선 측정")
    parser.add_argument("--samples", type=int, default=50, help="시나리오별 측정 횟수 (기본 50)")
    parser.add_argument("--warmups", type=int, default=5, help="시나리오별 준비 실행 횟수 (기본 5)")
    parser.add_argument("--large-lines", type=int, default=2000, help="합성 대형 소스 줄 수 (기본 2000)")
    parser.add_argument("--json", action="store_true", help="기계 판독용 JSON 출력")
    args = parser.parse_args()
    if args.samples <= 0 or args.warmups < 0 or args.large_lines < 3:
        parser.error("samples > 0, warmups >= 0, large-lines >= 3 이어야 합니다")

    metadata, results = benchmark(args)
    if args.json:
        print(json.dumps({
            "metadata": metadata,
            "results": [asdict(result) for result in results],
        }, ensure_ascii=False, indent=2))
    else:
        print_text(metadata, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
