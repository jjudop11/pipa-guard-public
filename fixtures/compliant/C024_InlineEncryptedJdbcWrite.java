// pipa-fixture-expect-clean
// 여권번호가 SQL 쓰기 호출 안에서 직접 AES-GCM 암호화된다. 별도 암호문 변수가 없어도
// 해당 식별자가 암호화 호출의 인자라는 연결을 인정해야 한다.
package com.example.identity;

import org.springframework.jdbc.core.JdbcTemplate;

public class InlineEncryptedIdentityJdbcRepository {

    private final JdbcTemplate jdbcTemplate;
    private final AesGcmEncryptor encryptor;

    public void insert(Long memberId, String passportNumber) {
        jdbcTemplate.update(
            "INSERT INTO member_identity (member_id, passport_no_enc) VALUES (?, ?)",
            memberId,
            encryptor.encrypt(passportNumber)
        );
    }
}
