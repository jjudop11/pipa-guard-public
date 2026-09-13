// pipa-fixture-expect-clean
// 일반 개인정보 세 항목을 인증서를 검증하는 HTTPS endpoint로 전송한다.
package com.example.member;

import org.springframework.web.client.RestTemplate;

public class SecureMemberContactClient {

    private final RestTemplate restTemplate;

    public SecureMemberContactClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(
        String fullName,
        String userEmailAddress,
        String userMobilePhoneNumber
    ) {
        MemberContact request =
            new MemberContact(fullName, userEmailAddress, userMobilePhoneNumber);
        restTemplate.postForEntity(
            "https://partner.example.com/member-contacts",
            request,
            Void.class
        );
    }
}
