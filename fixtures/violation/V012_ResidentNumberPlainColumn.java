// pipa-fixture-expect: K-ENC-001/plaintext-sized-column
// 주민등록번호를 원문 길이의 영속 컬럼에 저장한다. 14자는 안전한 암호 알고리즘의
// IV·인증 태그·암호문을 함께 담을 수 없으므로 암호화 부재가 구조로 확인된다.
package com.example.identity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class MemberIdentity {

    @Id
    private Long id;

    @Column(name = "resident_reg_no", nullable = false, length = 14)
    private String residentRegistrationNumber;
}
