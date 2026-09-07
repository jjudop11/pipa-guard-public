// pipa-fixture-expect-warn: K-ENC-004/plaintext-http-transmission
// 일반 이메일 주소와 휴대전화번호는 조직·공용 연락처일 수도 있어 경고만 한다.
package com.example.contact;

import org.springframework.web.client.RestTemplate;

public class ContactClient {

    private final RestTemplate restTemplate;

    public ContactClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String emailAddress, String mobilePhoneNumber) {
        ContactRequest request = new ContactRequest(emailAddress, mobilePhoneNumber);
        restTemplate.postForEntity(
            "http://partner.example.com/contacts",
            request,
            Void.class
        );
    }
}
