// pipa-fixture-expect-clean
// 여권번호를 AES-GCM으로 암호화한 값만 요청 DTO에 담아 외부 HTTP로 전송한다.
package com.example.partner;

import org.springframework.web.client.RestTemplate;

public class EncryptedPassportDtoClient {

    private final RestTemplate restTemplate;
    private final AesGcmEncryptor encryptor;

    public EncryptedPassportDtoClient(RestTemplate restTemplate, AesGcmEncryptor encryptor) {
        this.restTemplate = restTemplate;
        this.encryptor = encryptor;
    }

    public void send(String passportNumber) {
        String encryptedPassportNumber = encryptor.encrypt(passportNumber);
        PartnerPassportRequest request =
            new PartnerPassportRequest(encryptedPassportNumber);
        restTemplate.postForEntity(
            "http://partner.example.com/passports",
            request,
            Void.class
        );
    }
}
