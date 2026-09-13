// pipa-fixture-expect-clean
// 일반 업무 로그는 접속기록 정책이 지정한 sink가 아니므로 구성요소 검사의 대상이 아니다.
package com.example.batch;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BatchMetricService {
    private static final Logger log = LoggerFactory.getLogger(BatchMetricService.class);

    public void recordCompletion(String operatorId, String status) {
        log.info("batch completed operator={} status={}", operatorId, status);
    }
}
