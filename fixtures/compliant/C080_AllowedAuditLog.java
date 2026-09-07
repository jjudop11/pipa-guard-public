// pipa-fixture-expect-clean
// pipa-fixture-config: {"outputPolicies":[{"sink":"log","source":"C080_AllowedAuditLog.java#recordFailure","purpose":"계정 탈취 조사용 로그인 실패 감사","allowedItems":["emailAddress"],"evidence":"docs/privacy/login-audit.md"}]}
// 감사 목적에 필요한 이메일 주소 항목을 정책이 명시적으로 허용한다.
package com.example.member;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoginAuditService {
    private static final Logger log = LoggerFactory.getLogger(LoginAuditService.class);

    public void recordFailure(String userEmailAddress) {
        log.warn("login failed: {}", userEmailAddress);
    }
}
