// pipa-fixture-expect: K-ENC-002/two-way-converter
// JPA AttributeConverter는 복호화를 전제한다. 비밀번호에 붙이면 제7조 제1항 단서 위반.
package com.example.member;

import com.example.support.AesGcmStringConverter;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class Account {

    @Id
    private Long id;

    @Column(name = "login_id")
    private String loginId;

    @Convert(converter = AesGcmStringConverter.class)
    @Column(name = "password")
    private String password;
}
