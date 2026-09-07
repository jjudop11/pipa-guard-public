// pipa-fixture-expect-clean
// NoopHostnameVerifier가 파일에 있어도 개인정보가 네트워크 sink에 도달하지 않으면 이 규칙은 없다.
package com.example.health;

import org.apache.hc.client5.http.ssl.NoopHostnameVerifier;
import org.springframework.web.client.RestTemplate;

public class LegacyHealthClient {

    private final RestTemplate restTemplate;

    public LegacyHealthClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public String status() {
        Object verifier = NoopHostnameVerifier.INSTANCE;
        return restTemplate.getForObject("https://health.example.com/status", String.class);
    }
}
