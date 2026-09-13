// pipa-fixture-expect-clean
// 영속화 필드여도 개인정보 사전과 완전 일치하지 않는 식별자는 후보가 아니다. 부분 문자열이나
// 주변의 @Entity·@Column 신호가 orderNo, accountId, deviceFingerprint 등을 개인정보로
// 승격시켜서는 안 된다. tests/dictionary_cases.json의 no_match를 규칙 계층에서도 방어한다.
package com.example.order;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class OrderDeviceMetadata {

    @Id
    private Long id;

    @Column(name = "order_no")
    private String orderNo;

    @Column(name = "account_id")
    private String accountId;

    @Column(name = "card_type")
    private String cardType;

    @Column(name = "device_fingerprint")
    private String deviceFingerprint;

    @Column(name = "license_key")
    private String licenseKey;

    @Column(name = "passport_country")
    private String passportCountry;
}
