#!/usr/bin/env python3
"""기존 39개 시나리오와 암호 관련 대형 합성 입력을 함께 비교한다. 시간 합격선은 두지 않는다."""

import argparse
import importlib.util
import json
import os
import sys
import tempfile
from dataclasses import asdict

sys.dont_write_bytecode = True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--samples", type=int, default=50)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--large-lines", type=int, default=2000)
    args = parser.parse_args()
    if args.samples <= 0 or args.warmups < 0 or args.large_lines < 100:
        parser.error("samples > 0, warmups >= 0, large-lines >= 100 이어야 한다")
    spec = importlib.util.spec_from_file_location(
        "release_benchmark", os.path.join(args.root, "tests", "benchmark_hooks.py"),
    )
    bench = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bench
    spec.loader.exec_module(bench)
    metadata, results = bench.benchmark(args)
    engine = bench.load_engine()
    dic = engine.load_dictionary()
    plain = bench.large_java(args.large_lines - 1).replace(
        "public class LargeProfileService {", "public class LargeProfileService {\n    private String password;",
    )
    helper = bench.fixture("violation", "V071_PasswordAesHelperReturn.java")
    padding = args.large_lines - len(helper.splitlines())
    methods = bench.large_java(padding + 3).splitlines()[2:-1]
    mixed = helper.rsplit("}", 1)[0] + "\n".join(methods) + "\n}\n"
    with tempfile.TemporaryDirectory(prefix="pipa-release-benchmark-") as tmp:
        for label, source, expected in (
            ("비밀번호 필드 대형 Java", plain, "quiet"),
            ("암호 보조 메서드 대형 Java", mixed, "deny"),
        ):
            assert len(source.splitlines()) == args.large_lines
            path = os.path.join(tmp, "Synthetic.java")
            payload = bench.event("PreToolUse", "Write", file_path=path, content=source)
            input_label = "메모리 생성 합성 소스 %d줄" % args.large_lines
            results.append(bench.measure(
                "PreToolUse Write " + label, "새 프로세스 훅 전체", input_label,
                lambda data=payload, want=expected: bench.run_hook(data, want), args.warmups, args.samples,
            ))
            results.append(bench.measure(
                "analyze " + label, "동일 프로세스 엔진 내부", input_label,
                lambda text=source: engine.analyze(path, text, dic), args.warmups, args.samples,
            ))
    print(json.dumps({"metadata": metadata, "results": [asdict(r) for r in results]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
