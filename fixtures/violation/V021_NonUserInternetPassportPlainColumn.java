// pipa-fixture-expect: K-ENC-003/plaintext-sized-column
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internet","riskAssessment":{"basis":"risk_analysis","document":"docs/privacy/internal-unique-id-risk.md","date":"2026-08-31","conclusion":"encryption_not_required","exemptItems":["passportNumber"]}}
// 제7조 제3항 제1호의 인터넷망 구간에는 영향평가·위험도 분석 결과에 따른 예외가 없다.
package com.example.partner;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class PartnerPassport {

    @Id
    private Long id;

    @Column(name = "passport_no", length = 12)
    private String passportNumber;
}
