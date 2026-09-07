// pipa-fixture-expect-clean
// 주민등록번호를 AES-GCM으로 암호화한 변수만 SQL 쓰기 인자로 전달한다. SQL 문자열의
// 컬럼명과 암호화 변수명 모두 사전에 매칭되지만, 값 전파로 보호조치를 확인해야 한다.
package com.example.identity;

import org.springframework.jdbc.core.JdbcTemplate;

public class EncryptedIdentityJdbcRepository {

    private final JdbcTemplate jdbcTemplate;
    private final AesGcmEncryptor encryptor;

    public EncryptedIdentityJdbcRepository(JdbcTemplate jdbcTemplate, AesGcmEncryptor encryptor) {
        this.jdbcTemplate = jdbcTemplate;
        this.encryptor = encryptor;
    }

    public void insert(Long memberId, String residentRegistrationNumber) {
        String encryptedResidentRegistrationNumber = encryptor.encrypt(residentRegistrationNumber);
        jdbcTemplate.update(
            "INSERT INTO member_identity (member_id, resident_reg_no_enc) VALUES (?, ?)",
            memberId,
            encryptedResidentRegistrationNumber
        );
    }
}
