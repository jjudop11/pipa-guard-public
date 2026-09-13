// pipa-fixture-expect-warn: K-LOG-001/unverified-access-log-components
// pipa-fixture-config: {"accessLogPolicies":[{"source":"V064_IncompleteAccessLogPolicy.java#recordAccess","components":{"actorId":{"argument":"operatorId"},"sourceInfo":{"argument":"clientIp"},"dataSubjectInfo":{"argument":"memberId"},"action":{"argument":"action"}},"evidence":"docs/privacy/access-log.md"}]}
// 접속일시 공급 방식이 빠진 정책은 누락을 단정하지 않고 경고한다.
package com.example.audit;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AccessAuditService {
    private static final Logger accessLog = LoggerFactory.getLogger("ACCESS_LOG");

    public void recordAccess(
            String operatorId, String clientIp, String memberId, String action) {
        accessLog.info(
                "operator={} ip={} subject={} action={}",
                operatorId, clientIp, memberId, action);
    }
}
