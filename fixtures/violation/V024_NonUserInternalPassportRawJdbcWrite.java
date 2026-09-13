// pipa-fixture-expect: K-ENC-003/plaintext-sql-write
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internal","riskAssessment":null}
// 위험도 분석에 따른 범위 조정 없이 비이용자의 여권번호 원문을 SQL 값으로 직접 저장한다.
package com.example.partner;

import org.springframework.jdbc.core.JdbcTemplate;

public class PartnerPassportRepository {

    private final JdbcTemplate jdbcTemplate;

    public PartnerPassportRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public void insert(Long partnerId, String passportNumber) {
        jdbcTemplate.update(
            "INSERT INTO partner_passport (partner_id, passport_no) VALUES (?, ?)",
            partnerId,
            passportNumber
        );
    }
}
