#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipa-guard 검출 엔진 (Phase 4)

「개인정보의 안전성 확보조치 기준」(개인정보보호위원회 고시 제2026-9호, 시행 2026-07-01)을
근거로 Java·Kotlin 소스의 개인정보 보호조치 위반을 검출한다.
조항 원문은 rules/articles.md, 항목 사전은 rules/pii_items.json에 있다.

실행 방식
  1) hook — stdin으로 Claude Code / Codex 훅 이벤트 JSON을 받는다.
       PreToolUse   high 신뢰도 위반을 permissionDecision=deny 로 차단한다.
       PostToolUse  medium/low 신뢰도 위반을 additionalContext 로 통보한다.
     **종료코드는 언제나 0이다.** 훅이 편집 흐름 자체를 깨뜨리지 않는다. 차단은 stdout
     JSON으로만 표현한다. 판정하지 못했을 때는 systemMessage 로 알린다 — 조용히 통과하면
     보호가 사라진 것을 아무도 모른다.
  2) CLI — 파일이나 디렉터리를 인자로 받아 사람이 읽는 형식으로 출력한다.
       $ python3 bin/pipa_check.py src/main/java
       0 위반 없음 / 1 high 위반 존재 / 2 검사할 파일 없음 / 3 엔진 오류
     3을 1과 나눈 이유는 CI가 "위반을 찾았다"와 "엔진이 깨졌다"를 구별해야 하기 때문이다.
     오류 메시지는 stderr에 `pipa-guard: ` 로 시작한다.

  이 계약은 `tests/run_hooks.py`가 고정한다. 판정은 `tests/run_fixtures.py`가 고정한다.

설계 원칙
  - 표준 라이브러리만 쓴다. 훅은 매 편집마다 실행되므로 외부 패키지·네트워크·LLM을
    호출하지 않는다.
  - 필드명 단독으로는 절대 차단하지 않는다. 차단은 (개인정보 후보) AND (보호 대상
    sink 도달) AND (보호 장치 부재) 세 조건이 모두 성립할 때만 한다.
  - 결정적이다. 같은 입력에 같은 결과를 낸다.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from dataclasses import dataclass, field as dc_field
from datetime import date as calendar_date

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_DIR = os.path.join(PLUGIN_ROOT, "rules")

SUPPORTED_EXT = (".java", ".kt", ".kts")
CONFIG_NAME = ".pipa.json"
MAX_EVIDENCE = 160

CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}

# CLI 종료코드. 훅 모드는 언제나 0이다.
EXIT_CLEAN = 0
EXIT_HIGH = 1       # high 위반 존재
EXIT_USAGE = 2      # 검사할 파일이 없다
EXIT_ENGINE = 3     # 판정하지 못했다. EXIT_HIGH 와 섞이면 CI가 오진한다.

DEFAULT_CONFIG = {
    "exclude": [],
    # 제7조 제2항/제3항 판정 분기의 입력이다. 파일이 없으면 더 보수적인 이용자로 본다.
    "subjectType": "user",
    "storageZone": "internet",
    "riskAssessment": None,
    # 서버 수신의 인터넷망 노출과 TLS 종단은 소스만으로 알 수 없어 명시적 근거 계약을 받는다.
    "inboundTransport": None,
    # 로그·API 응답은 출력 용도에 따라 필요한 항목이 달라져 소스만으로 최소성을 단정하지 않는다.
    "outputPolicies": [],
    # 접속기록 구성요소는 전용 logger 호출과 코드 밖 공급 근거를 파일#메서드별로 선언한다.
    "accessLogPolicies": [],
    # 파일 저장 코드의 실제 실행·저장 위치를 파일#메서드별 근거와 함께 선언한다.
    "localStoragePolicies": [],
}

QUOTE_7_3 = (
    "개인정보처리자는 이용자가 아닌 정보주체의 개인정보를 다음 각 호와 같이 저장하는 "
    "경우에는 암호화하여야 한다. "
    "1. 인터넷망 구간 및 인터넷망 구간과 내부망의 중간 지점(DMZ : Demilitarized Zone)에 "
    "고유식별정보를 저장하는 경우 "
    "2. 내부망에 고유식별정보를 저장하는 경우(다만, 주민등록번호 외의 고유식별정보를 "
    "저장하는 경우에는 다음 각 목의 기준에 따라 암호화의 적용여부 및 적용범위를 정하여 "
    "시행할 수 있다) "
    "가. 법 제33조에 따른 개인정보 영향평가의 대상이 되는 공공기관의 경우에는 해당 "
    "개인정보 영향평가의 결과 "
    "나. 암호화 미적용시 위험도 분석에 따른 결과"
)

QUOTE_7_4 = (
    "개인정보처리자는 개인정보를 정보통신망을 통하여 인터넷망 구간으로 송ㆍ수신하는 경우에는 "
    "이를 안전한 암호 알고리즘으로 암호화하여야 한다."
)

QUOTE_7_5 = (
    "개인정보처리자는 이용자의 개인정보 또는 이용자가 아닌 정보주체의 고유식별정보, "
    "생체인식정보를 개인정보취급자의 컴퓨터, 모바일 기기 및 보조저장매체 등에 저장할 때에는 "
    "안전한 암호 알고리즘을 사용하여 암호화한 후 저장하여야 한다."
)

QUOTE_12_1 = (
    "개인정보처리자는 개인정보처리시스템에서 개인정보의 출력시(인쇄, 화면표시, 파일생성 등) "
    "용도를 특정하여야 하며, 용도에 따라 출력 항목을 최소화하여야 한다."
)

QUOTE_2_3 = (
    '"접속기록"이란 개인정보처리시스템에 접속하는 자가 개인정보처리시스템에 접속하여 수행한 '
    "업무내역에 대하여 식별자, 접속일시, 접속지 정보, 처리한 정보주체 정보, 수행업무 등을 "
    '전자적으로 기록한 것을 말한다. 이 경우 "접속"이란 개인정보처리시스템과 연결되어 데이터 '
    "송신 또는 수신이 가능한 상태를 말한다."
)

QUOTE_8_1 = (
    "개인정보처리자는 개인정보처리시스템에 접속한 자(다만, 정보주체는 제외한다)의 접속기록을 "
    "1년 이상 보관ㆍ관리하여야 한다. 다만, 다음 각 호의 어느 하나에 해당하는 경우에는 2년 이상 "
    "보관ㆍ관리하여야 한다.\n"
    "1. 5만명 이상의 정보주체에 관한 개인정보를 처리하는 개인정보처리시스템에 해당하는 경우\n"
    "2. 고유식별정보 또는 민감정보를 처리하는 개인정보처리시스템에 해당하는 경우\n"
    "3. 개인정보처리자로서 「전기통신사업법」제6조제1항에 따라 등록을 하거나 같은 항 단서에 따라 "
    "신고한 기간통신사업자에 해당하는 경우"
)


# --------------------------------------------------------------------------- #
# 결과 모델
# --------------------------------------------------------------------------- #

@dataclass
class Finding:
    rule: str            # 규칙 ID (예: K-ENC-002)
    check: str           # 세부 검사 (예: two-way)
    confidence: str      # high | medium | low
    path: str
    line: int
    message: str         # 무엇이 문제인가
    article: str         # 근거 조항 번호
    quote: str           # 근거 조항 원문
    fix: str             # 어떻게 고치는가
    evidence: str        # 해당 코드

    @property
    def rule_id(self) -> str:
        return "%s/%s" % (self.rule, self.check)


# --------------------------------------------------------------------------- #
# 항목 사전
# --------------------------------------------------------------------------- #

def normalize_ident(ident: str) -> str:
    """식별자를 사전 키로 정규화한다. camelCase와 snake_case를 같은 키로 모은다."""
    return ident.replace("_", "").replace("$", "").lower()


class Dictionary:
    """개인정보 항목 사전.

    정규화 완전일치만 인정한다. 부분 문자열 매칭을 하지 않기 때문에 orderNo,
    merchantNo, productNo 같은 식별자는 매칭되지 않는다. 접두사(get/set/member/new
    등)는 최대 3회까지 제거하며 재시도한다.
    """

    MAX_PREFIX_STRIPS = 3

    def __init__(self, data: dict):
        self.raw = data
        self.prefixes = sorted(
            {normalize_ident(p) for p in data.get("name_prefixes", []) if p},
            key=len,
            reverse=True,
        )
        self.strong: dict[str, dict] = {}
        self.weak: dict[str, dict] = {}
        for item in data.get("items", []):
            for alias in item.get("aliases_strong", []):
                self.strong[normalize_ident(alias)] = item
            for alias in item.get("aliases_weak", []):
                self.weak[normalize_ident(alias)] = item

    def match(self, ident: str):
        """식별자 -> (항목, 'strong'|'weak') 또는 (None, None)."""
        return self._match(normalize_ident(ident), self.MAX_PREFIX_STRIPS)

    def _match(self, norm: str, depth: int):
        if norm in self.strong:
            return self.strong[norm], "strong"
        if norm in self.weak:
            return self.weak[norm], "weak"
        if depth <= 0:
            return None, None
        for prefix in self.prefixes:
            if norm.startswith(prefix) and len(norm) > len(prefix):
                item, strength = self._match(norm[len(prefix):], depth - 1)
                if item is not None:
                    return item, strength
        return None, None


def load_dictionary() -> Dictionary:
    path = os.path.join(RULES_DIR, "pii_items.json")
    with open(path, "r", encoding="utf-8") as fp:
        return Dictionary(json.load(fp))


# --------------------------------------------------------------------------- #
# 소스 전처리
# --------------------------------------------------------------------------- #

IGNORE_RE = re.compile(r"pipa-guard:ignore\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*(?:/[a-z0-9-]+)?)\s+(\S.*?)\s*$")
IDENT_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
ANNOTATION_RE = re.compile(
    r"@(?:(?:field|get|set|property|param|receiver):)?[A-Za-z_][\w.]*"
    r"\s*(?:\((?:[^()]|\([^()]*\))*\))?"
)


def strip_comments(text: str) -> str:
    """주석을 공백으로 치환한다. 오프셋과 줄 번호를 보존하므로 위치 계산이 어긋나지 않는다.

    문자열 리터럴 내부는 보존한다. 알고리즘 이름이 리터럴로 등장하기 때문이다
    (예: MessageDigest.getInstance("MD5")).
    """
    out = list(text)
    i, n = 0, len(text)
    state = None  # None | line | block | dquote | squote
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if state is None:
            if ch == "/" and nxt == "/":
                out[i] = out[i + 1] = " "
                state = "line"
                i += 2
                continue
            if ch == "/" and nxt == "*":
                out[i] = out[i + 1] = " "
                state = "block"
                i += 2
                continue
            if ch == '"':
                state = "dquote"
            elif ch == "'":
                state = "squote"
            i += 1
            continue
        if state == "line":
            if ch == "\n":
                state = None
            else:
                out[i] = " "
            i += 1
            continue
        if state == "block":
            if ch == "*" and nxt == "/":
                out[i] = out[i + 1] = " "
                state = None
                i += 2
                continue
            if ch != "\n":
                out[i] = " "
            i += 1
            continue
        # 문자열·문자 리터럴
        if ch == "\\":
            i += 2
            continue
        if (state == "dquote" and ch == '"') or (state == "squote" and ch == "'"):
            state = None
        i += 1
    return "".join(out)


def build_line_map(text: str) -> list[int]:
    """인덱스 -> 1-기반 줄 번호."""
    lines = [1] * (len(text) + 1)
    ln = 1
    for i, ch in enumerate(text):
        lines[i] = ln
        if ch == "\n":
            ln += 1
    lines[len(text)] = ln
    return lines


def collect_ignores(text: str, code: str) -> dict[int, set[str]]:
    """`pipa-guard:ignore <RULE> <이유>` 지시자를 수집한다. 이유가 없으면 무시한다.

    억제 범위는 `@SuppressWarnings`와 같은 감각으로 정한다. 지시자가 있는 줄과, 그
    다음 비어 있지 않은 줄에서 시작하는 구문 단위 전체다. 메서드 선언 위에 두면 그
    메서드 본문 전체가, 문장 끝에 두면 그 문장만 억제된다.
    """
    src_lines = text.splitlines()
    code_lines = code.splitlines()

    # 각 줄이 시작될 때의 중괄호 깊이. 주석이 제거된 코드로 계산한다.
    depth_at = [0] * (len(code_lines) + 2)
    depth = 0
    for i, line in enumerate(code_lines, start=1):
        depth_at[i] = depth
        for ch in line:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1

    result: dict[int, set[str]] = {}
    for idx, raw in enumerate(src_lines, start=1):
        m = IGNORE_RE.search(raw)
        if not m:
            continue
        rule = m.group(1)
        targets = {idx}

        next_line = None
        for j in range(idx + 1, len(code_lines) + 1):
            if code_lines[j - 1].strip():
                next_line = j
                break
        if next_line is not None:
            base = depth_at[next_line]
            targets.add(next_line)
            j = next_line + 1
            while j <= len(code_lines) and depth_at[j] > base:
                targets.add(j)
                j += 1

        for target in targets:
            result.setdefault(target, set()).add(rule)
    return result


@dataclass
class Statement:
    line: int
    text: str  # 공백이 정규화된 한 줄


@dataclass
class Source:
    path: str
    text: str
    code: str
    statements: list[Statement]
    ignores: dict[int, set[str]] = dc_field(default_factory=dict)
    config: dict = dc_field(default_factory=lambda: dict(DEFAULT_CONFIG))

    @property
    def is_kotlin(self) -> bool:
        return self.path.endswith((".kt", ".kts"))


ONLY_ANNOTATIONS_RE = re.compile(
    r"^(?:@(?:(?:field|get|set|property|param|receiver):)?[A-Za-z_][\w.]*"
    r"\s*(?:\((?:[^()]|\([^()]*\))*\))?\s*)+$"
)
ANNOTATED_DECL_RE = re.compile(
    r"\b(?:class|interface|enum|record|object|public|private|protected|internal|"
    r"fun|val|var)\b"
)
CONTINUES_RE = re.compile(r"(?:[,+\-*/%=<>!&|?:.]|->)$")
MAX_MERGE = 12


def _balanced(text: str) -> bool:
    depth = 0
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
            if depth < 0:
                return True  # 닫힘이 더 많으면 앞 문장이 잘린 것 — 더 붙이지 않는다.
    return depth == 0


def _needs_continuation(text: str) -> bool:
    if not _balanced(text):
        return True
    if ONLY_ANNOTATIONS_RE.match(text):
        return True
    # 문자열 안의 SQL 함수처럼 괄호가 여러 겹인 어노테이션은 위 정규식만으로 완전히
    # 파싱하기 어렵다. 선언 키워드가 아직 없다면 다음 조각까지 이어 붙인다.
    if text.lstrip().startswith("@") and not ANNOTATED_DECL_RE.search(text):
        return True
    if CONTINUES_RE.search(text):
        return True
    return False


def split_statements(code: str, line_map: list[int]) -> list[Statement]:
    """`;` `{` `}` 줄바꿈을 경계로 자른 뒤, 이어지는 조각을 다시 붙인다.

    Kotlin은 `;`를 쓰지 않으므로 줄바꿈도 경계로 삼아야 한다. 대신 다음 세 경우는
    다음 조각과 합친다.
      - 괄호가 닫히지 않은 조각 (여러 줄에 걸친 호출)
      - 어노테이션만으로 이루어진 조각 (`@Convert(...)` 다음 줄에 필드 선언)
      - 연산자나 쉼표로 끝나는 조각

    결과적으로 `@Convert(...) @Column(...) private String password` 처럼
    어노테이션과 필드 선언을 한 문장으로 함께 볼 수 있다.
    """
    pieces: list[tuple[int, str]] = []
    seg_start = 0
    bounds = [i for i, ch in enumerate(code) if ch in ";{}\n"] + [len(code)]
    for i in bounds:
        seg = code[seg_start:i]
        if seg.strip():
            offset = len(seg) - len(seg.lstrip())
            pieces.append((line_map[seg_start + offset], " ".join(seg.split())))
        seg_start = i + 1

    out: list[Statement] = []
    buf: list[str] = []
    buf_line = 0
    for line, text in pieces:
        # Java·Kotlin fluent API가 이전 호출을 닫은 뒤 다음 줄을 `.uri(...)`처럼 점으로
        # 시작하는 경우다. 앞 조각은 괄호가 닫혀 있어 이미 out에 들어갔을 수 있으므로
        # 다시 꺼내 하나의 호출 체인으로 합친다.
        if not buf and text.lstrip().startswith(".") and out:
            previous = out.pop()
            buf_line = previous.line
            buf.append(previous.text)
        if not buf:
            buf_line = line
        buf.append(text)
        joined = " ".join(buf)
        if len(buf) < MAX_MERGE and _needs_continuation(joined):
            continue
        out.append(Statement(line=buf_line, text=joined))
        buf = []
    if buf:
        out.append(Statement(line=buf_line, text=" ".join(buf)))
    return out


def prepare(path: str, text: str, config: dict | None = None) -> Source:
    code = strip_comments(text)
    line_map = build_line_map(code)
    return Source(
        path=path,
        text=text,
        code=code,
        statements=split_statements(code, line_map),
        ignores=collect_ignores(text, code),
        config=dict(config or DEFAULT_CONFIG),
    )


# --------------------------------------------------------------------------- #
# 패턴 — 모두 실제 Java/Kotlin 암호 API 기준
# --------------------------------------------------------------------------- #

