// pipa-fixture-expect-warn: K-LEAK-001/unverified-log-output-purpose
// 개인정보 로그는 보이지만 로그 용도와 허용 항목의 근거가 없다.
package com.example.member;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoginAuditService {
    private static final Logger log = LoggerFactory.getLogger(LoginAuditService.class);

    public void recordFailure(String userEmailAddress) {
        log.warn("login failed: {}", userEmailAddress);
    }
}
