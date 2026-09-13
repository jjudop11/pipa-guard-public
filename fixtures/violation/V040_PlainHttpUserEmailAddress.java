// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 사용자 이메일 주소 원문을 외부 평문 HTTP로 전송한다.
package com.example.member;

import org.springframework.web.client.RestTemplate;

public class MemberEmailClient {

    private final RestTemplate restTemplate;

    public MemberEmailClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String userEmailAddress) {
        restTemplate.postForEntity(
            "http://partner.example.com/member-emails",
            userEmailAddress,
            Void.class
        );
    }
}
