// pipa-fixture-expect-clean
// @Entity 안에 주민등록번호 식별자가 있지만 @Transient라 데이터베이스 컬럼이 아니다.
// 화면 입력을 받는 동안만 존재하고 영속화되는 값은 별도의 검증 결과뿐이다.
// K-ENC-001은 엔티티 존재만으로 모든 필드를 저장 sink로 간주해서는 안 된다.
package com.example.identity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Transient;

@Entity
public class IdentityVerificationAttempt {

    @Id
    private Long id;

    @Transient
    private String residentRegistrationNumber;

    @Column(name = "verification_result", nullable = false)
    private String verificationResult;
}
