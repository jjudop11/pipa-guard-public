// pipa-fixture-expect-clean
// RestClient.retrieve()만 호출하고 terminal operation이 없으면 공식 계약상 실제 송신하지 않는다.
package com.example.identity;

import org.springframework.web.client.RestClient;

public class UnexecutedSpringIdentityRequest {

    private final RestClient restClient;

    public UnexecutedSpringIdentityRequest(RestClient restClient) {
        this.restClient = restClient;
    }

    public void prepare(String residentRegistrationNumber) {
        restClient.post()
            .uri("http://partner.example.com/member-identities")
            .body(new PartnerIdentityRequest(residentRegistrationNumber))
            .retrieve();
    }
}
