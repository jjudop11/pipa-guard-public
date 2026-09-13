// pipa-fixture-expect: K-LEAK-001/excessive-log-output
// pipa-fixture-config: {"outputPolicies":[{"sink":"log","source":"V057_ExcessiveSlf4jLog.java#recordLookup","purpose":"회원 조회 성공 건수 집계","allowedItems":[],"evidence":"docs/privacy/member-log-policy.md"}]}
// 개인정보를 허용하지 않은 로그 용도에 성명을 기록한다.
package com.example.member;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MemberLookupService {
    private static final Logger log = LoggerFactory.getLogger(MemberLookupService.class);

    public void recordLookup(String fullName) {
        log.info("member lookup succeeded: {}", fullName);
    }
}
