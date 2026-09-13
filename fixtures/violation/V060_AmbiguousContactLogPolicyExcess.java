// pipa-fixture-expect-warn: K-LEAK-001/excessive-log-output
// pipa-fixture-config: {"outputPolicies":[{"sink":"log","source":"V060_AmbiguousContactLogPolicyExcess.java#recordDelivery","purpose":"알림 발송 성공 건수 집계","allowedItems":[],"evidence":"docs/privacy/delivery-log.md"}]}
// 사람 연락처인지 모호한 weak 별칭은 정책 초과여도 차단하지 않고 경고한다.
package com.example.notification;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DeliveryLogService {
    private static final Logger log = LoggerFactory.getLogger(DeliveryLogService.class);

    public void recordDelivery(String emailAddress) {
        log.info("delivery succeeded: {}", emailAddress);
    }
}
