// pipa-fixture-expect-clean
// pipa-fixture-config: {"accessLogPolicies":[{"source":"C085_CompleteAccessLog.java#recordAccess","components":{"actorId":{"argument":"operatorId"},"accessedAt":{"external":"logger_timestamp"},"sourceInfo":{"argument":"clientIp"},"dataSubjectInfo":{"argument":"memberId"},"action":{"argument":"action"}},"evidence":"config/logback-access.xml"}]}
// logger가 접속일시를 공급하고 나머지 네 구성요소가 한 접속기록 호출에 모두 있다.
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
