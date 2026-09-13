// pipa-fixture-expect-clean
// pipa-fixture-config: {"accessLogPolicies":[{"source":"C087_AccessLogMdcComponents.java#recordAccess","components":{"actorId":{"external":"security_context"},"accessedAt":{"external":"logger_timestamp"},"sourceInfo":{"external":"request_mdc"},"dataSubjectInfo":{"argument":"memberId"},"action":{"argument":"action"}},"evidence":"config/logback-access.xml"}]}
// 보안 컨텍스트·logger·MDC가 공급하는 구성요소는 명시적 근거가 있으면 직접 인자를 요구하지 않는다.
package com.example.audit;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MdcAccessAuditService {
    private static final Logger accessLog = LoggerFactory.getLogger("ACCESS_LOG");

    public void recordAccess(String memberId, String action) {
        accessLog.info("subject={} action={}", memberId, action);
    }
}
