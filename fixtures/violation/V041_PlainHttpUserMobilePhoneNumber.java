// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 사용자 휴대전화번호 원문을 외부 평문 HTTP로 전송한다.
package com.example.member;

import org.springframework.web.client.RestTemplate;

public class MemberMobileClient {

    private final RestTemplate restTemplate;

    public MemberMobileClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String userMobilePhoneNumber) {
        restTemplate.postForEntity(
            "http://partner.example.com/member-mobiles",
            userMobilePhoneNumber,
            Void.class
        );
    }
}
