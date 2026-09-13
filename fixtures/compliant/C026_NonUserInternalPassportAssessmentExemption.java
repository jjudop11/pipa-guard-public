// pipa-fixture-expect-clean
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internal","riskAssessment":{"basis":"privacy_impact_assessment","document":"docs/privacy/impact-assessment-2026.md","date":"2026-08-31","conclusion":"encryption_not_required","exemptItems":["passportNumber"]}}
// 내부망의 주민등록번호 외 고유식별정보에 대해 영향평가 결과가 여권번호를 암호화 미적용
// 범위로 명시했다. 이 선언 범위 안에서만 제7조 제3항 제2호 단서를 적용한다.
package com.example.publicagency;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class AssessedPassportRecord {

    @Id
    private Long id;

    @Column(name = "passport_no", length = 12)
    private String passportNumber;
}
