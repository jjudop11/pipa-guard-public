// pipa-fixture-expect-clean
// 일반 개인정보 세 항목은 제7조 제2항이 열거한 이용자 저장 7항목이 아니다.
package com.example.member;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class MemberContactRecord {

    @Id
    private Long id;

    @Column(length = 20)
    private String fullName;

    @Column(length = 40)
    private String userEmailAddress;

    @Column(length = 20)
    private String userMobilePhoneNumber;
}
