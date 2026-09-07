// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 주민등록번호 원문을 외부의 명시적 http:// 주소로 직접 전송한다. 개인정보 후보,
// 인터넷망 전송 sink, 전송 구간 암호화 부재가 한 호출에서 모두 확인된다.
package com.example.identity;

import org.springframework.web.client.RestTemplate;

public class IdentityPartnerClient {

    private final RestTemplate restTemplate;

    public IdentityPartnerClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String residentRegistrationNumber) {
        restTemplate.postForEntity(
            "http://partner.example.com/member-identities",
            residentRegistrationNumber,
            Void.class
        );
    }
}
