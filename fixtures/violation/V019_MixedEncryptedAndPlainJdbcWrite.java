// pipa-fixture-expect: K-ENC-001/plaintext-sql-write
// 같은 SQL 쓰기에서 여권번호는 암호화하지만 주민등록번호는 원문으로 전달한다.
// 한 값의 암호화 호출이 문장 전체를 적법하게 만들면 안 된다.
package com.example.identity;

import org.springframework.jdbc.core.JdbcTemplate;

public class MixedIdentityJdbcRepository {

    private final JdbcTemplate jdbcTemplate;
    private final AesGcmEncryptor encryptor;

    public void insert(String passportNumber, String residentRegistrationNumber) {
        jdbcTemplate.update(
            "INSERT INTO member_identity (passport_no_enc, resident_reg_no) VALUES (?, ?)",
            encryptor.encrypt(passportNumber),
            residentRegistrationNumber
        );
    }
}
