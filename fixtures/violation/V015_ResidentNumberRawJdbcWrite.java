// pipa-fixture-expect: K-ENC-001/plaintext-sql-write
// 주민등록번호 원문 변수를 SQL INSERT의 값 인자로 직접 전달한다.
package com.example.identity;

import org.springframework.jdbc.core.JdbcTemplate;

public class IdentityJdbcRepository {

    private final JdbcTemplate jdbcTemplate;

    public IdentityJdbcRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public void insert(Long memberId, String residentRegistrationNumber) {
        jdbcTemplate.update(
            "INSERT INTO member_identity (member_id, resident_reg_no) VALUES (?, ?)",
            memberId,
            residentRegistrationNumber
        );
    }
}
