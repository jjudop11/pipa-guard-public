// pipa-fixture-expect: K-ENC-003/plaintext-sized-column
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internal","riskAssessment":{"basis":"risk_analysis","document":"docs/privacy/internal-unique-id-risk.md","date":"2026-08-31","conclusion":"encryption_not_required","exemptItems":["residentRegistrationNumber","passportNumber"]}}
// 내부망이라도 주민등록번호에는 제7조 제3항 제2호 단서가 적용되지 않는다. 평가 결과의
// 면제 범위에 잘못 포함했더라도 원문 길이 컬럼 저장은 차단되어야 한다.
package com.example.employee;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class EmployeeIdentity {

    @Id
    private Long id;

    @Column(name = "resident_reg_no", length = 14)
    private String residentRegistrationNumber;
}
