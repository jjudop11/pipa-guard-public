// pipa-fixture-expect-clean
// JPA ColumnTransformer가 데이터베이스의 대칭키 암호화 함수를 쓰도록 연결한다.
// @Convert가 아니더라도 저장 경로에 구조적으로 연결된 암호화 조치다.
package com.example.identity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import org.hibernate.annotations.ColumnTransformer;

@Entity
public class EncryptedPassportRecord {

    @Id
    private Long id;

    @Column(name = "passport_no_enc", nullable = false, length = 512)
    @ColumnTransformer(
        write = "pgp_sym_encrypt(?, current_setting('app.data_key'))",
        read = "pgp_sym_decrypt(passport_no_enc, current_setting('app.data_key'))"
    )
    private String passportNumber;
}