TWO_WAY_CRYPTO = [
    (r"\bCipher\s*\.\s*getInstance\s*\(", "javax.crypto.Cipher"),
    (r"\bSecretKeySpec\b", "javax.crypto.spec.SecretKeySpec"),
    (r"\bIvParameterSpec\b", "javax.crypto.spec.IvParameterSpec"),
    (r"\bGCMParameterSpec\b", "javax.crypto.spec.GCMParameterSpec"),
    (r"\bEncryptors\s*\.\s*(?:text|delux|standard|stronger|queryableText)\b",
     "Spring Security Encryptors (양방향)"),
    (r"\bAesBytesEncryptor\b", "Spring Security AesBytesEncryptor"),
    (r"\b(?:Text|Bytes)Encryptor\b", "Spring Security TextEncryptor/BytesEncryptor"),
    (r"\bStandardPBEStringEncryptor\b", "Jasypt StandardPBEStringEncryptor"),
    (r"\bAES256Util\b|\bAesUtil\b|\bAES256\b|\bAESUtil\b", "AES 유틸리티"),
    (r'"\s*(?:AES|DESede|TripleDES|SEED|ARIA|Blowfish|RC2|RC4|ARCFOUR)\b',
     "양방향 암호 알고리즘 문자열"),
    (r"\b(?:AES|DESede|TripleDES|SEED|ARIA|Blowfish)\b", "양방향 암호 알고리즘"),
    (r"\.\s*encrypt\s*\(", ".encrypt() 호출"),
    (r"\.\s*decrypt\s*\(", ".decrypt() 호출"),
    (r"\.\s*doFinal\s*\(", "Cipher.doFinal()"),
]

# Base64는 암호화가 아니다. 단순 인코딩을 암호화로 오인한 코드를 잡는다.
BASE64_ENCODE = [
    (r"\bBase64\s*\.\s*get(?:Url|Mime)?Encoder\b", "Base64 인코딩(암호화가 아님)"),
    (r"\bBase64\s*\.\s*encodeBase64(?:String)?\b", "Base64 인코딩(암호화가 아님)"),
    (r"\bBase64Utils\s*\.\s*encode", "Base64 인코딩(암호화가 아님)"),
]

WEAK_HASH = [
    (r'\bgetInstance\s*\(\s*"\s*(?:MD2|MD4|MD5|SHA-?1)\s*"', "MD2/MD4/MD5/SHA-1"),
    (r"\bDigestUtils\s*\.\s*(?:md2|md5|md5Hex|md5DigestAsHex|sha1|sha1Hex|shaHex)\s*\(",
     "DigestUtils 취약 해시"),
    (r"\bHashing\s*\.\s*(?:md5|sha1)\s*\(", "Guava Hashing 취약 해시"),
    (r"\bMd5Crypt\b", "Md5Crypt"),
]

STRONG_HASH = [
    r'\bgetInstance\s*\(\s*"\s*SHA-?(?:224|256|384|512)',
    r'\bgetInstance\s*\(\s*"\s*SHA3',
    r"\bDigestUtils\s*\.\s*sha(?:256|384|512)",
    r"\bHashing\s*\.\s*sha(?:256|384|512)",
    r"\bPBKDF2|\bPbkdf2",
    r"\bMac\s*\.\s*getInstance\b|\bHmac",
]

# 제7조 제1항 단서를 충족하는 일방향 암호화 수단
SAFE_ONE_WAY = [
    r"\bPasswordEncoder\b",
    r"\bPasswordEncoderFactories\b",
    r"\bBCrypt\b",
    r"\bArgon2\b",
    r"\bSCrypt\b|\bScryptUtil\b|\bSCryptUtil\b",
    r"\bPbkdf2|\bPBKDF2",
]

# 시스템 계정 크리덴셜(DB 접속 비밀번호 등)은 제7조 제1항 단서의 "비밀번호"가 아니다.
# 제2조 제8호는 정보주체·개인정보취급자가 접속 시 입력하는 문자열로 정의한다.
CONFIG_CREDENTIAL = [
    r"@Value\s*\(",
    r"@ConfigurationProperties\b",
    r"\bSystem\s*\.\s*getenv\b",
    r"\bSystem\s*\.\s*getProperty\b",
    r"\bgetProperty\s*\(",
    r"\bProperties\b",
    r"\bEnvironment\b",
    r"\bDataSource\b|\bHikari",
    r"\bKeyStore\b",
    r"\bJdbcUrl\b|\bjdbc:",
]

# 결제 API처럼 설정 객체의 시크릿 키를 HTTP Basic 인증용으로 Base64 인코딩하는 경우가 있다.
# 이 값은 정보주체의 비밀번호가 아니다. 직접 인코딩 문장을 통째로 제외하지 않고, 시크릿 키
# 접근자로부터 값을 받은 대입문의 좌변만 시스템 크리덴셜로 표시한다. C093·V070이 경계를 고정한다.
SYSTEM_SECRET_ACCESSOR = [
    r"\.\s*(?:get)?[Ss]ecret[Kk]ey\s*\(\s*\)",
]

# 비밀번호 확인 입력 비교로 보이는 신호
CONFIRM_HINT = [
    r"[Cc]onfirm", r"[Rr]eenter", r"[Rr]eEnter", r"[Rr]etype", r"[Aa]gain",
    r"[Mm]atch(?:es)?Confirm", r"[Vv]erifyInput",
]

# 알고리즘 객체를 변수에 담아 두고 다른 문장에서 개인정보에 적용하는 형태를 잡기 위한
# 얕은 값 전파용 패턴이다. 좌변 식별자에 알고리즘 종류를 표시해 둔다.
ASSIGN_RE = re.compile(r"([A-Za-z_$][\w$]*)\s*=\s*([^=].*)")
RECEIVER_BINDINGS = [
    (r'getInstance\s*\(\s*"\s*(?:MD2|MD4|MD5|SHA-?1)\s*"', "weak_hash", "MD2/MD4/MD5/SHA-1"),
    (r'getInstance\s*\(\s*"\s*SHA-?(?:224|256|384|512)', "strong_hash", "SHA-2"),
    (r'getInstance\s*\(\s*"\s*SHA3', "strong_hash", "SHA-3"),
    (r"\bMac\s*\.\s*getInstance\b", "strong_hash", "HMAC"),
    (r'\bSecretKeyFactory\s*\.\s*getInstance\s*\(\s*"\s*PBKDF2', "strong_hash", "PBKDF2"),
]
# 표시된 식별자가 실제로 값을 처리하는 호출 형태
RECEIVER_USE_RE = r"\b(?:%s)\s*\.\s*(?:digest|update|doFinal|encrypt|decrypt|generateSecret)\s*\("

# 알고리즘 이름 문자열. 상수에 담아 두고 getInstance에 넘기는 형태를 잡기 위한 것이다.
# 리터럴이 getInstance 문장에 없어도 상수를 따라가면 알고리즘을 알 수 있다.
ALG_NAME_LITERAL = [
    (r'^"\s*(?:MD2|MD4|MD5|SHA-?1)\s*"$', "weak_hash", "MD2/MD4/MD5/SHA-1"),
    (r'^"\s*SHA-?(?:224|256|384|512)', "strong_hash", "SHA-2"),
    (r'^"\s*SHA3', "strong_hash", "SHA-3"),
    (r'^"\s*PBKDF2', "strong_hash", "PBKDF2"),
    (r'^"\s*Hmac', "strong_hash", "HMAC"),
    (r'^"\s*(?:AES|ARIA|SEED|DESede|DES|Blowfish|RC2|RC4)\b', "two_way", "양방향 암호 알고리즘"),
]

# getInstance에 리터럴이 아니라 식별자가 넘어가는 형태. 그 식별자를 상수 표에서 찾는다.
GET_INSTANCE_ARG_RE = re.compile(r"getInstance\s*\(\s*([A-Za-z_$][\w$.]*)\s*[),]")
# 문장 안의 호출 이름. 표시된 팩토리 메서드를 호출하는지 본다.
CALL_NAME_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")
RETURN_RE = re.compile(r"^\s*return\b(.*)$")
# 메서드 선언. 수식어가 하나 이상 있어야 인정한다. Kotlin의 fun·override도 받는다.
METHOD_DECL_RE = re.compile(
    r"^\s*(?:@\w+[\w\s.\"'(),${}=-]*?\s+)?"
    r"(?:(?:public|private|protected|internal|static|final|synchronized|abstract|"
    r"default|native|strictfp|open|override|suspend|fun|inline|operator)\s+)+"
    r"[\w<>\[\]?,.$ ]*?\b([A-Za-z_$][\w$]*)\s*\("
)
NOT_METHOD_NAMES = {
    "if", "for", "while", "switch", "catch", "return", "new", "synchronized",
    "super", "this", "do", "else", "try", "when",
}
# 전파 라운드 수. 팩토리 메서드가 사용처보다 뒤에 선언되는 것이 흔하므로 여러 번 돈다.
# 고정 횟수이므로 판정은 결정적이다.
PROPAGATION_ROUNDS = 3

CONVERT_RE = re.compile(
    r"@(?:(?:field|get|set|property|param|receiver):)?Convert\s*\(([^)]*)\)"
)
CRYPTO_WORD_RE = re.compile(r"AES|Aes|ARIA|Aria|SEED|Seed|Cipher|Crypto|Encrypt|Decrypt|TwoWay|Reversible|Symmetric")
ONEWAY_WORD_RE = re.compile(r"BCrypt|Bcrypt|BCRYPT|Argon|SCrypt|Scrypt|Pbkdf|PBKDF|Hash|Digest|OneWay|SHA|Sha")
EQUALS_RE = re.compile(r"\.\s*equals(?:IgnoreCase)?\s*\(")

# K-ENC-001 저장 구조. Kotlin의 use-site target(@field:)도 Java 어노테이션과 같은 의미로 본다.
USE_SITE = r"(?:(?:field|get|set|property|param|receiver):)?"
PERSISTENCE_TYPE_RE = re.compile(r"@(?:Entity|Embeddable|MappedSuperclass)\b")
COLUMN_RE = re.compile(r"@" + USE_SITE + r"Column\b(?:\(([^)]*)\))?")
TRANSIENT_RE = re.compile(r"@" + USE_SITE + r"Transient\b|\btransient\s+")
COLUMN_TRANSFORMER_RE = re.compile(r"@" + USE_SITE + r"ColumnTransformer\b")
COLUMN_LENGTH_RE = re.compile(r"\blength\s*=\s*(\d+)\b")
JAVA_FIELD_RE = re.compile(
    r"\b(?:public|protected|private)\s+(?:(?:final|volatile|transient)\s+)*"
    r"[A-Za-z_$][\w$<>,.?\[\] ]*\s+[A-Za-z_$][\w$]*(?:\s*=.*)?$"
)
KOTLIN_FIELD_RE = re.compile(r"\b(?:val|var)\s+[A-Za-z_$][\w$]*\s*:\s*[^,;)]+(?:\s*=.*)?$")
STATIC_FIELD_RE = re.compile(r"\bstatic\b|\bcompanion\s+object\b")

SQL_WRITE_RE = re.compile(r"\b(?:INSERT\s+INTO|UPDATE\s+[A-Za-z_])", re.IGNORECASE)
SQL_WRITE_CALL_RE = re.compile(r"\.\s*(?:update|batchUpdate|execute)\s*\(", re.IGNORECASE)
SQL_CRYPTO_RE = re.compile(
    r"\b(?:pgp_sym_encrypt|aes_encrypt|encrypt|encrypt_iv)\s*\(", re.IGNORECASE
)
INLINE_CRYPTO_ARG_RE = re.compile(
    r"(?:\.\s*(?:encrypt|doFinal)\s*\(|\b(?:Encryptors?\w*|AES\w*)\s*\([^,]*,)"
    r"\s*([A-Za-z_$][\w$]*)",
    re.IGNORECASE,
)
STRING_LITERAL_RE = re.compile(r'"(?:\\.|[^"\\])*"')

# K-ENC-005 로컬 파일 저장 구조. 범용 write()를 파일 sink로 오인하지 않도록 정적 Files API와
# 선언된 java.io 파일 수신자, Kotlin File 수신자만 인정한다.
FILES_WRITE_RE = re.compile(r"\bFiles\s*\.\s*(?:write|writeString)\s*\(")
FILE_STREAM_DECL_RE = re.compile(
    r"\b(?:FileOutputStream|FileWriter)\s+([A-Za-z_$][\w$]*)\b"
)
JAVA_FILE_DECL_RE = re.compile(r"\bFile\s+([A-Za-z_$][\w$]*)\b")
KOTLIN_FILE_ASSIGN_RE = re.compile(
    r"\b(?:val|var)\s+([A-Za-z_$][\w$]*)\s*(?::\s*File\s*)?=\s*"
    r"(?:java\s*\.\s*io\s*\.\s*)?File\s*\("
)
FILE_MEMBER_WRITE_RE = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*\.\s*"
    r"(write|append|writeText|writeBytes|appendText|appendBytes)\s*\("
)
ONE_WAY_ENCODER_DECL_RE = re.compile(
    r"\b(?:PasswordEncoder|BCryptPasswordEncoder|Argon2PasswordEncoder|"
    r"SCryptPasswordEncoder|Pbkdf2PasswordEncoder)\s+([A-Za-z_$][\w$]*)\b"
)

# K-ENC-004 전송 구조. Java·Kotlin의 명시적 HTTP 클라이언트 호출만 본다.
HTTP_CLIENT_CONTEXT_RE = re.compile(
    r"\b(?:RestTemplate|RestClient|WebClient|HttpClient|HttpRequest|OkHttpClient|"
    r"CloseableHttpClient|ClassicHttpRequest|ClassicRequestBuilder|Retrofit|"
    r"FeignClient|HttpServiceProxyFactory|HttpExchange|GetExchange|PostExchange|"
    r"PutExchange|PatchExchange|DeleteExchange|HttpURLConnection|URLConnection)\b"
)
HTTP_SEND_CALL_RE = re.compile(
    r"\.\s*(?:postForObject|postForEntity|put|patchForObject|exchange|getForObject|"
    r"getForEntity|enqueue|exchangeToMono|exchangeToFlux)\s*\(",
    re.IGNORECASE,
)
HTTP_RETRIEVE_TERMINAL_RE = re.compile(
    r"\.\s*retrieve\s*\(\s*\).*?\.\s*(?:body|bodyToMono|bodyToFlux|toEntity|"
    r"toBodilessEntity)\s*\(",
    re.IGNORECASE,
)
OKHTTP_SEND_CALL_RE = re.compile(
    r"\.\s*newCall\s*\([^)]*\)\s*\.\s*(?:execute|enqueue)\s*\(",
    re.IGNORECASE,
)
APACHE_HTTP_CONTEXT_RE = re.compile(
    r"\b(?:CloseableHttpClient|ClassicHttpRequest|ClassicRequestBuilder|HttpClients)\b"
)
APACHE_HTTP_CLIENT_DECL_RE = re.compile(
    r"\b(?:CloseableHttpClient|HttpClient)\s+([A-Za-z_$][\w$]*)\b"
)
JDK_HTTP_CLIENT_DECL_RE = re.compile(
    r"(?:\bjava\s*\.\s*net\s*\.\s*http\s*\.\s*)?"
    r"\bHttpClient\s+([A-Za-z_$][\w$]*)\b"
)
DECLARATIVE_INTERFACE_RE = re.compile(
    r"\binterface\s+([A-Za-z_$][\w$]*)[^{}]*\{([^{}]*)\}", re.DOTALL
)
FEIGN_CLIENT_BEFORE_INTERFACE_RE = re.compile(
    r"@(?:[A-Za-z_$][\w$]*\.)*FeignClient\s*"
    r"\(((?:[^()]|\([^()]*\))*)\)\s*(?:(?:public|protected|private)\s+)?$",
    re.DOTALL,
)
FEIGN_URL_RE = re.compile(r"\burl\s*=\s*(\"(?:\\.|[^\"\\])*\")")
SPRING_HTTP_METHOD_ANNOTATION_RE = re.compile(
    r"@(?:[A-Za-z_$][\w$]*\.)*(?:HttpExchange|GetExchange|PostExchange|PutExchange|"
    r"PatchExchange|DeleteExchange)\b\s*(?:\((?:[^()]|\([^()]*\))*\))?"
)
FEIGN_HTTP_METHOD_ANNOTATION_RE = re.compile(
    r"@(?:[A-Za-z_$][\w$]*\.)*(?:RequestMapping|GetMapping|PostMapping|PutMapping|"
    r"PatchMapping|DeleteMapping)\b\s*(?:\((?:[^()]|\([^()]*\))*\))?"
)
RETROFIT_HTTP_METHOD_ANNOTATION_RE = re.compile(
    r"@(?:[A-Za-z_$][\w$]*\.)*(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|HTTP)\b"
    r"\s*(?:\((?:[^()]|\([^()]*\))*\))?"
)
DECLARATIVE_TERMINAL_RE = {
    "retrofit_call": re.compile(r"\.\s*(?:execute|enqueue)\s*\(", re.IGNORECASE),
    "reactive": re.compile(r"\.\s*(?:block|subscribe)\s*\(", re.IGNORECASE),
}
HTTP_URL_LITERAL_RE = re.compile(r'"(https?://(?:\\.|[^"\\])*)"', re.IGNORECASE)
KOTLIN_INTERPOLATION_RE = re.compile(r"\$(?:\{\s*)?([A-Za-z_$][\w$]*)")
DTO_MUTATOR_RE = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*\.\s*(?:set|with|add|put)[A-Z_][A-Za-z0-9_$]*\s*\("
)
TLS_VERIFICATION_DISABLED = [
    (r"\bNoopHostnameVerifier\s*\.\s*INSTANCE\b", "NoopHostnameVerifier.INSTANCE"),
    (r"\bAllowAllHostnameVerifier\s*\.\s*INSTANCE\b", "AllowAllHostnameVerifier.INSTANCE"),
    (r"\bTrustAllStrategy\s*\.\s*INSTANCE\b", "TrustAllStrategy.INSTANCE"),
    (r"\bInsecureTrustManagerFactory\s*\.\s*INSTANCE\b", "InsecureTrustManagerFactory.INSTANCE"),
    (r"\b(?:setSSLHostnameVerifier|setHostnameVerifier|hostnameVerifier)\s*\(\s*"
     r"\([^)]*\)\s*->\s*true", "항상 true를 반환하는 HostnameVerifier"),
]

