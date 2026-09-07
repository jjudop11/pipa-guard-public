// pipa-fixture-expect-clean
// 일반 기능 플래그 이름에 trustAll이 있어도 실제 TLS 검증 무력화 API가 아니다.
package com.example.identity;

import org.springframework.web.client.RestTemplate;

public class FeatureFlagIdentityClient {

    private final RestTemplate restTemplate;
    private final boolean trustAllPartnerFields;

    public FeatureFlagIdentityClient(
            RestTemplate restTemplate,
            boolean trustAllPartnerFields) {
        this.restTemplate = restTemplate;
        this.trustAllPartnerFields = trustAllPartnerFields;
    }

    public void send(String residentRegistrationNumber) {
        restTemplate.postForEntity(
            "https://partner.example.com/member-identities",
            residentRegistrationNumber,
            Void.class
        );
    }
}
