// pipa-fixture-expect-clean
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internet","riskAssessment":null}
// 인터넷망 구간에 저장하는 비이용자의 고유식별정보를 안전한 양방향 암호화 컨버터에 연결한다.
package com.example.visitor;

import com.example.support.AesGcmStringConverter;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class EncryptedVisitorIdentity {

    @Id
    private Long id;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "driver_license_no_enc", length = 512)
    private String driverLicenseNumber;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "alien_reg_no_enc", length = 512)
    private String alienRegistrationNumber;
}