# K-ENC-004 서버 수신 구조. 요청 매핑과 요청값 바인딩이 한 메서드 선언에 함께 있어야 한다.
SERVER_CONTROLLER_CONTEXT_RE = re.compile(
    r"@(?:[A-Za-z_$][\w$]*\.)*(?:RestController|Controller)\b"
)
SERVER_MAPPING_RE = re.compile(
    r"@(?:[A-Za-z_$][\w$]*\.)*(?:RequestMapping|GetMapping|PostMapping|PutMapping|"
    r"PatchMapping|DeleteMapping)\b"
)
SERVER_REQUEST_BINDING_RE = re.compile(
    r"@(?:[A-Za-z_$][\w$]*\.)*(?:RequestBody|RequestParam|RequestHeader|PathVariable|"
    r"ModelAttribute|CookieValue)\b"
)
SERVER_DTO_DECL_RE = re.compile(
    r"\b(?:(?:data\s+)?class|record)\s+([A-Z][A-Za-z0-9_$]*)\b"
)

# K-LEAK-001/002 출력 sink. 일반 객체의 info()를 로그로 오인하지 않도록 선언된 logger
# 수신자와 Lombok의 @Slf4j 기본 수신자만 인정한다.
LOGGER_DECL_RE = re.compile(
    r"\b(?:Logger|KLogger)\s+([A-Za-z_$][\w$]*)\b|"
    r"\b([A-Za-z_$][\w$]*)\s*=\s*(?:LoggerFactory\s*\.\s*getLogger|"
    r"KotlinLogging\s*\.\s*logger)\b"
)
LOMBOK_LOG_RE = re.compile(r"@(?:[A-Za-z_$][\w$]*\.)?Slf4j\b")
LOG_CALL_RE = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*\.\s*(?:trace|debug|info|warn|error|log|severe|"
    r"warning|fine|finer|finest)\s*\("
)

# IV(12바이트)와 GCM 인증 태그(16바이트)에 열거된 번호 항목의 암호문을 더해 Base64로
# 저장하면 44자를 넘는다. 그보다 짧은 컬럼은 일반 영속 필드보다 강한 부재 증거다. (D-05)
MIN_ENCRYPTED_TEXT_LENGTH = 44


def _first(patterns, text: str):
    for pattern, label in patterns:
        m = re.search(pattern, text)
        if m:
            return label, m
    return None, None


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


