// pipa-fixture-expect-clean
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internal","riskAssessment":{"basis":"risk_analysis","document":"docs/privacy/internal-unique-id-risk.md","date":"2026-08-31","conclusion":"encryption_not_required","exemptItems":["passportNumber"]}}
// 영향평가·위험도 분석 결과의 항목별 범위를 지킨다. 주민등록번호는 항상 암호화하고,
// 단서가 허용하는 여권번호만 명시적으로 미적용한다.
package com.example.partner;

import com.example.support.AesGcmStringConverter;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class AssessedPartnerIdentity {

    @Id
    private Long id;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "resident_reg_no_enc", length = 512)
    private String residentRegistrationNumber;

    @Column(name = "passport_no", length = 12)
    private String passportNumber;
}
