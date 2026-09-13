// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// Base64는 암호화가 아니다. 이름이 encoded인 값을 평문 HTTP로 보내도 보호조치로 인정하면 안 된다.
package com.example.partner;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.springframework.web.client.RestTemplate;

public class EncodedPassportClient {

    private final RestTemplate restTemplate;

    public EncodedPassportClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String passportNumber) {
        String encodedPassportNumber = Base64.getEncoder().encodeToString(
            passportNumber.getBytes(StandardCharsets.UTF_8)
        );
        restTemplate.postForEntity(
            "http://partner.example.com/passports",
            encodedPassportNumber,
            Void.class
        );
    }
}
