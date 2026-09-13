// pipa-fixture-expect-clean
// 제7조 제2항 각 호의 항목을 양방향 암호화해 저장한다. 제2항이 요구하는 그대로이므로
// 적법하다. Phase 1에서 사전에 7항목을 등재했으므로 "사전에 있는 항목"만으로 대상을
// 고르면 이 파일 전체가 오탐이 된다. K-ENC-002는 제7조 제1항 단서 규칙이고 대상은
// 비밀번호(one_way_only)뿐이다.
//
// C006은 주민등록번호·계좌번호를 담당한다. 여기는 나머지 항목이다.
package com.example.customer;

import com.example.support.AesGcmStringConverter;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class ForeignCustomer {

    @Id
    private Long id;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "passport_no_enc", length = 512)
    private String passportNo;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "driver_license_no_enc", length = 512)
    private String driverLicenseNo;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "alien_reg_no_enc", length = 512)
    private String alienRegistrationNo;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "credit_card_no_enc", length = 512)
    private String creditCardNo;
}
