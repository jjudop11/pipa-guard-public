// pipa-fixture-expect-clean
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internet","riskAssessment":null}
// 제7조 제3항은 고유식별정보만 열거한다. 제2항의 이용자 금융정보인 신용카드번호와
// 계좌번호를 비이용자 맥락에서도 같은 규칙으로 넓히면 조항 범위를 벗어난다.
package com.example.vendor;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class VendorSettlement {

    @Id
    private Long id;

    @Column(name = "credit_card_no", length = 20)
    private String creditCardNumber;

    @Column(name = "account_no", length = 20)
    private String accountNumber;
}
