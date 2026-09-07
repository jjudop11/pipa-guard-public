// pipa-fixture-expect-clean
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internet","riskAssessment":null}
// 비이용자의 여권번호를 실제 암호화 호출로 처리한 결과만 SQL 값 인자로 전달한다.
package com.example.partner;

import org.springframework.jdbc.core.JdbcTemplate;

public class EncryptedPartnerPassportRepository {

    private final JdbcTemplate jdbcTemplate;
    private final AesGcmEncryptor encryptor;

    public EncryptedPartnerPassportRepository(
            JdbcTemplate jdbcTemplate,
            AesGcmEncryptor encryptor) {
        this.jdbcTemplate = jdbcTemplate;
        this.encryptor = encryptor;
    }

    public void insert(Long partnerId, String passportNumber) {
        String encryptedPassport = encryptor.encrypt(passportNumber);
        jdbcTemplate.update(
            "INSERT INTO partner_passport (partner_id, passport_no_enc) VALUES (?, ?)",
            partnerId,
            encryptedPassport
        );
    }
}