def _call_arguments_at(text: str, open_paren: int) -> list[str] | None:
    """호출의 여는 괄호 위치에서 최상위 인자를 자른다.

    Java·Kotlin 문자열과 괄호·대괄호·중괄호 안의 쉼표는 인자 경계로 보지 않는다. 완전한 AST를
    만들지 않고 명시적 sink의 payload 자리만 좁게 읽기 위한 보조 함수다.
    """
    if open_paren < 0 or open_paren >= len(text) or text[open_paren] != "(":
        return None
    arguments: list[str] = []
    start = open_paren + 1
    paren_depth = 1
    bracket_depth = 0
    brace_depth = 0
    quote: str | None = None
    escaped = False
    for index in range(open_paren + 1, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
            if paren_depth == 0:
                arguments.append(text[start:index].strip())
                return arguments if arguments != [""] else []
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth = max(0, brace_depth - 1)
        elif (char == "," and paren_depth == 1
              and bracket_depth == 0 and brace_depth == 0):
            arguments.append(text[start:index].strip())
            start = index + 1
    return None


def redact(text: str) -> str:
    """근거 코드에 개인정보 리터럴이 섞여 나가지 않게 가린다.

    주민등록번호 전체 값을 로그·보고서에 남기지 않는다는 원칙을 검출기 자신도 지킨다.
    """
    text = re.sub(r"\b(\d{6})[-\s]?\d{7}\b", r"\1-*******", text)
    text = re.sub(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "****-****-****-****", text)
    text = re.sub(r"\b\d{8,}\b", lambda m: m.group(0)[:2] + "*" * (len(m.group(0)) - 2), text)
    text = re.sub(r'"([^"]{41,})"', lambda m: '"%s…"' % m.group(1)[:38], text)
    if len(text) > MAX_EVIDENCE:
        text = text[: MAX_EVIDENCE - 1] + "…"
    return text


# --------------------------------------------------------------------------- #
# 규칙 K-ENC-002 — 비밀번호 일방향 암호화 (제7조 제1항 단서)
# --------------------------------------------------------------------------- #

ART_7_1 = "개인정보의 안전성 확보조치 기준 제7조 제1항"
QUOTE_7_1 = (
    "개인정보처리자는 비밀번호, 생체인식정보 등 인증정보를 저장 또는 정보통신망을 통하여\n"
    "송ㆍ수신하는 경우에 이를 안전한 암호 알고리즘으로 암호화하여야 한다.\n"
    "다만, 비밀번호를 저장하는 경우에는 복호화되지 아니하도록 일방향 암호화하여\n"
    "저장하여야 한다."
)

FIX_ONE_WAY = (
    "BCryptPasswordEncoder, Argon2PasswordEncoder 등 PasswordEncoder 구현체의 encode()로 "
    "일방향 해시하여 저장하고, 복호화 경로(decrypt/doFinal)를 제거하십시오. "
    "인증은 passwordEncoder.matches(rawPassword, encodedPassword)로 수행합니다."
)


def _auth_hits(statement: str, dic: Dictionary):
    """문장에서 일방향 암호화 대상 식별자를 찾는다. -> [(원본 식별자, 항목, 강도)]

    제7조 제1항 단서의 대상은 "비밀번호를 저장하는 경우"다. 따라서 사전에서
    `encryption == "one_way_only"` 인 항목만 고른다. 분류(`category`)로 고르면
    생체인식정보가 걸린다 — 제2조 제11호의 인증정보이지만 단서 대상이 아니어서
    양방향 암호화가 적법하다. 방어선은 C015다.
    """
    hits = []
    seen = set()
    for m in IDENT_RE.finditer(statement):
        ident = m.group(0)
        if ident in seen:
            continue
        seen.add(ident)
        item, strength = dic.match(ident)
        if item is not None and item.get("encryption") == "one_way_only":
            hits.append((ident, item, strength))
    return hits


def _config_credential_idents(src: Source, dic: Dictionary) -> set[str]:
    """설정에서 주입된 시스템 크리덴셜 식별자를 모은다.

    `@Value("${spring.datasource.password}") private String dbPassword;` 처럼 선언은
    설정 신호와 함께 있지만 사용은 다른 문장에서 일어난다. 선언 시점에 식별자를 표시해
    두어야 사용 문장에서도 대상 밖으로 판정할 수 있다. 파일 범위의 얕은 전파다.
    """
    marked: set[str] = set()
    for st in src.statements:
        if _any(CONFIG_CREDENTIAL, st.text):
            for ident, _item, _strength in _auth_hits(st.text, dic):
                marked.add(normalize_ident(ident))
            continue

        # `String credential = properties.secretKey() + ":";` 같은 명시적 대입만 전파한다.
        # 같은 문장의 사용자 password까지 제외하면 실제 위반이 숨으므로 좌변 하나만 본다.
        if _any(SYSTEM_SECRET_ACCESSOR, st.text):
            assign = ASSIGN_RE.search(st.text)
            if not assign:
                continue
            target = assign.group(1)
            item, _strength = dic.match(target)
            if item is not None and item.get("encryption") == "one_way_only":
                marked.add(normalize_ident(target))
    return marked


def _method_name(text: str) -> str | None:
    """문장이 메서드 선언이면 메서드명을 준다. 아니면 None."""
    m = METHOD_DECL_RE.match(text)
    # 경로 문자열(`/members/...`)이 든 Spring 매핑 어노테이션은 METHOD_DECL_RE의 가벼운
    # 어노테이션 문자 집합을 벗어난다. 공통 어노테이션 제거기를 거친 선언으로 한 번 더 본다.
    if not m:
        m = METHOD_DECL_RE.match(ANNOTATION_RE.sub(" ", text))
    if not m:
        return None
    name = m.group(1)
    if name in NOT_METHOD_NAMES:
        return None
    return name


def _alg_const_kind(rhs: str):
    """우변이 알고리즘 이름 문자열 하나뿐이면 종류를 준다. -> (종류, 표시명)"""
    value = rhs.strip().rstrip(";").strip()
    for pattern, kind, label in ALG_NAME_LITERAL:
        if re.match(pattern, value, re.IGNORECASE):
            return kind, label
    return None, None


def _crypto_receivers(src: Source) -> dict[str, tuple[str, str, int]]:
    """알고리즘 객체를 담은 변수를 찾아 종류를 표시한다. -> {식별자: (종류, 표시명, 결정행)}

    `MessageDigest digest = MessageDigest.getInstance("SHA-1");` 처럼 알고리즘 선택은
    한 문장에서 하고, 그 객체를 개인정보에 적용하는 것은 다른 문장에서 한다. 문장 하나만
    보면 어느 쪽도 위반으로 보이지 않는다. 알고리즘을 담은 변수를 표시해 두어야 적용
    문장에서 판정할 수 있다. 파일 범위의 얕은 값 전파다.

    실제 생성 코드는 여기에 두 겹의 간접 참조를 더 얹는다. (V008)

        private static final String ALGORITHM = "SHA-1";        // 리터럴은 상수에
        private static MessageDigest newDigest() {
            return MessageDigest.getInstance(ALGORITHM);        // getInstance에 리터럴이 없다
        }
        MessageDigest md = newDigest();                         // 인스턴스는 팩토리 반환값
        return md.digest(rawPin.getBytes(UTF_8));               // 여기가 적용 지점

    그래서 세 가지를 함께 표시한다.
      alg_consts  알고리즘 이름 문자열을 담은 상수
      factories   알고리즘 객체를 반환하는 메서드
      receivers   알고리즘 객체를 담은 변수 (반환값)

    팩토리 메서드가 사용처보다 뒤에 선언되는 것이 흔하므로 고정 횟수만큼 반복해서
    전파한다. 횟수가 고정이므로 판정은 결정적이다.

    전파 대상이 되려면 알고리즘 종류가 확정되어야 한다. 파일 안에 SHA-1이 있다는 이유로
    무관한 문장을 물들이지 않는다. `C013`(SHA-1 체크섬 팩토리와 BCrypt 비밀번호가 한
    클래스에 공존)과 `C012`(같은 구조인데 상수가 PBKDF2)가 그 방어선이다.
    """
    alg_consts: dict[str, tuple[str, str]] = {}
    factories: dict[str, tuple[str, str, int]] = {}
    receivers: dict[str, tuple[str, str, int]] = {}

    def classify(expr: str):
        """식이 알고리즘 객체를 만들어 내는지 본다. -> (종류, 표시명)"""
        for pattern, kind, label in RECEIVER_BINDINGS:
            if re.search(pattern, expr):
                return kind, label

        # getInstance(ALGORITHM) — 인자가 표시된 상수인 경우
        for m in GET_INSTANCE_ARG_RE.finditer(expr):
            arg = normalize_ident(m.group(1).split(".")[-1])
            if arg in alg_consts:
                return alg_consts[arg]

        # newDigest() — 표시된 팩토리 메서드 호출
        for m in CALL_NAME_RE.finditer(expr):
            name = normalize_ident(m.group(1))
            if name in factories:
                kind, label, _line = factories[name]
                return kind, label

        # md.digest(...) — 표시된 변수를 실제로 값 처리에 쓰는 경우.
        # 판정 규칙은 적용 문장과 같아야 하므로 _receiver_hit을 그대로 쓴다.
        kind, label, _line = _receiver_hit(expr, receivers)
        if kind is not None:
            return kind, label

        crypto_label, _ = _first(TWO_WAY_CRYPTO, expr)
        if crypto_label:
            return "two_way", crypto_label
        return None, None

    for _round in range(PROPAGATION_ROUNDS):
        current_method: str | None = None
        for st in src.statements:
            name = _method_name(st.text)
            if name is not None:
                current_method = normalize_ident(name)

            assign = ASSIGN_RE.search(st.text)
            if assign:
                target, rhs = assign.group(1), assign.group(2)

                const_kind, const_label = _alg_const_kind(rhs)
                if const_kind is not None:
                    alg_consts[normalize_ident(target)] = (const_kind, const_label)

                kind, label = classify(rhs)
                if kind is not None:
                    receivers[normalize_ident(target)] = (kind, label, st.line)

            ret = RETURN_RE.match(st.text)
            if ret and current_method is not None:
                kind, label = classify(ret.group(1))
                if kind is not None:
                    factories.setdefault(current_method, (kind, label, st.line))

    return receivers


def _receiver_hit(statement: str, receivers: dict[str, tuple[str, str, int]]):
    """문장이 표시된 알고리즘 변수를 사용하는지 본다. -> (종류, 표시명, 결정행)"""
    if not receivers:
        return None, None, 0
    for m in IDENT_RE.finditer(statement):
        norm = normalize_ident(m.group(0))
        if norm not in receivers:
            continue
        use = RECEIVER_USE_RE % re.escape(m.group(0))
        if re.search(use, statement):
            return receivers[norm]
    return None, None, 0


# --------------------------------------------------------------------------- #
# 규칙 K-ENC-001 — 이용자 개인정보 7항목 암호화 저장 (제7조 제2항)
# --------------------------------------------------------------------------- #

def _article7_storage_hits(statement: str, dic: Dictionary):
    """제7조 제2항의 양방향 암호화 허용 항목을 찾는다."""
    hits = []
    seen = set()
    for match in IDENT_RE.finditer(statement):
        ident = match.group(0)
        if ident in seen:
            continue
        seen.add(ident)
        item, strength = dic.match(ident)
        if item is not None and item.get("encryption") == "two_way_allowed":
            hits.append((ident, item, strength))
    return hits


def _protected_value_idents(src: Source, dic: Dictionary) -> set[str]:
    """암호화 결과를 담은 식별자를 파일 범위에서 얕게 표시한다.

    `encrypted = encryptor.encrypt(residentNumber)` 다음 문장의 SQL 쓰기나 HTTP 송신에서
    `encrypted`만 전달되는 형태를 적법으로 판정하기 위한 것이다. 저장 규칙의 7항목뿐 아니라
    전송 전용 일반 개인정보도 보호값이 될 수 있으므로 사전의 모든 항목을 시작점으로 삼는다.
    이름의 encrypted 접두어는 증거로 쓰지 않고 우변의 실제 암호 호출에서 시작한다. 표시된
    값을 다시 대입하는 경우만 고정 횟수로 전파한다.
    """
    protected: set[str] = set()
    for _round in range(PROPAGATION_ROUNDS):
        for statement in src.statements:
            assign = ASSIGN_RE.search(statement.text)
            if not assign:
                continue
            target, rhs = assign.group(1), assign.group(2)
            target_norm = normalize_ident(target)

            crypto_label, _ = _first(TWO_WAY_CRYPTO, rhs)
            encrypts_pii_item = any(
                dic.match(match.group(0))[0] is not None
                for match in IDENT_RE.finditer(rhs)
            )
            inherited = any(
                normalize_ident(match.group(0)) in protected
                for match in IDENT_RE.finditer(rhs)
            )
            if (crypto_label and encrypts_pii_item) or inherited:
                protected.add(target_norm)
    return protected


def _one_way_protected_hits(
    expression: str,
    dic: Dictionary,
    encoder_receivers: set[str],
) -> set[str]:
    """선언된 PasswordEncoder 수신자가 일방향 처리한 비밀번호 식별자를 찾는다."""
    protected: set[str] = set()
    for match in re.finditer(
        r"\b([A-Za-z_$][\w$]*)\s*\.\s*encode\s*\(", expression
    ):
        if normalize_ident(match.group(1)) not in encoder_receivers:
            continue
        arguments = _call_arguments_at(expression, match.end() - 1)
        if not arguments:
            continue
        for ident, _item, _strength in _auth_hits(arguments[0], dic):
            protected.add(normalize_ident(ident))
    return protected


def _local_storage_protected_idents(src: Source, dic: Dictionary) -> set[str]:
    """로컬 저장에서 안전한 암호화 결과로 확인된 식별자를 얕게 표시한다.

    제7조 제5항의 일반 개인정보에는 양방향 암호화 결과를, 비밀번호에는 제7조 제1항 단서의
    PasswordEncoder 일방향 결과도 보호값으로 인정한다. 일반 이름의 encode()는 인정하지 않는다.
    """
    protected = _protected_value_idents(src, dic)
    encoder_receivers = {
        normalize_ident(match.group(1))
        for match in ONE_WAY_ENCODER_DECL_RE.finditer(src.code)
    }
    for _round in range(PROPAGATION_ROUNDS):
        for statement in src.statements:
            assign = ASSIGN_RE.search(statement.text)
            if not assign:
                continue
            target, rhs = assign.group(1), assign.group(2)
            inherited = any(
                normalize_ident(match.group(0)) in protected
                for match in IDENT_RE.finditer(rhs)
            )
            if inherited or _one_way_protected_hits(rhs, dic, encoder_receivers):
                protected.add(normalize_ident(target))
    return protected


def _persistent_field(statement: str) -> bool:
    return bool(
        COLUMN_RE.search(statement)
        or JAVA_FIELD_RE.search(statement)
        or KOTLIN_FIELD_RE.search(statement)
    )


def _column_has_encryption(statement: str) -> bool:
    converter = CONVERT_RE.search(statement)
    if converter and CRYPTO_WORD_RE.search(converter.group(1)):
        return True
    if COLUMN_TRANSFORMER_RE.search(statement) and SQL_CRYPTO_RE.search(statement):
        return True
    crypto_label, _ = _first(TWO_WAY_CRYPTO, statement)
    return bool(crypto_label)


def _article_finding_fields(item: dict) -> tuple[str, str, str]:
    return (
        item.get("label", "개인정보"),
        "개인정보의 안전성 확보조치 기준 %s" % item.get("article", "제7조 제2항"),
        item.get("article_quote", ""),
    )


def rule_article7_user_storage(src: Source, dic: Dictionary) -> list[Finding]:
    """이용자의 제7조 제2항 7개 항목이 암호화 없이 저장되는 구조를 찾는다.

    `.pipa.json`이 이용자가 아닌 정보주체라고 명시한 경우에는 제3항 규칙의 범위이므로 여기서
    판정하지 않는다. 알 수 없는 값이나 설정 부재는 더 보수적인 이용자로 취급한다. (D-02)
    """
    if src.config.get("subjectType") == "non_user":
        return []

    findings: list[Finding] = []

    # 엔티티·임베디드 타입의 영속 필드. 짧은 명시 길이는 암호문을 담을 수 없으므로 high,
    # 그 외에는 애플리케이션 계층 암호화 가능성을 배제할 수 없어 경고만 한다.
    if PERSISTENCE_TYPE_RE.search(src.code):
        for statement in src.statements:
            if not _persistent_field(statement.text):
                continue
            if STATIC_FIELD_RE.search(statement.text) or TRANSIENT_RE.search(statement.text):
                continue

            hits = _article7_storage_hits(statement.text, dic)
            if not hits:
                continue

            strongest = "strong" if any(hit[2] == "strong" for hit in hits) else "weak"
            item = hits[0][1]
            label, article, quote = _article_finding_fields(item)
            column = COLUMN_RE.search(statement.text)
            length = None
            if column and column.group(1):
                length_match = COLUMN_LENGTH_RE.search(column.group(1))
                if length_match:
                    length = int(length_match.group(1))

            if length is not None and length < MIN_ENCRYPTED_TEXT_LENGTH:
                findings.append(Finding(
                    rule="K-ENC-001", check="plaintext-sized-column",
                    confidence="high" if strongest == "strong" else "medium",
                    path=src.path, line=statement.line,
                    message=("%s 영속 컬럼의 길이가 %d자로, IV와 인증 태그를 포함한 안전한 "
                             "암호문을 저장할 수 없습니다. 원문 크기의 컬럼은 암호화 부재를 "
                             "나타냅니다." % (label, length)),
                    article=article, quote=quote,
                    fix=("안전한 양방향 암호화 컨버터를 영속 경로에 연결하고, IV·인증 태그·"
                         "암호문을 담도록 사용하는 암호 형식의 실제 출력 길이에 맞춰 컬럼을 "
                         "넓히십시오."),
                    evidence=redact(statement.text),
                ))
                continue

            if _column_has_encryption(statement.text):
                continue

            findings.append(Finding(
                rule="K-ENC-001", check="unprotected-column",
                confidence="medium" if strongest == "strong" else "low",
                path=src.path, line=statement.line,
                message=("%s 영속 필드에 @Convert 또는 @ColumnTransformer 등의 암호화 연결이 "
                         "보이지 않습니다. 다른 계층에서 암호화할 가능성이 있어 차단하지 않고 "
                         "확인을 요청합니다." % label),
                article=article, quote=quote,
                fix=("AES-GCM 등 안전한 양방향 암호화 컨버터를 연결하거나, 저장 전에 암호화된 "
                     "값만 이 필드에 들어오는 경로를 코드로 드러내십시오."),
                evidence=redact(statement.text),
            ))

    # SQL 문자열과 값 인자가 같은 문장에 있는 명시적 INSERT/UPDATE. 암호화 결과로 표시된
    # 식별자와 DB 암호 함수는 제외하고, 원문 후보가 인자로 직접 남은 경우만 판정한다.
    has_sql_write = SQL_WRITE_RE.search(src.code) and SQL_WRITE_CALL_RE.search(src.code)
    if has_sql_write:
        protected_idents = _protected_value_idents(src, dic)
        for statement in src.statements:
            if not SQL_WRITE_RE.search(statement.text) or not SQL_WRITE_CALL_RE.search(statement.text):
                continue
            literals = " ".join(match.group(0) for match in STRING_LITERAL_RE.finditer(statement.text))
            if SQL_CRYPTO_RE.search(literals):
                continue

            outside_literals = STRING_LITERAL_RE.sub(" ", statement.text)
            hits = _article7_storage_hits(outside_literals, dic)
            inline_protected = {
                normalize_ident(match.group(1))
                for match in INLINE_CRYPTO_ARG_RE.finditer(outside_literals)
            }
            raw_hits = [
                hit for hit in hits
                if (normalize_ident(hit[0]) not in protected_idents
                    and normalize_ident(hit[0]) not in inline_protected)
            ]
            if not raw_hits:
                continue

            strongest = "strong" if any(hit[2] == "strong" for hit in raw_hits) else "weak"
            item = raw_hits[0][1]
            label, article, quote = _article_finding_fields(item)
            findings.append(Finding(
                rule="K-ENC-001", check="plaintext-sql-write",
                confidence="high" if strongest == "strong" else "medium",
                path=src.path, line=statement.line,
                message=("%s 원문 식별자가 SQL INSERT/UPDATE의 값 인자로 직접 전달되고 있으며, "
                         "그 경로에 암호화 호출이 없습니다." % label),
                article=article, quote=quote,
                fix=("AES-GCM 등 안전한 양방향 암호화 결과만 SQL 인자로 전달하거나, 검증된 "
                     "데이터베이스 암호 함수를 쓰기 식에 연결하십시오."),
                evidence=redact(statement.text),
            ))

    return findings


# --------------------------------------------------------------------------- #
# 규칙 K-ENC-003 — 비이용자 고유식별정보 암호화 저장 (제7조 제3항)
# --------------------------------------------------------------------------- #

def _assessment_exempts_unique_id(config: dict, item: dict) -> bool:
    """내부망의 주민등록번호 외 고유식별정보가 명시적 평가 범위에서 제외됐는지 본다.

    riskAssessment 객체가 있다는 사실만으로 암호화 의무를 끄지 않는다. 제7조 제3항 제2호의
    근거 종류, 결과 문서, 날짜, 미적용 결론과 항목별 적용범위가 모두 선언된 경우만 인정한다.
    주민등록번호는 법문상 단서 밖이므로 어떤 설정으로도 면제하지 않는다. (D-20)
    """
    if config.get("storageZone") != "internal":
        return False
    if item.get("key") == "residentRegistrationNumber":
        return False

    assessment = config.get("riskAssessment")
    if not isinstance(assessment, dict):
        return False
    if assessment.get("basis") not in ("privacy_impact_assessment", "risk_analysis"):
        return False
    if assessment.get("conclusion") != "encryption_not_required":
        return False

    document = assessment.get("document")
    date = assessment.get("date")
    exempt_items = assessment.get("exemptItems")
    if not isinstance(document, str) or not document.strip():
        return False
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return False
    try:
        calendar_date.fromisoformat(date)
    except ValueError:
        return False
    if not isinstance(exempt_items, list):
        return False
    return item.get("key") in exempt_items


def _article7_non_user_hits(statement: str, dic: Dictionary, config: dict):
    """제7조 제3항의 고유식별정보 중 현재 설정에서 암호화 의무가 남는 항목을 찾는다."""
    hits = []
    seen = set()
    for match in IDENT_RE.finditer(statement):
        ident = match.group(0)
        if ident in seen:
            continue
        seen.add(ident)
        item, strength = dic.match(ident)
        if item is None or item.get("category") != "unique_id":
            continue
        if _assessment_exempts_unique_id(config, item):
            continue
        hits.append((ident, item, strength))
    return hits


def _article7_non_user_finding_fields(item: dict) -> tuple[str, str, str]:
    return (
        item.get("label", "고유식별정보"),
        "개인정보의 안전성 확보조치 기준 제7조 제3항",
        QUOTE_7_3,
    )


def rule_article7_non_user_storage(src: Source, dic: Dictionary) -> list[Finding]:
    """비이용자의 고유식별정보가 제7조 제3항 분기에 맞게 암호화되는지 찾는다."""
    if src.config.get("subjectType") != "non_user":
        return []

    findings: list[Finding] = []
    storage_zone = src.config.get("storageZone")
    if storage_zone == "internal":
        zone = "내부망"
    elif storage_zone == "internet":
        zone = "인터넷망 구간 또는 DMZ"
    else:
        zone = "알 수 없는 저장 구간(인터넷망 기준)"

    if PERSISTENCE_TYPE_RE.search(src.code):
        for statement in src.statements:
            if not _persistent_field(statement.text):
                continue
            if STATIC_FIELD_RE.search(statement.text) or TRANSIENT_RE.search(statement.text):
                continue

            hits = _article7_non_user_hits(statement.text, dic, src.config)
            if not hits:
                continue

            strongest = "strong" if any(hit[2] == "strong" for hit in hits) else "weak"
            item = hits[0][1]
            label, article, quote = _article7_non_user_finding_fields(item)
            column = COLUMN_RE.search(statement.text)
            length = None
            if column and column.group(1):
                length_match = COLUMN_LENGTH_RE.search(column.group(1))
                if length_match:
                    length = int(length_match.group(1))

            if length is not None and length < MIN_ENCRYPTED_TEXT_LENGTH:
                findings.append(Finding(
                    rule="K-ENC-003", check="plaintext-sized-column",
                    confidence="high" if strongest == "strong" else "medium",
                    path=src.path, line=statement.line,
                    message=("%s에 저장하는 비이용자 %s 영속 컬럼의 길이가 %d자로, IV와 "
                             "인증 태그를 포함한 안전한 암호문을 저장할 수 없습니다. 원문 "
                             "크기의 컬럼은 암호화 부재를 나타냅니다."
                             % (zone, label, length)),
                    article=article, quote=quote,
                    fix=("안전한 양방향 암호화 컨버터를 영속 경로에 연결하고, IV·인증 태그·"
                         "암호문을 담도록 사용하는 암호 형식의 실제 출력 길이에 맞춰 컬럼을 "
                         "넓히십시오."),
                    evidence=redact(statement.text),
                ))
                continue

            if _column_has_encryption(statement.text):
                continue

            findings.append(Finding(
                rule="K-ENC-003", check="unprotected-column",
                confidence="medium" if strongest == "strong" else "low",
                path=src.path, line=statement.line,
                message=("%s에 저장하는 비이용자 %s 영속 필드에 @Convert 또는 "
                         "@ColumnTransformer 등의 암호화 연결이 보이지 않습니다. 다른 계층에서 "
                         "암호화할 가능성이 있어 차단하지 않고 확인을 요청합니다."
                         % (zone, label)),
                article=article, quote=quote,
                fix=("AES-GCM 등 안전한 양방향 암호화 컨버터를 연결하거나, 저장 전에 암호화된 "
                     "값만 이 필드에 들어오는 경로를 코드로 드러내십시오."),
                evidence=redact(statement.text),
            ))

    has_sql_write = SQL_WRITE_RE.search(src.code) and SQL_WRITE_CALL_RE.search(src.code)
    if has_sql_write:
        protected_idents = _protected_value_idents(src, dic)
        for statement in src.statements:
            if not SQL_WRITE_RE.search(statement.text) or not SQL_WRITE_CALL_RE.search(statement.text):
                continue
            literals = " ".join(match.group(0) for match in STRING_LITERAL_RE.finditer(statement.text))
            if SQL_CRYPTO_RE.search(literals):
                continue

            outside_literals = STRING_LITERAL_RE.sub(" ", statement.text)
            hits = _article7_non_user_hits(outside_literals, dic, src.config)
            inline_protected = {
                normalize_ident(match.group(1))
                for match in INLINE_CRYPTO_ARG_RE.finditer(outside_literals)
            }
            raw_hits = [
                hit for hit in hits
                if (normalize_ident(hit[0]) not in protected_idents
                    and normalize_ident(hit[0]) not in inline_protected)
            ]
            if not raw_hits:
                continue

            strongest = "strong" if any(hit[2] == "strong" for hit in raw_hits) else "weak"
            item = raw_hits[0][1]
            label, article, quote = _article7_non_user_finding_fields(item)
            findings.append(Finding(
                rule="K-ENC-003", check="plaintext-sql-write",
                confidence="high" if strongest == "strong" else "medium",
                path=src.path, line=statement.line,
                message=("%s에 저장하는 비이용자 %s 원문 식별자가 SQL INSERT/UPDATE의 값 "
                         "인자로 직접 전달되고 있으며, 그 경로에 암호화 호출이 없습니다."
                         % (zone, label)),
                article=article, quote=quote,
                fix=("AES-GCM 등 안전한 양방향 암호화 결과만 SQL 인자로 전달하거나, 검증된 "
                     "데이터베이스 암호 함수를 쓰기 식에 연결하십시오."),
                evidence=redact(statement.text),
            ))

    return findings


# --------------------------------------------------------------------------- #
# 규칙 K-ENC-005 — 취급자 단말·보조저장매체 저장 암호화 (제7조 제5항)
# --------------------------------------------------------------------------- #

LOCAL_STORAGE_TARGETS = {"workstation", "mobile", "removable_media", "server"}
PROTECTED_LOCAL_STORAGE_TARGETS = {"workstation", "mobile", "removable_media"}
LOCAL_STORAGE_TARGET_LABELS = {
    "workstation": "개인정보취급자의 컴퓨터",
    "mobile": "모바일 기기",
    "removable_media": "보조저장매체",
}


def _article7_device_storage_hits(statement: str, dic: Dictionary, config: dict):
    """제7조 제5항이 정보주체 구분에 따라 요구하는 개인정보 후보를 찾는다."""
    hits = _transmission_pii_hits(statement, dic)
    if config.get("subjectType") != "non_user":
        return hits
    return [
        hit for hit in hits
        if (hit[1].get("category") == "unique_id"
            or hit[1].get("key") == "biometricRecognitionInfo")
    ]


def _file_storage_receivers(src: Source) -> tuple[set[str], set[str]]:
    """명시적으로 파일에 연결된 write 수신자를 종류별로 모은다."""
    streams: set[str] = set()
    files: set[str] = set()
    for statement in src.statements:
        streams.update(
            normalize_ident(match.group(1))
            for match in FILE_STREAM_DECL_RE.finditer(statement.text)
        )
        files.update(
            normalize_ident(match.group(1))
            for match in JAVA_FILE_DECL_RE.finditer(statement.text)
        )
        files.update(
            normalize_ident(match.group(1))
            for match in KOTLIN_FILE_ASSIGN_RE.finditer(statement.text)
        )
    return streams, files


def _file_storage_payloads(
    statement: str,
    stream_receivers: set[str],
    file_receivers: set[str],
) -> list[str]:
    """지원하는 파일 저장 호출에서 실제 저장값 인자만 돌려준다."""
    payloads: list[str] = []
    for match in FILES_WRITE_RE.finditer(statement):
        arguments = _call_arguments_at(statement, match.end() - 1)
        if arguments is not None and len(arguments) >= 2:
            payloads.append(arguments[1])

    for match in FILE_MEMBER_WRITE_RE.finditer(statement):
        receiver = normalize_ident(match.group(1))
        method = match.group(2)
        is_stream_sink = receiver in stream_receivers and method in {"write", "append"}
        is_kotlin_file_sink = (
            receiver in file_receivers
            and method in {"writeText", "writeBytes", "appendText", "appendBytes"}
        )
        if not is_stream_sink and not is_kotlin_file_sink:
            continue
        arguments = _call_arguments_at(statement, match.end() - 1)
        if arguments:
            payloads.append(arguments[0])
    return payloads


def _local_storage_policy(src: Source, method: str) -> tuple[str, str | None]:
    """파일#메서드 저장 위치 계약을 none | invalid | valid와 target으로 정규화한다."""
    policies = src.config.get("localStoragePolicies")
    if policies is None:
        return "none", None
    if not isinstance(policies, list):
        return "invalid", None
    matches = [
        policy for policy in policies
        if (isinstance(policy, dict)
            and _policy_source_matches(src.path, policy.get("source"), method))
    ]
    if not matches:
        return "none", None
    if len(matches) != 1:
        return "invalid", None
    policy = matches[0]
    target = policy.get("target")
    evidence = policy.get("evidence")
    if (target not in LOCAL_STORAGE_TARGETS
            or not isinstance(evidence, str) or not evidence.strip()):
        return "invalid", None
    return "valid", target


def rule_article7_device_storage(src: Source, dic: Dictionary) -> list[Finding]:
    """개인정보가 취급자 단말·보조저장매체의 파일에 암호화 없이 저장되는지 본다."""
    if (FILES_WRITE_RE.search(src.code) is None
            and FILE_MEMBER_WRITE_RE.search(src.code) is None):
        return []

    stream_receivers, file_receivers = _file_storage_receivers(src)
    protected_idents = _local_storage_protected_idents(src, dic)
    encoder_receivers = {
        normalize_ident(match.group(1))
        for match in ONE_WAY_ENCODER_DECL_RE.finditer(src.code)
    }
    scopes = _statement_method_scopes(src)
    findings: list[Finding] = []

    for statement, scope in zip(src.statements, scopes):
        payloads = _file_storage_payloads(
            statement.text, stream_receivers, file_receivers
        )
        if not payloads:
            continue
        method = scope.split("@", 1)[0]
        policy_status, target = _local_storage_policy(src, method)
        if policy_status == "valid" and target == "server":
            continue

        for payload in payloads:
            hits = _article7_device_storage_hits(payload, dic, src.config)
            inline_protected = {
                normalize_ident(match.group(1))
                for match in INLINE_CRYPTO_ARG_RE.finditer(payload)
            }
            inline_protected.update(
                _one_way_protected_hits(payload, dic, encoder_receivers)
            )
            raw_hits = [
                hit for hit in hits
                if (normalize_ident(hit[0]) not in protected_idents
                    and normalize_ident(hit[0]) not in inline_protected)
            ]
            if not raw_hits:
                continue

            strongest = next(
                (hit for hit in raw_hits if hit[2] == "strong"), raw_hits[0]
            )
            _ident, item, strength = strongest
            label = item.get("label", "개인정보")
            if policy_status == "valid" and target in PROTECTED_LOCAL_STORAGE_TARGETS:
                target_label = LOCAL_STORAGE_TARGET_LABELS[target]
                findings.append(Finding(
                    rule="K-ENC-005", check="plaintext-device-storage",
                    confidence="high" if strength == "strong" else "medium",
                    path=src.path, line=statement.line,
                    message=("%s 원문 식별자가 %s의 명시적 파일 저장 호출에 도달하며, "
                             "그 경로에 안전한 암호화가 없습니다." % (label, target_label)),
                    article="개인정보의 안전성 확보조치 기준 제7조 제5항",
                    quote=QUOTE_7_5,
                    fix=("비밀번호는 PasswordEncoder로 일방향 암호화하고, 그 밖의 개인정보는 "
                         "AES-GCM 등 안전한 암호 알고리즘으로 처리한 결과만 파일에 저장하십시오."),
                    evidence=redact(statement.text),
                ))
            else:
                findings.append(Finding(
                    rule="K-ENC-005", check="unverified-device-storage-target",
                    confidence="medium" if strength == "strong" else "low",
                    path=src.path, line=statement.line,
                    message=("%s 원문 식별자가 명시적 파일 저장 호출에 도달하지만, 실행 위치와 "
                             "저장매체를 확인할 완전한 localStoragePolicies 선언이 없습니다."
                             % label),
                    article="개인정보의 안전성 확보조치 기준 제7조 제5항",
                    quote=QUOTE_7_5,
                    fix=(".pipa.json의 localStoragePolicies에 정확한 source, target과 실제 배포·"
                         "운영 근거 evidence를 선언하고, 보호 대상 단말이면 저장 전에 안전한 "
                         "암호 알고리즘을 적용하십시오."),
                    evidence=redact(statement.text),
                ))
    return findings


# --------------------------------------------------------------------------- #
# 규칙 K-ENC-004 — 인터넷망 구간 송·수신 암호화 (제7조 제4항)
# --------------------------------------------------------------------------- #

def _internal_http_host(host: str | None) -> bool:
    """URL 호스트가 코드에서 명시적으로 내부 주소라고 확인되는지 본다."""
    if not host:
        return False
    normalized = host.rstrip(".").lower()
    if (normalized == "localhost"
            or normalized.endswith((".localhost", ".internal", ".local", ".svc",
                                    ".cluster.local"))):
        return True
    if normalized in ("::1", "0:0:0:0:0:0:0:1"):
        return True
    if re.match(r"^(?:fc|fd|fe[89ab])", normalized):
        return True

    parts = normalized.split(".")
    if len(parts) != 4 or not all(part.isdigit() for part in parts):
        return False
    octets = [int(part) for part in parts]
    if any(part > 255 for part in octets):
        return False
    first, second = octets[:2]
    return (
        first in (0, 10, 127)
        or (first == 169 and second == 254)
        or (first == 172 and 16 <= second <= 31)
        or (first == 192 and second == 168)
    )


def _http_url_host(url: str) -> str | None:
    """정규식으로 찾은 HTTP URL에서 호스트만 경량 추출한다."""
    if "://" not in url:
        return None
    authority = re.split(r"[/#?]", url.split("://", 1)[1], maxsplit=1)[0]
    authority = authority.rsplit("@", 1)[-1]
    if authority.startswith("["):
        end = authority.find("]")
        return authority[1:end] if end > 1 else None
    return authority.rsplit(":", 1)[0] if ":" in authority else authority


def _literal_transport_kind(text: str) -> str | None:
    """문자열 리터럴의 URL에서 plain_http | https | internal 을 판정한다."""
    kinds: list[str] = []
    for match in HTTP_URL_LITERAL_RE.finditer(text):
        url = match.group(1)
        scheme = url.split(":", 1)[0].lower()
        host = _http_url_host(url)
        if scheme == "https":
            kinds.append("https")
        elif scheme == "http" and _internal_http_host(host):
            kinds.append("internal")
        elif scheme == "http" and host:
            kinds.append("plain_http")

    # 같은 식에서 여러 후보가 보이면 보호되지 않은 외부 HTTP를 가장 보수적으로 우선한다.
    if "plain_http" in kinds:
        return "plain_http"
    if "https" in kinds:
        return "https"
    if "internal" in kinds:
        return "internal"
    return None


def _http_endpoint_idents(src: Source) -> dict[str, str]:
    """URL 리터럴을 담은 식별자와 단순 재대입을 파일 범위에서 얕게 표시한다."""
    endpoints: dict[str, str] = {}
    for _round in range(PROPAGATION_ROUNDS):
        for statement in src.statements:
            assign = ASSIGN_RE.search(statement.text)
            if not assign:
                continue
            target, rhs = assign.group(1), assign.group(2)
            kind = _literal_transport_kind(rhs)
            if kind is None:
                inherited = {
                    endpoints[normalize_ident(match.group(0))]
                    for match in IDENT_RE.finditer(rhs)
                    if normalize_ident(match.group(0)) in endpoints
                }
                if "plain_http" in inherited:
                    kind = "plain_http"
                elif "https" in inherited:
                    kind = "https"
                elif "internal" in inherited:
                    kind = "internal"
            if kind is not None:
                endpoints[normalize_ident(target)] = kind
    return endpoints


def _statement_transport_kind(statement: str, endpoints: dict[str, str]) -> str | None:
    direct = _literal_transport_kind(statement)
    if direct is not None:
        return direct
    inherited = {
        endpoints[normalize_ident(match.group(0))]
        for match in IDENT_RE.finditer(statement)
        if normalize_ident(match.group(0)) in endpoints
    }
    if "plain_http" in inherited:
        return "plain_http"
    if "https" in inherited:
        return "https"
    if "internal" in inherited:
        return "internal"
    return None


def _transmission_pii_hits(statement: str, dic: Dictionary):
    """HTTP 호출 인자에 드러난 사전 개인정보 후보를 찾는다."""
    outside_literals = STRING_LITERAL_RE.sub(" ", statement)
    idents = []
    for match in IDENT_RE.finditer(outside_literals):
        # builder의 `.passportNumber(encryptedValue)`처럼 인자가 있는 멤버 호출명은 값이
        # 아니다. 반면 `.getPassportNumber()`처럼 인자 없는 getter는 반환값일 수 있어 남긴다.
        before = outside_literals[:match.start()].rstrip()
        after = outside_literals[match.end():]
        if (before.endswith(".")
                and re.match(r"\s*\(", after)
                and not re.match(r"\s*\(\s*\)", after)):
            continue
        idents.append(match.group(0))
    # Kotlin 문자열 템플릿은 리터럴 안에 실제 값 식별자가 있으므로 별도로 되살린다.
    for literal in STRING_LITERAL_RE.finditer(statement):
        idents.extend(match.group(1) for match in KOTLIN_INTERPOLATION_RE.finditer(literal.group(0)))

    hits = []
    seen = set()
    for ident in idents:
        if ident in seen:
            continue
        seen.add(ident)
        item, strength = dic.match(ident)
        if item is not None:
            hits.append((ident, item, strength))
    return hits


def _statement_method_scopes(src: Source) -> list[str]:
    """얕은 전파가 같은 메서드의 흔한 지역 변수명을 넘어 새지 않도록 범위를 표시한다."""
    current = "<file>"
    scopes: list[str] = []
    for statement in src.statements:
        name = _method_name(statement.text)
        if name is not None:
            current = "%s@%d" % (normalize_ident(name), statement.line)
        scopes.append(current)
    return scopes


def _following_method_signature(body: str, start: int) -> str:
    """어노테이션 뒤의 Java/Kotlin 인터페이스 메서드 선언 하나를 잘라낸다."""
    depth = 0
    saw_params = False
    index = start
    while index < len(body):
        ch = body[index]
        if ch == "(":
            depth += 1
            saw_params = True
        elif ch == ")" and depth > 0:
            depth -= 1
        elif saw_params and depth == 0 and ch in ";\n":
            break
        index += 1
    return body[start:index]


def _annotated_interface_methods(
    body: str,
    annotation_re: re.Pattern,
    framework: str,
) -> dict[str, str]:
    """선언형 HTTP 인터페이스의 메서드명과 실행 terminal 종류를 돌려준다.

    반환값은 method -> direct | retrofit_call | reactive 이다. Retrofit의 일반 Call과
    Spring의 reactive 반환값은 프록시 메서드 호출만으로 송신됐다고 단정하지 않는다.
    """
    methods: dict[str, str] = {}
    for annotation in annotation_re.finditer(body):
        signature = _following_method_signature(body, annotation.end())
        clean = " ".join(ANNOTATION_RE.sub(" ", signature).split())
        if not clean or "(" not in clean:
            continue

        kotlin = re.search(
            r"\b(?:(suspend)\s+)?fun\s+([A-Za-z_$][\w$]*)\s*\(", clean
        )
        if kotlin:
            method = kotlin.group(2)
            if framework == "retrofit" and not kotlin.group(1):
                mode = "retrofit_call"
            elif framework == "spring" and re.search(r"\b(?:Mono|Flux|Publisher)\b", clean):
                mode = "reactive"
            else:
                mode = "direct"
            methods[normalize_ident(method)] = mode
            continue

        head = clean.split("(", 1)[0].strip()
        method_match = re.search(r"([A-Za-z_$][\w$]*)\s*$", head)
        if method_match is None:
            continue
        method = method_match.group(1)
        return_type = head[:method_match.start()]
        if framework == "retrofit":
            mode = "retrofit_call"
        elif framework == "spring" and re.search(
            r"\b(?:Mono|Flux|Publisher)\b", return_type
        ):
            mode = "reactive"
        else:
            mode = "direct"
        methods[normalize_ident(method)] = mode
    return methods


def _prefer_transport(current: str | None, candidate: str | None) -> str | None:
    """여러 선언이 한 호출명에 모이면 보호가 약한 쪽을 우선한다."""
    rank = {"plain_http": 3, None: 2, "https": 1, "internal": 0}
    return candidate if rank[candidate] > rank[current] else current


def _declarative_http_sends(
    src: Source,
    endpoints: dict[str, str],
) -> dict[int, str | None]:
    """선언형 클라이언트의 실제 프록시 호출 문장과 전송 구간을 연결한다.

    현재 파일 안에서 인터페이스 선언, 프록시 수신자, 실제 호출이 모두 확인되는 경우만 sink로
    인정한다. Spring HTTP Service와 Retrofit은 createClient/create 연결도 요구한다. Feign은
    @FeignClient 타입으로 선언된 수신자의 호출을 요구한다. 선언만 있는 파일은 결과가 없다.
    """
    spring_types: dict[str, dict[str, str]] = {}
    retrofit_types: dict[str, dict[str, str]] = {}
    feign_types: dict[str, tuple[dict[str, str], str | None]] = {}

    for interface in DECLARATIVE_INTERFACE_RE.finditer(src.code):
        type_name, body = interface.group(1), interface.group(2)
        type_norm = normalize_ident(type_name)

        if "HttpServiceProxyFactory" in src.code:
            methods = _annotated_interface_methods(
                body, SPRING_HTTP_METHOD_ANNOTATION_RE, "spring"
            )
            if methods:
                spring_types[type_norm] = methods

        if re.search(r"\bRetrofit\b", src.code):
            methods = _annotated_interface_methods(
                body, RETROFIT_HTTP_METHOD_ANNOTATION_RE, "retrofit"
            )
            if methods:
                retrofit_types[type_norm] = methods

        before = src.code[max(0, interface.start() - 2000):interface.start()]
        feign = FEIGN_CLIENT_BEFORE_INTERFACE_RE.search(before)
        if feign:
            methods = _annotated_interface_methods(
                body, FEIGN_HTTP_METHOD_ANNOTATION_RE, "feign"
            )
            if methods:
                url = FEIGN_URL_RE.search(feign.group(1))
                kind = _literal_transport_kind(url.group(1)) if url else None
                feign_types[type_norm] = (methods, kind)

    # receiver -> method -> (실행 방식, endpoint 종류)
    receivers: dict[str, dict[str, tuple[str, str | None]]] = {}
    receiver_types: dict[str, set[str]] = {}

    def remember(
        receiver: str,
        client_type: str,
        methods: dict[str, str],
        kind: str | None,
    ) -> None:
        receiver_norm = normalize_ident(receiver)
        receiver_types.setdefault(receiver_norm, set()).add(client_type)
        target = receivers.setdefault(receiver_norm, {})
        for method, mode in methods.items():
            previous = target.get(method)
            if previous is None:
                target[method] = (mode, kind)
            else:
                target[method] = (mode, _prefer_transport(previous[1], kind))

    # Spring/Retrofit은 실제 프록시 생성 대입을 endpoint 얕은 전파와 연결한다.
    for statement in src.statements:
        assign = ASSIGN_RE.search(statement.text)
        if not assign:
            continue
        receiver, rhs = assign.group(1), assign.group(2)
        receiver_kind = _statement_transport_kind(rhs, endpoints)
        for type_norm, methods in spring_types.items():
            if re.search(
                r"\bcreateclient\s*\(\s*" + re.escape(type_norm)
                + r"\s*(?:\.\s*class|::\s*class\s*\.\s*java)\s*\)",
                normalize_ident(rhs),
            ):
                remember(receiver, type_norm, methods, receiver_kind)
        for type_norm, methods in retrofit_types.items():
            if re.search(
                r"\.\s*create\s*\(\s*" + re.escape(type_norm)
                + r"\s*(?:\.\s*class|::\s*class\s*\.\s*java)\s*\)",
                normalize_ident(rhs),
            ):
                remember(receiver, type_norm, methods, receiver_kind)

    # Feign 프록시는 컨테이너가 주입하므로 @FeignClient 타입 선언으로 수신자를 한정한다.
    for type_norm, (methods, kind) in feign_types.items():
        type_pattern = next(
            (match.group(1) for match in DECLARATIVE_INTERFACE_RE.finditer(src.code)
             if normalize_ident(match.group(1)) == type_norm),
            None,
        )
        if type_pattern is None:
            continue
        for match in re.finditer(
            r"\b" + re.escape(type_pattern) + r"\s+([A-Za-z_$][\w$]*)\b",
            src.code,
        ):
            remember(match.group(1), type_norm, methods, kind)
        for match in re.finditer(
            r"\b(?:val|var)\s+([A-Za-z_$][\w$]*)\s*:\s*"
            + re.escape(type_pattern) + r"\b",
            src.code,
        ):
            remember(match.group(1), type_norm, methods, kind)

    # 같은 식별자가 다른 명시적 타입으로 다시 선언되면 지역 변수 shadowing 여부를 이 경량
    # 분석으로 확정할 수 없다. 파일 전체에서 한 수신자로 합쳐 차단하지 않고 후보에서 뺀다.
    for receiver, client_types in receiver_types.items():
        declared_types = {
            normalize_ident(match.group(1))
            for match in re.finditer(
                r"\b([A-Z][A-Za-z0-9_$]*)\s+" + re.escape(receiver) + r"\b",
                src.code,
                re.IGNORECASE,
            )
            if match.group(1)[:1].isupper()
        }
        declared_types.update(
            normalize_ident(match.group(1))
            for match in re.finditer(
                r"\b" + re.escape(receiver) + r"\s*:\s*"
                r"([A-Z][A-Za-z0-9_$]*)\b",
                src.code,
            )
        )
        if declared_types - client_types:
            receivers.pop(receiver, None)

    sends: dict[int, str | None] = {}
    call_args = r"(?:[^()]|\([^()]*\))*"
    for index, statement in enumerate(src.statements):
        for receiver, methods in receivers.items():
            for method, (mode, kind) in methods.items():
                call = re.search(
                    r"\b" + re.escape(receiver) + r"\s*\.\s*" + re.escape(method)
                    + r"\s*\(" + call_args + r"\)",
                    normalize_ident(statement.text),
                )
                if call is None:
                    continue
                terminal = DECLARATIVE_TERMINAL_RE.get(mode)
                if terminal is not None and terminal.search(
                    normalize_ident(statement.text)[call.end():]
                ) is None:
                    continue
                if index in sends:
                    sends[index] = _prefer_transport(sends[index], kind)
                else:
                    sends[index] = kind
    return sends


def _apache_http_client_receivers(src: Source) -> set[str]:
    """Apache HttpClient로 선언된 수신자만 범용 이름 execute()의 HTTP 의미를 인정한다."""
    if not APACHE_HTTP_CONTEXT_RE.search(src.code):
        return set()
    return {
        normalize_ident(match.group(1))
        for match in APACHE_HTTP_CLIENT_DECL_RE.finditer(src.code)
    }


def _jdk_http_client_receivers(src: Source) -> set[str]:
    """JDK HttpClient로 선언된 수신자만 범용 이름 send/sendAsync를 HTTP로 인정한다."""
    if not re.search(r"\bjava\s*\.\s*net\s*\.\s*http\b|\bHttpRequest\b", src.code):
        return set()
    return {
        normalize_ident(match.group(1))
        for match in JDK_HTTP_CLIENT_DECL_RE.finditer(src.code)
    }


def _is_http_send_statement(
    statement: str,
    apache_receivers: set[str],
    jdk_receivers: set[str],
    declarative: bool = False,
) -> bool:
    if declarative:
        return True
    if (HTTP_SEND_CALL_RE.search(statement)
            or HTTP_RETRIEVE_TERMINAL_RE.search(statement)
            or OKHTTP_SEND_CALL_RE.search(statement)):
        return True
    for match in re.finditer(
        r"\b([A-Za-z_$][\w$]*)\s*\.\s*execute\s*\(", statement, re.IGNORECASE
    ):
        if normalize_ident(match.group(1)) in apache_receivers:
            return True
    for match in re.finditer(
        r"\b([A-Za-z_$][\w$]*)\s*\.\s*send(?:Async)?\s*\(", statement,
        re.IGNORECASE,
    ):
        if normalize_ident(match.group(1)) in jdk_receivers:
            return True
    return False


def _unprotected_transmission_hits(
    statement: str,
    dic: Dictionary,
    protected_idents: set[str],
):
    hits = _transmission_pii_hits(statement, dic)
    inline_protected = {
        normalize_ident(match.group(1))
        for match in INLINE_CRYPTO_ARG_RE.finditer(statement)
    }
    return [
        hit for hit in hits
        if (normalize_ident(hit[0]) not in protected_idents
            and normalize_ident(hit[0]) not in inline_protected)
    ], inline_protected


def _request_value_taints(
    src: Source,
    dic: Dictionary,
    protected_idents: set[str],
    scopes: list[str],
) -> dict[tuple[str, str], tuple[dict, str, int]]:
    """원문 개인정보가 들어간 요청 DTO·래퍼 지역 변수를 같은 메서드 안에서 얕게 표시한다."""
    taints: dict[tuple[str, str], tuple[dict, str, int]] = {}

    def remember(key: tuple[str, str], candidates: list[tuple[dict, str, int]]) -> None:
        if not candidates:
            return
        strongest = next((candidate for candidate in candidates if candidate[1] == "strong"),
                         candidates[0])
        previous = taints.get(key)
        if previous is None or (previous[1] != "strong" and strongest[1] == "strong"):
            taints[key] = strongest

    for _round in range(PROPAGATION_ROUNDS):
        for statement, scope in zip(src.statements, scopes):
            raw_hits, inline_protected = _unprotected_transmission_hits(
                statement.text, dic, protected_idents
            )
            direct = [(item, strength, statement.line) for _ident, item, strength in raw_hits]

            assign = ASSIGN_RE.search(statement.text)
            if assign:
                target, rhs = assign.group(1), assign.group(2)
                inherited = [
                    taints[(scope, normalize_ident(match.group(0)))]
                    for match in IDENT_RE.finditer(rhs)
                    if ((scope, normalize_ident(match.group(0))) in taints
                        and normalize_ident(match.group(0)) not in inline_protected)
                ]
                remember((scope, normalize_ident(target)), direct + inherited)

            mutator = DTO_MUTATOR_RE.search(statement.text)
            if mutator and direct:
                remember((scope, normalize_ident(mutator.group(1))), direct)

    return taints


def _server_request_dto_items(src: Source, dic: Dictionary) -> dict[str, tuple[dict, str]]:
    """같은 파일의 Java record/class·Kotlin data class 요청 DTO에서 개인정보 항목을 찾는다."""
    dto_items: dict[str, tuple[dict, str]] = {}
    current_type: str | None = None
    for statement in src.statements:
        declaration = SERVER_DTO_DECL_RE.search(statement.text)
        if declaration is not None:
            current_type = normalize_ident(declaration.group(1))
        hits = _transmission_pii_hits(statement.text, dic)
        if current_type is None or not hits:
            continue
        strongest = next((hit for hit in hits if hit[2] == "strong"), hits[0])
        previous = dto_items.get(current_type)
        if previous is None or (previous[1] != "strong" and strongest[2] == "strong"):
            dto_items[current_type] = (strongest[1], strongest[2])
    return dto_items


def _inbound_transport_kind(config: dict) -> str | None:
    """명시적 수신 경계 계약을 secure | internal | plain 으로 정규화한다.

    보호를 끄는 선언도, 보호됐다고 보는 선언도 근거 문자열을 요구한다. 필드 누락·오타·서로
    모순되는 조합은 None으로 남겨 서버 수신 endpoint에서 경고하게 한다.
    """
    inbound = config.get("inboundTransport")
    if not isinstance(inbound, dict):
        return None
    exposure = inbound.get("exposure")
    termination = inbound.get("tlsTermination")
    https_only = inbound.get("httpsOnly")
    evidence = inbound.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        return None
    if exposure == "internal":
        return "internal"
    if exposure != "internet":
        return None
    if termination in {"application", "trusted_proxy"} and https_only is True:
        return "secure"
    if termination == "none" and https_only is False:
        return "plain"
    return None


def rule_article7_server_receive(src: Source, dic: Dictionary) -> list[Finding]:
    """Spring endpoint가 개인정보 요청값을 받는 인터넷망 구간의 TLS 계약을 확인한다."""
    if not SERVER_CONTROLLER_CONTEXT_RE.search(src.code):
        return []

    dto_items = _server_request_dto_items(src, dic)
    transport = _inbound_transport_kind(src.config)
    findings: list[Finding] = []

    for statement in src.statements:
        if (SERVER_MAPPING_RE.search(statement.text) is None
                or SERVER_REQUEST_BINDING_RE.search(statement.text) is None):
            continue

        hits = _transmission_pii_hits(statement.text, dic)
        candidates = [(item, strength) for _ident, item, strength in hits]
        for match in IDENT_RE.finditer(STRING_LITERAL_RE.sub(" ", statement.text)):
            candidate = dto_items.get(normalize_ident(match.group(0)))
            if candidate is not None:
                candidates.append(candidate)
        if not candidates or transport in {"secure", "internal"}:
            continue

        item, strength = next(
            (candidate for candidate in candidates if candidate[1] == "strong"),
            candidates[0],
        )
        label = item.get("label", "개인정보")
        if transport == "plain":
            findings.append(Finding(
                rule="K-ENC-004", check="plaintext-server-receive",
                confidence="high" if strength == "strong" else "medium",
                path=src.path, line=statement.line,
                message=("%s 요청값을 받는 서버 endpoint가 외부 인터넷망에서 TLS 종단 없이 "
                         "평문 수신하도록 선언되어 있습니다." % label),
                article="개인정보의 안전성 확보조치 기준 제7조 제4항",
                quote=QUOTE_7_4,
                fix=("애플리케이션 서버에 HTTPS 전용 TLS를 설정하거나 신뢰하는 경계 프록시에서 "
                     "TLS를 종단하고, inboundTransport에 실제 배포 근거를 기록하십시오."),
                evidence=redact(statement.text),
            ))
        else:
            findings.append(Finding(
                rule="K-ENC-004", check="unverified-server-receive-tls",
                confidence="medium" if strength == "strong" else "low",
                path=src.path, line=statement.line,
                message=("%s 요청값을 받는 서버 endpoint가 있지만 외부 노출 여부와 TLS 종단을 "
                         "확인할 inboundTransport 근거가 없거나 불완전합니다." % label),
                article="개인정보의 안전성 확보조치 기준 제7조 제4항",
                quote=QUOTE_7_4,
                fix=(".pipa.json의 inboundTransport에 exposure, tlsTermination, httpsOnly와 "
                     "배포 설정 evidence를 함께 선언하십시오."),
                evidence=redact(statement.text),
            ))

    return findings


def _output_dto_items(
    src: Source,
    dic: Dictionary,
) -> dict[str, dict[str, tuple[dict, str]]]:
    """같은 파일의 DTO 타입별 개인정보 항목을 모은다.

    모든 class/record/data class 선언에서 현재 타입을 다시 설정하므로 앞 DTO의 항목이 뒤 타입으로
    새지 않는다. 응답 메서드가 실제 반환형으로 참조한 타입만 출력 후보로 사용한다.
    """
    result: dict[str, dict[str, tuple[dict, str]]] = {}
    current_type: str | None = None
    for statement in src.statements:
        declaration = SERVER_DTO_DECL_RE.search(statement.text)
        if declaration is not None:
            current_type = normalize_ident(declaration.group(1))
            result.setdefault(current_type, {})
        if current_type is None:
            continue
        for _ident, item, strength in _transmission_pii_hits(statement.text, dic):
            key = item.get("key")
            if not key:
                continue
            previous = result[current_type].get(key)
            if previous is None or (previous[1] != "strong" and strength == "strong"):
                result[current_type][key] = (item, strength)
    return result


def _output_policy_allowed_items(
    src: Source,
    dic: Dictionary,
    sink: str,
    method: str,
) -> set[str] | None:
    """현재 파일#메서드에 대응하는 완전한 출력 정책의 허용 항목을 돌려준다.

    source는 프로젝트 상대 경로의 접미사와 메서드명을 `path/File.java#method`로 연결한다.
    와일드카드·상위 경로·중복 정책은 넓은 허용으로 악용될 수 있어 인정하지 않는다.
    """
    policies = src.config.get("outputPolicies")
    if not isinstance(policies, list):
        return None

    source_path = src.path.replace("\\", "/")
    method_norm = normalize_ident(method)
    matches: list[dict] = []
    for policy in policies:
        if not isinstance(policy, dict) or policy.get("sink") != sink:
            continue
        selector = policy.get("source")
        if _policy_source_matches(source_path, selector, method_norm):
            matches.append(policy)

    if len(matches) != 1:
        return None
    policy = matches[0]
    purpose = policy.get("purpose")
    evidence = policy.get("evidence")
    allowed = policy.get("allowedItems")
    if (not isinstance(purpose, str) or not purpose.strip()
            or not isinstance(evidence, str) or not evidence.strip()
            or not isinstance(allowed, list)
            or any(not isinstance(key, str) for key in allowed)
            or len(allowed) != len(set(allowed))):
        return None

    known = {item.get("key") for item in dic.raw.get("items", [])}
    if any(key not in known for key in allowed):
        return None
    return set(allowed)


def _policy_source_matches(source_path: str, selector, method: str) -> bool:
    """와일드카드 없이 정확한 프로젝트 상대 파일 접미사와 메서드를 연결한다."""
    if not isinstance(selector, str) or selector.count("#") != 1:
        return False
    file_part, selected_method = selector.rsplit("#", 1)
    file_part = file_part.replace("\\", "/").lstrip("./")
    if (not file_part or not selected_method or ".." in file_part.split("/")
            or "*" in file_part or "?" in file_part):
        return False
    normalized_path = source_path.replace("\\", "/")
    path_matches = normalized_path == file_part or normalized_path.endswith("/" + file_part)
    return path_matches and normalize_ident(selected_method) == normalize_ident(method)


def _response_dto_types(
    statement: str,
    method: str,
    dto_items: dict[str, dict[str, tuple[dict, str]]],
) -> set[str]:
    """Spring 매핑 메서드 선언에서 요청 인자를 제외한 반환 DTO 타입만 고른다."""
    clean = " ".join(ANNOTATION_RE.sub(" ", statement).split())
    segment = ""
    if re.search(r"\bfun\s+%s\s*\(" % re.escape(method), clean):
        # Kotlin은 매개변수 닫힘 뒤 `: 반환형`에 반환 타입이 있다.
        match = re.search(r"\)\s*:\s*([^={]+)", clean)
        if match:
            segment = match.group(1)
    else:
        match = re.search(r"\b%s\s*\(" % re.escape(method), clean)
        if match:
            # Java는 메서드명 앞에 반환 타입이 있고 매개변수 타입은 뒤에 있다.
            segment = clean[:match.start()]
    return {
        normalize_ident(token.group(0))
        for token in IDENT_RE.finditer(segment)
        if normalize_ident(token.group(0)) in dto_items
    }


def _remember_output_item(
    target: dict[str, tuple[dict, str, int, str]],
    item: dict,
    strength: str,
    line: int,
    evidence: str,
) -> None:
    key = item.get("key")
    if not key:
        return
    previous = target.get(key)
    if previous is None or (previous[1] != "strong" and strength == "strong"):
        target[key] = (item, strength, line, evidence)


def _output_finding(
    src: Source,
    dic: Dictionary,
    sink: str,
    method: str,
    items: dict[str, tuple[dict, str, int, str]],
) -> Finding | None:
    """정책 초과는 high, 목적·허용 범위 미확인은 medium으로 라우팅한다."""
    if not items:
        return None
    allowed = _output_policy_allowed_items(src, dic, sink, method)
    if allowed is None:
        selected = list(items.values())
        strongest = next((value for value in selected if value[1] == "strong"), selected[0])
        item, strength, line, evidence = strongest
        common = {
            "confidence": "medium" if strength == "strong" else "low",
            "path": src.path,
            "line": line,
            "article": "개인정보의 안전성 확보조치 기준 제12조 제1항",
            "quote": QUOTE_12_1,
            "fix": (".pipa.json의 outputPolicies에 sink, source(상대 파일#메서드), purpose, "
                    "allowedItems와 evidence를 모두 선언하십시오."),
            "evidence": redact(evidence),
        }
        label = item.get("label", "개인정보")
        if sink == "api":
            return Finding(
                rule="K-LEAK-002", check="unverified-api-output-purpose",
                message=("API 응답에 %s 항목이 출력되지만 용도와 허용 항목을 확인할 완전한 "
                         "outputPolicies 근거가 없습니다." % label),
                **common,
            )
        return Finding(
            rule="K-LEAK-001", check="unverified-log-output-purpose",
            message=("로그에 %s 항목이 출력되지만 용도와 허용 항목을 확인할 완전한 "
                     "outputPolicies 근거가 없습니다." % label),
            **common,
        )

    excessive = [value for key, value in items.items() if key not in allowed]
    if not excessive:
        return None
    strongest = next((value for value in excessive if value[1] == "strong"), excessive[0])
    labels = sorted({value[0].get("label", "개인정보") for value in excessive})
    _item, strength, line, evidence = strongest
    common = {
        "confidence": "high" if strength == "strong" else "medium",
        "path": src.path,
        "line": line,
        "article": "개인정보의 안전성 확보조치 기준 제12조 제1항",
        "quote": QUOTE_12_1,
        "fix": ("출력 용도에 불필요한 항목을 응답 DTO 또는 로그 인자에서 제거하십시오. 업무상 "
                "필요하다면 근거 문서를 검토한 뒤 outputPolicies의 allowedItems를 갱신하십시오."),
        "evidence": redact(evidence),
    }
    if sink == "api":
        return Finding(
            rule="K-LEAK-002", check="excessive-api-response",
            message=("API 응답의 출력 정책이 허용하지 않은 개인정보 항목(%s)이 출력됩니다."
                     % ", ".join(labels)),
            **common,
        )
    return Finding(
        rule="K-LEAK-001", check="excessive-log-output",
        message=("로그의 출력 정책이 허용하지 않은 개인정보 항목(%s)이 출력됩니다."
                 % ", ".join(labels)),
        **common,
    )


def rule_article12_api_output(src: Source, dic: Dictionary) -> list[Finding]:
    """Spring API 응답의 개인정보 항목이 명시한 출력 용도 범위를 넘는지 본다."""
    if not SERVER_CONTROLLER_CONTEXT_RE.search(src.code):
        return []

    dto_items = _output_dto_items(src, dic)
    scopes = _statement_method_scopes(src)
    endpoints: dict[str, tuple[str, int]] = {}
    outputs: dict[str, dict[str, tuple[dict, str, int, str]]] = {}
    typed_locals: dict[tuple[str, str], str] = {}

    for statement, scope in zip(src.statements, scopes):
        if SERVER_MAPPING_RE.search(statement.text):
            method = _method_name(statement.text)
            if method is not None:
                endpoints[scope] = (method, statement.line)
                bucket = outputs.setdefault(scope, {})
                for dto_type in _response_dto_types(statement.text, method, dto_items):
                    for item, strength in dto_items[dto_type].values():
                        _remember_output_item(bucket, item, strength, statement.line, statement.text)
                # Kotlin expression body는 매핑 선언과 반환식이 같은 문장이다.
                if "=" in statement.text:
                    rhs = statement.text.split("=", 1)[1]
                    for _ident, item, strength in _transmission_pii_hits(rhs, dic):
                        _remember_output_item(bucket, item, strength, statement.line, statement.text)

        if scope not in endpoints:
            continue
        for dto_type in dto_items:
            match = re.search(
                r"\b%s\b\s+([A-Za-z_$][\w$]*)\b" % re.escape(dto_type),
                normalize_ident(statement.text),
            )
            if match:
                typed_locals[(scope, normalize_ident(match.group(1)))] = dto_type

        returned = RETURN_RE.match(statement.text)
        if returned is None:
            continue
        bucket = outputs.setdefault(scope, {})
        expression = returned.group(1)
        for _ident, item, strength in _transmission_pii_hits(expression, dic):
            _remember_output_item(bucket, item, strength, statement.line, statement.text)
        for token in IDENT_RE.finditer(expression):
            norm = normalize_ident(token.group(0))
            dto_type = norm if norm in dto_items else typed_locals.get((scope, norm))
            if dto_type is None:
                continue
            for item, strength in dto_items[dto_type].values():
                _remember_output_item(bucket, item, strength, statement.line, statement.text)

    findings: list[Finding] = []
    for scope, (method, _line) in endpoints.items():
        finding = _output_finding(
            src, dic, "api", method, outputs.get(scope, {}),
        )
        if finding is not None:
            findings.append(finding)
    return findings


def _logger_receivers(src: Source) -> set[str]:
    receivers: set[str] = {"log"} if LOMBOK_LOG_RE.search(src.code) else set()
    for statement in src.statements:
        for match in LOGGER_DECL_RE.finditer(statement.text):
            receiver = match.group(1) or match.group(2)
            if receiver:
                receivers.add(normalize_ident(receiver))
    return receivers


def rule_article12_log_output(src: Source, dic: Dictionary) -> list[Finding]:
    """선언된 logger 호출의 개인정보 항목이 명시한 로그 용도 범위를 넘는지 본다."""
    receivers = _logger_receivers(src)
    if not receivers:
        return []
    scopes = _statement_method_scopes(src)
    outputs: dict[str, dict[str, tuple[dict, str, int, str]]] = {}
    methods: dict[str, str] = {}
    for statement, scope in zip(src.statements, scopes):
        call = LOG_CALL_RE.search(statement.text)
        if call is None or normalize_ident(call.group(1)) not in receivers:
            continue
        hits = _transmission_pii_hits(statement.text[call.end():], dic)
        if not hits:
            continue
        method = scope.split("@", 1)[0]
        if method == "<file>":
            continue
        methods[scope] = method
        bucket = outputs.setdefault(scope, {})
        for _ident, item, strength in hits:
            _remember_output_item(bucket, item, strength, statement.line, statement.text)

    findings: list[Finding] = []
    for scope, method in methods.items():
        finding = _output_finding(
            src, dic, "log", method, outputs.get(scope, {}),
        )
        if finding is not None:
            findings.append(finding)
    return findings


ACCESS_LOG_COMPONENTS = (
    "actorId",
    "accessedAt",
    "sourceInfo",
    "dataSubjectInfo",
    "action",
)
ACCESS_LOG_COMPONENT_LABELS = {
    "actorId": "식별자",
    "accessedAt": "접속일시",
    "sourceInfo": "접속지 정보",
    "dataSubjectInfo": "처리한 정보주체 정보",
    "action": "수행업무",
}
ACCESS_LOG_EXTERNAL = {
    "actorId": {"security_context", "mdc"},
    "accessedAt": {"logger_timestamp", "mdc"},
    "sourceInfo": {"request_context", "request_mdc", "mdc"},
    "dataSubjectInfo": {"request_context", "request_mdc", "mdc"},
    "action": {"framework_event", "request_context", "mdc"},
}


def _access_log_policy(
    src: Source,
    method: str,
) -> tuple[str, dict[str, str]]:
    """접속기록 정책 상태와 코드에서 직접 확인할 구성요소 식별자를 돌려준다.

    반환 상태는 none / invalid / valid다. external 구성요소는 설정 근거가 공급하므로 반환하는
    식별자 목록에서 제외한다.
    """
    policies = src.config.get("accessLogPolicies")
    if not isinstance(policies, list):
        return "none", {}
    matches = [
        policy for policy in policies
        if isinstance(policy, dict)
        and _policy_source_matches(src.path, policy.get("source"), method)
    ]
    if not matches:
        return "none", {}
    if len(matches) != 1:
        return "invalid", {}

    policy = matches[0]
    evidence = policy.get("evidence")
    components = policy.get("components")
    if (not isinstance(evidence, str) or not evidence.strip()
            or not isinstance(components, dict)
            or set(components) != set(ACCESS_LOG_COMPONENTS)):
        return "invalid", {}

    arguments: dict[str, str] = {}
    used_arguments: set[str] = set()
    for component in ACCESS_LOG_COMPONENTS:
        spec = components.get(component)
        if not isinstance(spec, dict) or len(spec) != 1:
            return "invalid", {}
        if "argument" in spec:
            argument = spec.get("argument")
            if not isinstance(argument, str) or IDENT_RE.fullmatch(argument) is None:
                return "invalid", {}
            normalized = normalize_ident(argument)
            if normalized in used_arguments:
                return "invalid", {}
            used_arguments.add(normalized)
            arguments[component] = normalized
            continue
        if "external" in spec:
            provider = spec.get("external")
            if provider not in ACCESS_LOG_EXTERNAL[component]:
                return "invalid", {}
            continue
        return "invalid", {}
    return "valid", arguments


def _access_log_argument_idents(statement: str, call_end: int) -> set[str]:
    """logger 호출의 포맷 문자열을 제외한 직접 값 식별자를 모은다."""
    arguments = statement[call_end:]
    outside_literals = STRING_LITERAL_RE.sub(" ", arguments)
    idents = {
        normalize_ident(match.group(0))
        for match in IDENT_RE.finditer(outside_literals)
    }
    for literal in STRING_LITERAL_RE.finditer(arguments):
        idents.update(
            normalize_ident(match.group(1))
            for match in KOTLIN_INTERPOLATION_RE.finditer(literal.group(0))
        )
    return idents


def rule_article8_access_log(src: Source, dic: Dictionary) -> list[Finding]:
    """명시한 접속기록 logger 호출에 제2조 제3호의 구성요소가 있는지 본다."""
    del dic  # 이 규칙은 개인정보 항목 사전이 아니라 명시적 접속기록 계약을 사용한다.
    policies = src.config.get("accessLogPolicies")
    if not policies:
        return []
    receivers = _logger_receivers(src)
    if not receivers:
        return []

    scopes = _statement_method_scopes(src)
    calls: dict[str, list[tuple[Statement, set[str]]]] = {}
    methods: dict[str, str] = {}
    for statement, scope in zip(src.statements, scopes):
        call = LOG_CALL_RE.search(statement.text)
        if call is None or normalize_ident(call.group(1)) not in receivers:
            continue
        method = scope.split("@", 1)[0]
        if method == "<file>":
            continue
        methods[scope] = method
        calls.setdefault(scope, []).append(
            (statement, _access_log_argument_idents(statement.text, call.end()))
        )

    findings: list[Finding] = []
    for scope, method in methods.items():
        status, required_arguments = _access_log_policy(src, method)
        if status == "none":
            continue
        statement_calls = calls[scope]
        if status == "invalid":
            statement, _idents = statement_calls[0]
            findings.append(Finding(
                rule="K-LOG-001", check="unverified-access-log-components",
                confidence="medium", path=src.path, line=statement.line,
                message=("접속기록 logger 호출이 지정되어 있지만 다섯 구성요소의 공급 방식과 "
                         "근거를 확인할 완전한 accessLogPolicies 선언이 없습니다."),
                article="개인정보의 안전성 확보조치 기준 제8조 제1항 및 제2조 제3호",
                quote=QUOTE_2_3 + "\n" + QUOTE_8_1,
                fix=(".pipa.json의 accessLogPolicies에 source, evidence와 actorId, accessedAt, "
                     "sourceInfo, dataSubjectInfo, action의 argument 또는 허용된 external 공급자를 "
                     "모두 선언하십시오."),
                evidence=redact(statement.text),
            ))
            continue

        candidates: list[tuple[list[str], Statement]] = []
        for statement, idents in statement_calls:
            missing = [
                component for component, argument in required_arguments.items()
                if argument not in idents
            ]
            if not missing:
                candidates = []
                break
            candidates.append((missing, statement))
        if not candidates:
            continue
        missing, statement = min(candidates, key=lambda candidate: len(candidate[0]))
        labels = [ACCESS_LOG_COMPONENT_LABELS[component] for component in missing]
        findings.append(Finding(
            rule="K-LOG-001", check="missing-access-log-component",
            confidence="high", path=src.path, line=statement.line,
            message=("접속기록 logger 호출에 정책이 직접 인자로 지정한 구성요소(%s)가 없습니다."
                     % ", ".join(labels)),
            article="개인정보의 안전성 확보조치 기준 제8조 제1항 및 제2조 제3호",
            quote=QUOTE_2_3 + "\n" + QUOTE_8_1,
            fix=("누락된 구성요소를 같은 접속기록 호출의 직접 인자로 추가하십시오. logger·MDC·"
                 "보안 컨텍스트가 공급한다면 실제 설정 근거를 확인하고 해당 구성요소를 external로 "
                 "선언하십시오."),
            evidence=redact(statement.text),
        ))
    return findings


def rule_article7_internet_transmission(src: Source, dic: Dictionary) -> list[Finding]:
    """HTTP 클라이언트로 개인정보 원문을 보호되지 않은 인터넷망 구간에 보내는지 찾는다."""
    if not HTTP_CLIENT_CONTEXT_RE.search(src.code):
        return []

    apache_receivers = _apache_http_client_receivers(src)
    jdk_receivers = _jdk_http_client_receivers(src)
    endpoints = _http_endpoint_idents(src)
    declarative_sends = _declarative_http_sends(src, endpoints)
    if not any(
        _is_http_send_statement(
            statement.text, apache_receivers, jdk_receivers,
            index in declarative_sends
        )
        for index, statement in enumerate(src.statements)
    ):
        return []

    protected_idents = _protected_value_idents(src, dic)
    scopes = _statement_method_scopes(src)
    request_taints = _request_value_taints(src, dic, protected_idents, scopes)
    tls_disabled_label, _ = _first(TLS_VERIFICATION_DISABLED, src.code)
    findings: list[Finding] = []

    for index, (statement, scope) in enumerate(zip(src.statements, scopes)):
        if not _is_http_send_statement(
            statement.text, apache_receivers, jdk_receivers,
            index in declarative_sends
        ):
            continue

        raw_hits, _inline_protected = _unprotected_transmission_hits(
            statement.text, dic, protected_idents
        )
        seen = {normalize_ident(hit[0]) for hit in raw_hits}
        for match in IDENT_RE.finditer(STRING_LITERAL_RE.sub(" ", statement.text)):
            norm = normalize_ident(match.group(0))
            taint = request_taints.get((scope, norm))
            if taint is None or norm in seen:
                continue
            item, strength, _origin_line = taint
            raw_hits.append((match.group(0), item, strength))
            seen.add(norm)
        if not raw_hits:
            continue

        transport = _statement_transport_kind(statement.text, endpoints)
        if transport is None and index in declarative_sends:
            transport = declarative_sends[index]
        if transport == "internal":
            continue

        strongest = "strong" if any(hit[2] == "strong" for hit in raw_hits) else "weak"
        item = raw_hits[0][1]
        label = item.get("label", "개인정보")

        if transport == "https" and tls_disabled_label:
            findings.append(Finding(
                rule="K-ENC-004", check="tls-verification-disabled",
                confidence="medium" if strongest == "strong" else "low",
                path=src.path, line=statement.line,
                message=("%s 원문 식별자를 HTTPS로 전송하지만 같은 파일에 TLS 인증서 또는 "
                         "호스트명 검증을 무력화하는 신호(%s)가 있습니다. 해당 설정이 이 "
                         "클라이언트 인스턴스에 연결됐는지 확인해야 합니다."
                         % (label, tls_disabled_label)),
                article="개인정보의 안전성 확보조치 기준 제7조 제4항",
                quote=QUOTE_7_4,
                fix=("기본 인증서 체인과 호스트명 검증을 복원하고, 운영 코드에서 TrustAll·"
                     "NoopHostnameVerifier 계열 설정을 제거하십시오."),
                evidence=redact(statement.text),
            ))
        elif transport == "https":
            continue
        elif transport == "plain_http":
            findings.append(Finding(
                rule="K-ENC-004", check="plaintext-http-transmission",
                confidence="high" if strongest == "strong" else "medium",
                path=src.path, line=statement.line,
                message=("%s 원문 식별자가 외부의 명시적 http:// 클라이언트 호출에 "
                         "도달하고 있어 인터넷망 전송 구간이 암호화되지 않습니다." % label),
                article="개인정보의 안전성 확보조치 기준 제7조 제4항",
                quote=QUOTE_7_4,
                fix=("인증서를 검증하는 HTTPS endpoint로 전환하거나, 전송 전에 안전한 암호 "
                     "알고리즘으로 처리한 payload만 전달하십시오."),
                evidence=redact(statement.text),
            ))
        else:
            findings.append(Finding(
                rule="K-ENC-004", check="unverified-network-transmission",
                confidence="medium" if strongest == "strong" else "low",
                path=src.path, line=statement.line,
                message=("%s 원문 식별자가 HTTP 클라이언트 호출에 도달하지만 endpoint의 "
                         "스킴을 이 파일에서 확인할 수 없습니다. 인터넷망 구간이라면 안전한 "
                         "암호 알고리즘으로 보호해야 합니다." % label),
                article="개인정보의 안전성 확보조치 기준 제7조 제4항",
                quote=QUOTE_7_4,
                fix=("endpoint가 인증서를 검증하는 HTTPS임을 설정과 코드에서 확인하거나, "
                     "전송 전에 안전한 암호 알고리즘으로 처리한 payload만 전달하십시오."),
                evidence=redact(statement.text),
            ))

    return findings


def rule_password_one_way(src: Source, dic: Dictionary) -> list[Finding]:
    findings: list[Finding] = []
    file_has_safe = _any(SAFE_ONE_WAY, src.code)
    config_idents = _config_credential_idents(src, dic)
    receivers = _crypto_receivers(src)
    strong_hash_stmts: list[tuple[Statement, str]] = []

    for st in src.statements:
        hits = _auth_hits(st.text, dic)
        if not hits:
            continue

        # 시스템 계정 크리덴셜은 제2조 제8호의 "비밀번호"가 아니므로 대상이 아니다.
        # 문장 안의 인증정보 식별자가 모두 설정 유래일 때만 건너뛴다.
        if _any(CONFIG_CREDENTIAL, st.text):
            continue
        if all(normalize_ident(h[0]) in config_idents for h in hits):
            continue

        strongest = "strong" if any(h[2] == "strong" for h in hits) else "weak"
        item = hits[0][1]
        label = item.get("label", "인증정보")
        evidence = redact(st.text)

        stmt_safe = _any(SAFE_ONE_WAY, st.text)

        crypto_label, _ = _first(TWO_WAY_CRYPTO, st.text)
        hash_label, _ = _first(WEAK_HASH, st.text)
        strong_in_stmt = _any(STRONG_HASH, st.text)

        # 알고리즘이 이 문장에 없으면 앞에서 표시해 둔 변수를 통해 전파를 확인한다.
        prop_kind, prop_label, prop_line = (None, None, 0)
        if not crypto_label and not hash_label and not strong_in_stmt:
            prop_kind, prop_label, prop_line = _receiver_hit(st.text, receivers)
            if prop_kind == "two_way":
                crypto_label = prop_label
            elif prop_kind == "weak_hash":
                hash_label = prop_label
            elif prop_kind == "strong_hash":
                strong_in_stmt = True
        origin = (" 알고리즘은 %d행에서 결정됩니다." % prop_line) if prop_kind else ""

        # (A) 양방향 암호 알고리즘 적용
        if crypto_label and not stmt_safe:
            findings.append(Finding(
                rule="K-ENC-002", check="two-way",
                confidence="high" if strongest == "strong" else "medium",
                path=src.path, line=st.line,
                message="%s를 양방향 암호 알고리즘(%s)으로 처리하고 있습니다. "
                        "복호화가 가능한 방식으로 저장하면 제7조 제1항 단서를 위반합니다.%s"
                        % (label, crypto_label, origin),
                article=ART_7_1 + " 단서", quote=QUOTE_7_1,
                fix=FIX_ONE_WAY, evidence=evidence,
            ))
            continue

        # (B) 취약 해시 알고리즘
        if hash_label:
            findings.append(Finding(
                rule="K-ENC-002", check="weak-hash",
                confidence="high" if strongest == "strong" else "medium",
                path=src.path, line=st.line,
                message="%s를 취약한 해시 알고리즘(%s)으로 처리하고 있습니다. "
                        "일방향이더라도 '안전한 암호 알고리즘'에 해당하지 않습니다.%s"
                        % (label, hash_label, origin),
                article=ART_7_1 + " 단서", quote=QUOTE_7_1,
                fix=FIX_ONE_WAY, evidence=evidence,
            ))
            continue

        # (C) @Convert 로 양방향 컨버터를 연결
        conv = CONVERT_RE.search(st.text)
        if conv:
            arg = conv.group(1)
            if CRYPTO_WORD_RE.search(arg) and not ONEWAY_WORD_RE.search(arg):
                findings.append(Finding(
                    rule="K-ENC-002", check="two-way-converter",
                    confidence="high" if strongest == "strong" else "medium",
                    path=src.path, line=st.line,
                    message="%s 필드에 양방향 암호화 컨버터(@Convert%s)를 연결했습니다. "
                            "컨버터는 복호화를 전제하므로 제7조 제1항 단서를 위반합니다."
                            % (label, "(" + " ".join(arg.split()) + ")"),
                    article=ART_7_1 + " 단서", quote=QUOTE_7_1,
                    fix=FIX_ONE_WAY, evidence=evidence,
                ))
                continue

        # (D) Base64 인코딩을 암호화로 사용
        b64_label, _ = _first(BASE64_ENCODE, st.text)
        if b64_label and not stmt_safe and not strong_in_stmt:
            findings.append(Finding(
                rule="K-ENC-002", check="encoding-not-encryption",
                confidence="high" if strongest == "strong" else "medium",
                path=src.path, line=st.line,
                message="%s를 Base64로 인코딩하고 있습니다. Base64는 누구나 원문으로 되돌릴 수 "
                        "있는 인코딩이며 암호화가 아닙니다." % label,
                article=ART_7_1 + " 단서", quote=QUOTE_7_1,
                fix=FIX_ONE_WAY, evidence=evidence,
            ))
            continue

        # (E) 안전한 해시를 쓰지만 salt/반복이 보이지 않음 — 파일 단위로 판정한다.
        if strong_in_stmt and not stmt_safe:
            strong_hash_stmts.append((st, label))

        # (F) 평문 비교로 보이는 인증 — 확인 입력 비교와 구분이 불가능하므로 경고만 한다.
        if (EQUALS_RE.search(st.text)
                and not file_has_safe
                and not _any(CONFIRM_HINT, st.text)):
            findings.append(Finding(
                rule="K-ENC-002", check="plaintext-compare",
                confidence="medium",
                path=src.path, line=st.line,
                message="%s를 equals()로 직접 비교하고 있습니다. 저장값과 입력값을 비교하는 "
                        "인증이라면 저장값이 평문이라는 뜻이므로 제7조 제1항 단서 위반입니다. "
                        "비밀번호 확인 입력 검증이라면 해당하지 않습니다." % label,
                article=ART_7_1 + " 단서", quote=QUOTE_7_1,
                fix="인증이라면 passwordEncoder.matches(raw, encoded)로 대체하십시오. "
                    "확인 입력 검증이라면 변수명에 confirm 등을 사용해 의도를 드러내십시오.",
                evidence=evidence,
            ))

    # (E) 마무리 — 파일 어디에도 salt/반복 신호가 없을 때만 보고한다.
    if strong_hash_stmts and not _any(
        [r"[Ss]alt", r"[Ii]teration", r"\bPBKDF2|\bPbkdf2", r"\bBCrypt\b",
         r"\bArgon2\b", r"\bSCrypt\b", r"\bHmac"], src.code
    ):
        st, label = strong_hash_stmts[0]
        findings.append(Finding(
            rule="K-ENC-002", check="unsalted-hash",
            confidence="medium",
            path=src.path, line=st.line,
            message="%s를 salt나 반복 없이 단순 해시하고 있습니다. 일방향이지만 사전공격·"
                    "레인보우테이블에 취약하여 '안전한 암호 알고리즘'으로 보기 어렵습니다." % label,
            article=ART_7_1 + " 단서", quote=QUOTE_7_1,
            fix="BCryptPasswordEncoder 또는 Argon2PasswordEncoder처럼 salt와 작업계수를 "
                "내장한 구현체를 사용하십시오.",
            evidence=redact(st.text),
        ))

    return findings


RULES = [
    rule_article7_user_storage,
    rule_article7_non_user_storage,
    rule_article7_device_storage,
    rule_article7_internet_transmission,
    rule_article7_server_receive,
    rule_article12_api_output,
    rule_article12_log_output,
    rule_article8_access_log,
    rule_password_one_way,
]


# --------------------------------------------------------------------------- #
# 분석
# --------------------------------------------------------------------------- #

def analyze(path: str, text: str, dic: Dictionary, config: dict | None = None) -> list[Finding]:
    src = prepare(path, text, config)
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(src, dic))

    kept = []
    for f in findings:
        suppressed = src.ignores.get(f.line, set())
        if f.rule in suppressed or f.rule_id in suppressed:
            continue
        kept.append(f)

    kept.sort(key=lambda f: (-CONFIDENCE_RANK.get(f.confidence, 0), f.line))
    return kept


