// pipa-fixture-expect: K-LOG-001/missing-access-log-component
// pipa-fixture-config: {"accessLogPolicies":[{"source":"V063_MissingAccessLogSubject.java#recordAccess","components":{"actorId":{"argument":"operatorId"},"accessedAt":{"external":"logger_timestamp"},"sourceInfo":{"argument":"clientIp"},"dataSubjectInfo":{"argument":"memberId"},"action":{"argument":"action"}},"evidence":"config/logback-access.xml"}]}
// 접속기록 정책은 다섯 구성요소를 선언했지만 실제 로그 호출에서 처리한 정보주체가 빠졌다.
package com.example.audit;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AccessAuditService {
    private static final Logger accessLog = LoggerFactory.getLogger("ACCESS_LOG");

    public void recordAccess(
            String operatorId, String clientIp, String memberId, String action) {
        accessLog.info("operator={} ip={} action={}", operatorId, clientIp, action);
    }
}
