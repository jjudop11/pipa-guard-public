// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 여권번호가 setter로 기존 요청 DTO에 들어간 뒤 외부 평문 HTTP sink에 도달한다.
package com.example.partner;

import org.springframework.web.client.RestTemplate;

public class PassportDtoClient {

    private final RestTemplate restTemplate;

    public PassportDtoClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String passportNumber) {
        PartnerPassportRequest request = new PartnerPassportRequest();
        request.setPassportNumber(passportNumber);
        restTemplate.postForEntity(
            "http://partner.example.com/passports",
            request,
            Void.class
        );
    }
}