# --------------------------------------------------------------------------- #
# 설정
# --------------------------------------------------------------------------- #

def find_config(start_dir: str) -> tuple[dict, str]:
    """파일 위치에서 위로 올라가며 .pipa.json을 찾는다. -> (설정, 프로젝트 루트)"""
    cur = os.path.abspath(start_dir)
    for _ in range(24):
        candidate = os.path.join(cur, CONFIG_NAME)
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as fp:
                    cfg = dict(DEFAULT_CONFIG)
                    cfg.update(json.load(fp))
                    return cfg, cur
            except (OSError, ValueError):
                return dict(DEFAULT_CONFIG), cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return dict(DEFAULT_CONFIG), os.path.abspath(start_dir)


def is_excluded(path: str, root: str, cfg: dict) -> bool:
    patterns = cfg.get("exclude") or []
    if not patterns:
        return False
    abs_path = os.path.abspath(path)
    try:
        rel = os.path.relpath(abs_path, root)
    except ValueError:
        rel = abs_path
    rel = rel.replace(os.sep, "/")
    for pattern in patterns:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch("/" + rel, pattern):
            return True
        # 디렉터리 패턴 편의 처리: "fixtures/" -> 그 아래 전부
        if pattern.endswith("/") and rel.startswith(pattern):
            return True
    return False


