// pipa-fixture-expect: K-ENC-003/plaintext-sized-column
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internal","riskAssessment":{"document":"docs/privacy/internal-unique-id-risk.md","date":"2026-08-31"}}
// 평가 문서 경로가 있다는 사실만으로는 암호화 적용범위가 정해지지 않는다. 근거 종류·결론·
// 면제 항목이 빠진 설정은 보호를 끄지 않아야 한다.
package com.example.visitor;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class VisitorRegistration {

    @Id
    private Long id;

    @Column(name = "alien_reg_no", length = 14)
    private String alienRegistrationNumber;
}
