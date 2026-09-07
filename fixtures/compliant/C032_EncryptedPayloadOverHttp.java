// pipa-fixture-expect-clean
// 외부 HTTP 구간이지만 여권번호를 실제 AES-GCM 암호화한 결과만 전송한다.
package com.example.partner;

import org.springframework.web.client.RestTemplate;

public class EncryptedPassportPartnerClient {

    private final RestTemplate restTemplate;
    private final AesGcmEncryptor encryptor;

    public EncryptedPassportPartnerClient(RestTemplate restTemplate, AesGcmEncryptor encryptor) {
        this.restTemplate = restTemplate;
        this.encryptor = encryptor;
    }

    public void send(String passportNumber) {
        String encryptedPassportNumber = encryptor.encrypt(passportNumber);
        restTemplate.postForEntity(
            "http://partner.example.com/passports",
            encryptedPassportNumber,
            Void.class
        );
    }
}