# --------------------------------------------------------------------------- #
# 훅 모드
# --------------------------------------------------------------------------- #

CODEX_PATCH_HEADER_RE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")
CODEX_PATCH_MOVE_RE = re.compile(r"^\*\*\* Move to: (.+)$")


def _codex_patch_sections(command: str):
    """Codex apply_patch 명령을 파일별 구간으로 나눈다.

    반환값은 ``[(동작, 원본 경로, 이동 경로, 본문 행)]``이다. apply_patch 자체를 실행하지 않고
    PreToolUse에서 결과를 합성하기 위한 최소 문법만 읽는다.
    """
    lines = command.splitlines()
    if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        return None

    sections = []
    index = 1
    while index < len(lines) - 1:
        header = CODEX_PATCH_HEADER_RE.match(lines[index])
        if header is None:
            return None
        operation, raw_path = header.groups()
        index += 1
        body = []
        while index < len(lines) - 1 and CODEX_PATCH_HEADER_RE.match(lines[index]) is None:
            body.append(lines[index])
            index += 1

        move_to = None
        if operation == "Update" and body:
            move = CODEX_PATCH_MOVE_RE.match(body[0])
            if move is not None:
                move_to = move.group(1)
                body = body[1:]
        sections.append((operation, raw_path, move_to, body))
    return sections


