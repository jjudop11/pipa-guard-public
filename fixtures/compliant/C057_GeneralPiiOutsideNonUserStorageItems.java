// pipa-fixture-expect-clean
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internet"}
// 일반 개인정보 세 항목은 제7조 제3항의 고유식별정보 저장 범위도 아니다.
package com.example.employee;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class EmployeeContactRecord {

    @Id
    private Long id;

    @Column(length = 20)
    private String fullName;

    @Column(length = 40)
    private String userEmailAddress;

    @Column(length = 20)
    private String userMobilePhoneNumber;
}
