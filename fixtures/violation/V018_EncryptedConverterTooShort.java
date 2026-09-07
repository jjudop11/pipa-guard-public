// pipa-fixture-expect: K-ENC-001/plaintext-sized-column
// AES-GCM 컨버터를 선언했지만 주민등록번호 컬럼이 14자뿐이다. 보호조치 이름이 있어도
// 실제 암호문을 담을 수 없는 저장 구조이므로 짧은 컬럼 증거가 우선해야 한다.
package com.example.identity;

import com.example.support.AesGcmStringConverter;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class BrokenEncryptedIdentity {

    @Id
    private Long id;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "resident_reg_no_enc", nullable = false, length = 14)
    private String residentRegistrationNumber;
}