def _find_line_sequence(lines: list[str], needle: list[str], start: int = 0) -> int | None:
    if not needle:
        return None
    limit = len(lines) - len(needle) + 1
    for index in range(max(0, start), max(0, limit)):
        if lines[index:index + len(needle)] == needle:
            return index
    return None


def _codex_update_result(current: str, body: list[str]) -> str | None:
    """Update File 구간을 현재 내용에 메모리상 적용한다. 실제 파일은 변경하지 않는다."""
    if not body:
        return current

    hunks: list[tuple[str, list[str]]] = []
    marker = None
    hunk_lines: list[str] = []
    for line in body:
        if line.startswith("@@"):
            if marker is not None:
                hunks.append((marker, hunk_lines))
            marker = line[2:].strip()
            hunk_lines = []
        elif marker is None:
            return None
        else:
            hunk_lines.append(line)
    if marker is None:
        return None
    hunks.append((marker, hunk_lines))

    result = current.splitlines()
    cursor = 0
    for marker, lines in hunks:
        old_lines: list[str] = []
        new_lines: list[str] = []
        for line in lines:
            if line == "\\ No newline at end of file":
                continue
            if not line or line[0] not in " +-":
                return None
            value = line[1:]
            if line[0] in " -":
                old_lines.append(value)
            if line[0] in " +":
                new_lines.append(value)

        search_from = cursor
        if marker:
            marker_index = next(
                (index for index in range(cursor, len(result))
                 if result[index].strip() == marker or marker in result[index]),
                None,
            )
            if marker_index is None:
                return None
            search_from = marker_index

        position = _find_line_sequence(result, old_lines, search_from)
        if position is None:
            if old_lines:
                return None
            if not marker:
                return None
            position = search_from + 1
        result[position:position + len(old_lines)] = new_lines
        cursor = position + len(new_lines)

    trailing_newline = current.endswith(("\n", "\r"))
    rebuilt = "\n".join(result)
    if trailing_newline and rebuilt:
        rebuilt += "\n"
    return rebuilt


