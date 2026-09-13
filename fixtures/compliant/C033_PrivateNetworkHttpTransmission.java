// pipa-fixture-expect-clean
// RFC1918 사설 주소의 내부 호출은 제7조 제4항의 인터넷망 구간이라고 확정하지 않는다.
package com.example.internal;

import org.springframework.web.client.RestTemplate;

public class InternalIdentityClient {

    private final RestTemplate restTemplate;

    public InternalIdentityClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String residentRegistrationNumber) {
        restTemplate.postForEntity(
            "http://10.20.30.40/internal/member-identities",
            residentRegistrationNumber,
            Void.class
        );
    }
}
