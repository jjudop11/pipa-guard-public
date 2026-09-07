// pipa-fixture-expect-warn: K-ENC-004/unverified-network-transmission
// 운전면허번호가 HTTP 클라이언트 sink로 가지만 endpoint의 스킴을 이 파일에서 확인할 수 없다.
// 인터넷망 평문 전송이라고 확정할 수 없으므로 차단하지 않고 경고해야 한다.
package com.example.contractor;

import org.springframework.web.client.RestTemplate;

public class LicenseVerificationClient {

    private final RestTemplate restTemplate;
    private final String endpoint;

    public LicenseVerificationClient(RestTemplate restTemplate, String endpoint) {
        this.restTemplate = restTemplate;
        this.endpoint = endpoint;
    }

    public void verify(String driverLicenseNumber) {
        restTemplate.postForEntity(endpoint, driverLicenseNumber, Void.class);
    }
}