def _codex_patch_targets(event: str, event_data: dict, tool_input: dict):
    """Codex apply_patch 이벤트에서 검사할 ``(경로, 결과 텍스트)``를 만든다."""
    command = tool_input.get("command")
    cwd = event_data.get("cwd")
    if not isinstance(command, str) or not command:
        return [], "apply_patch 명령이 없습니다"
    if not isinstance(cwd, str) or not cwd:
        return [], "Codex 훅 이벤트에 cwd 가 없습니다"

    sections = _codex_patch_sections(command)
    if sections is None:
        return [], "apply_patch 형식을 해석할 수 없습니다"

    targets: list[tuple[str, str]] = []
    for operation, raw_path, move_to, body in sections:
        selected_path = move_to or raw_path
        path = selected_path if os.path.isabs(selected_path) else os.path.join(cwd, selected_path)
        path = os.path.abspath(path)
        if not path.endswith(SUPPORTED_EXT) or operation == "Delete":
            continue

        if event == "PostToolUse":
            text = _read(path)
            if text is None:
                return targets, "apply_patch 완료 파일을 읽을 수 없습니다"
            targets.append((path, text))
            continue

        if event != "PreToolUse":
            continue
        if operation == "Add":
            if any(not line.startswith("+") for line in body):
                return targets, "apply_patch 신규 파일 내용을 해석할 수 없습니다"
            text = "\n".join(line[1:] for line in body)
            if body:
                text += "\n"
            targets.append((path, text))
            continue

        current = _read(os.path.abspath(raw_path if os.path.isabs(raw_path)
                                        else os.path.join(cwd, raw_path)))
        if current is None:
            return targets, "apply_patch 대상 파일을 읽을 수 없습니다"
        text = _codex_update_result(current, body)
        if text is None:
            return targets, "apply_patch 결과를 재구성할 수 없습니다"
        targets.append((path, text))
    return targets, None


def resulting_text(event: str, tool_name: str, tool_input: dict, path: str):
    """검사 대상 텍스트를 만든다.

    Write는 content를 그대로 쓴다. Edit는 디스크의 현재 내용에 패치를 적용한 결과를
    합성한다. 파일 전체 문맥이 필요한 규칙(@Entity 존재 여부 등)을 위해서다.
    PostToolUse는 이미 기록된 파일을 읽는다.
    """
    if event == "PostToolUse":
        return _read(path)

    if tool_name == "Write":
        content = tool_input.get("content")
        return content if isinstance(content, str) else None

    if tool_name == "Edit":
        old = tool_input.get("old_string")
        new = tool_input.get("new_string")
        if not isinstance(new, str):
            return None
        current = _read(path)
        if current is None or not isinstance(old, str) or old not in current:
            return new  # 합성 불가 — 새 조각만이라도 검사한다.
        if tool_input.get("replace_all"):
            return current.replace(old, new)
        return current.replace(old, new, 1)

    return None


def _read(path: str):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fp:
            return fp.read()
    except OSError:
        return None


def format_deny_reason(findings: list[Finding]) -> str:
    lines = [
        "pipa-guard: 개인정보 보호조치 위반 %d건이 검출되어 파일 쓰기를 차단했습니다." % len(findings),
        "",
    ]
    for f in findings:
        lines.append("[%s] %s:%d" % (f.rule_id, os.path.basename(f.path), f.line))
        lines.append("  문제: %s" % f.message)
        lines.append("  근거: %s" % f.article)
        for q in f.quote.splitlines():
            lines.append("        %s" % q)
        lines.append("  수정: %s" % f.fix)
        lines.append("  코드: %s" % f.evidence)
        lines.append("")
    lines.append("위 위반을 모두 해소한 코드로 다시 작성하십시오. "
                 "조항을 충족하지 못하면 같은 이유로 다시 차단됩니다.")
    return "\n".join(lines)


def format_warning(findings: list[Finding]) -> str:
    lines = ["pipa-guard 경고 %d건 (차단하지 않음, 확인 필요):" % len(findings), ""]
    for f in findings:
        lines.append("[%s] %s:%d" % (f.rule_id, os.path.basename(f.path), f.line))
        lines.append("  %s" % f.message)
        lines.append("  근거: %s" % f.article)
        lines.append("  수정: %s" % f.fix)
        lines.append("")
    return "\n".join(lines)


def undetermined(reason: str) -> int:
    """판정하지 못했다는 것을 사용자에게 알린다. 종료코드는 0이다.

    편집을 막지는 않는다. 판정하지 못한 것을 근거로 차단하면 조항 없는 차단이 된다.
    그러나 **조용히 통과시키지도 않는다.** 적법한 코드가 통과할 때의 출력도 "없음"이므로,
    신호가 없으면 사용자와 에이전트 모두 "검사해서 문제없음"과 "검사하지 못함"을 구별할
    수 없다. 보호가 사라진 사실을 아무도 모르는 상태가 이 프로젝트에서 가장 나쁜 상태다.

    systemMessage 는 훅 공통 출력 필드다. 사용자에게 경고로 보이고, 결정에는 관여하지
    않는다. 계약은 tests/run_hooks.py 가 고정한다.
    """
    print(json.dumps({
        "systemMessage": "pipa-guard: 이 편집을 검사하지 못했습니다 — %s" % reason,
    }, ensure_ascii=False))
    return 0


def run_hook() -> int:
    try:
        event_data = json.load(sys.stdin)
    except (ValueError, OSError):
        return undetermined("훅 이벤트 JSON을 읽을 수 없습니다")
    if not isinstance(event_data, dict):
        return undetermined("훅 이벤트가 객체가 아닙니다")

    event = event_data.get("hook_event_name") or ""
    tool_name = event_data.get("tool_name") or ""
    tool_input = event_data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return undetermined("훅 이벤트의 tool_input 형식이 예상과 다릅니다")

    target_error = None
    if tool_name == "apply_patch":
        targets, target_error = _codex_patch_targets(event, event_data, tool_input)
    else:
        path = tool_input.get("file_path") or ""
        if not isinstance(path, str) or not path:
            return undetermined("훅 이벤트에 file_path 가 없습니다")
        # 아래 두 갈래는 실패가 아니라 "검사 대상이 아니다"이므로 조용히 통과시킨다.
        if not path.endswith(SUPPORTED_EXT):
            return 0
        text = resulting_text(event, tool_name, tool_input, path)
        targets = [(path, text)] if text else []

    if not targets and target_error:
        return undetermined(target_error)
    if not targets:
        return 0

    scoped_targets: list[tuple[str, str, dict]] = []
    try:
        for path, text in targets:
            cfg, root = find_config(os.path.dirname(os.path.abspath(path)) or os.getcwd())
            if not is_excluded(path, root, cfg):
                scoped_targets.append((path, text, cfg))
    except Exception as exc:
        # 설정 탐색 실패에도 소스나 예외 메시지를 그대로 내보내지 않는다. (규약 7)
        return undetermined("검사 범위를 정하는 중 오류가 발생했습니다 (%s)" % type(exc).__name__)

    # exclude는 정상적인 비대상 판정이다. 사전보다 먼저 적용해야 제외 대상이 사전 오류로
    # 인해 "검사하지 못함"으로 바뀌지 않는다.
    if not scoped_targets and not target_error:
        return 0

    try:
        dic = load_dictionary()
    except (OSError, ValueError) as exc:
        # 사전이 없거나 깨졌다. 규칙이 대상을 고를 수 없으므로 아무것도 검출되지 않는다.
        return undetermined("항목 사전을 읽을 수 없습니다 (%s)" % type(exc).__name__)

    findings: list[Finding] = []
    try:
        for path, text, cfg in scoped_targets:
            findings.extend(analyze(path, text, dic, cfg))
    except Exception as exc:
        # 예외 메시지에 소스 조각이 섞일 수 있으므로 종류만 알린다. (규약 7)
        return undetermined("판정 중 오류가 발생했습니다 (%s)" % type(exc).__name__)
    findings.sort(key=lambda f: (-CONFIDENCE_RANK.get(f.confidence, 0), f.path, f.line))
    high = [f for f in findings if f.confidence == "high"]
    rest = [f for f in findings if f.confidence != "high"]

    if event == "PreToolUse":
        output = {}
        if target_error:
            output["systemMessage"] = "pipa-guard: 이 편집의 일부를 검사하지 못했습니다 — %s" % target_error
        if high:
            output["hookSpecificOutput"] = {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": format_deny_reason(high),
            }
        if output:
            print(json.dumps(output, ensure_ascii=False))
        return 0

    if event == "PostToolUse":
        output = {}
        if target_error:
            output["systemMessage"] = "pipa-guard: 이 편집의 일부를 검사하지 못했습니다 — %s" % target_error
        if rest:
            output["hookSpecificOutput"] = {
                "hookEventName": "PostToolUse",
                "additionalContext": format_warning(rest),
            }
        if output:
            print(json.dumps(output, ensure_ascii=False))
        return 0

    return 0


# --------------------------------------------------------------------------- #
# CLI 모드
# --------------------------------------------------------------------------- #

def collect_targets(args: list[str]) -> list[str]:
    targets: list[str] = []
    for arg in args:
        if os.path.isdir(arg):
            for dirpath, dirnames, filenames in os.walk(arg):
                dirnames[:] = [d for d in dirnames
                               if d not in {".git", "build", "target", "out", "node_modules", ".gradle"}]
                for name in sorted(filenames):
                    if name.endswith(SUPPORTED_EXT):
                        targets.append(os.path.join(dirpath, name))
        elif arg.endswith(SUPPORTED_EXT):
            targets.append(arg)
    return targets


def fail(reason: str) -> int:
    """엔진이 판정하지 못했음을 stderr로 알린다. -> EXIT_ENGINE

    CI가 종료코드만 보고 "위반을 찾았다"(1)와 "엔진이 깨졌다"(3)를 구별할 수 있어야 한다.
    같은 코드로 합치면 사전이 깨진 것을 exclude 설정 문제로 오진한다. 실제로 그랬다.
    """
    sys.stderr.write("pipa-guard: %s\n" % reason)
    return EXIT_ENGINE


def run_cli(args: list[str]) -> int:
    as_json = "--json" in args
    paths = collect_targets([a for a in args if not a.startswith("--")])
    if not paths:
        sys.stderr.write("pipa-guard: 검사할 .java / .kt 파일이 없습니다.\n")
        return EXIT_USAGE

    try:
        dic = load_dictionary()
    except (OSError, ValueError) as exc:
        return fail("항목 사전(rules/pii_items.json)을 읽을 수 없습니다 — %s"
                    % type(exc).__name__)

    all_findings: list[Finding] = []
    for path in paths:
        text = _read(path)
        if text is None:
            continue
        cfg, root = find_config(os.path.dirname(os.path.abspath(path)))
        if is_excluded(path, root, cfg):
            continue
        try:
            all_findings.extend(analyze(path, text, dic, cfg))
        except Exception as exc:
            # 예외 메시지에 소스 조각이 섞일 수 있으므로 종류만 알린다. (규약 7)
            return fail("%s 판정 중 오류가 발생했습니다 — %s" % (path, type(exc).__name__))

    if as_json:
        print(json.dumps([f.__dict__ for f in all_findings], ensure_ascii=False, indent=2))
    else:
        for f in all_findings:
            mark = {"high": "차단", "medium": "경고", "low": "참고"}.get(f.confidence, f.confidence)
            print("%s:%d  [%s] %s" % (f.path, f.line, mark, f.rule_id))
            print("    문제: %s" % f.message)
            print("    근거: %s" % f.article)
            print("    수정: %s" % f.fix)
            print("    코드: %s" % f.evidence)
            print()
        high = sum(1 for f in all_findings if f.confidence == "high")
        print("파일 %d개 검사 — 차단 %d건, 경고 %d건"
              % (len(paths), high, len(all_findings) - high))

    return EXIT_HIGH if any(f.confidence == "high" for f in all_findings) else EXIT_CLEAN


def main() -> int:
    args = sys.argv[1:]
    if args:
        return run_cli(args)
    return run_hook()


if __name__ == "__main__":
    sys.exit(main())
