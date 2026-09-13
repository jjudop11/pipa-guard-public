// pipa-fixture-expect-clean
// 로그 포맷 문자열에 개인정보 항목명이 있어도 실제 개인정보 값 인자가 아니면 대상이 아니다.
package com.example.member;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MemberMetricService {
    private static final Logger log = LoggerFactory.getLogger(MemberMetricService.class);

    public void record(String status) {
        log.info("userEmailAddress field status: {}", status);
    }
}
