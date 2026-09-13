// 주민등록번호는 제7조 제2항 제1호에 따라 양방향 암호화 저장이 적법하다.
// AES가 쓰였다는 사실만으로 검출해서는 안 된다. K-ENC-002는 비밀번호에만 적용된다.
// (제7조 제2항 규칙 K-ENC-001은 Phase 2에서 이 파일을 적법으로 판정해야 한다.)
package com.example.customer;

import com.example.support.AesGcmStringConverter;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class Customer {

    @Id
    private Long id;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "resident_reg_no_enc", length = 512)
    private String residentRegistrationNumber;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "account_no_enc", length = 512)
    private String accountNo;
}
