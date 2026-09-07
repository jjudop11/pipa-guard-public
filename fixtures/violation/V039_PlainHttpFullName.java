// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 사람의 성명으로 한정된 fullName 원문을 외부 평문 HTTP로 전송한다.
package com.example.member;

import org.springframework.web.client.RestTemplate;

public class MemberNameClient {

    private final RestTemplate restTemplate;

    public MemberNameClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String fullName) {
        restTemplate.postForEntity(
            "http://partner.example.com/member-names",
            fullName,
            Void.class
        );
    }
}
