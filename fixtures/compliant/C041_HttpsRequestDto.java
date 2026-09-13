// pipa-fixture-expect-clean
// 주민등록번호가 요청 DTO에 들어가지만 HTTPS 전송 구간을 사용한다.
package com.example.identity;

import org.springframework.web.client.RestTemplate;

public class SecureIdentityDtoClient {

    private final RestTemplate restTemplate;

    public SecureIdentityDtoClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String residentRegistrationNumber) {
        PartnerIdentityRequest request =
            new PartnerIdentityRequest(residentRegistrationNumber);
        restTemplate.postForEntity(
            "https://partner.example.com/member-identities",
            request,
            Void.class
        );
    }
}
