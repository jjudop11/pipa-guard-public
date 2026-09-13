// pipa-fixture-expect-clean
// setter 이름에 passportNumber가 있어도 실제 인자는 암호화된 값이므로 DTO를 오염시키면 안 된다.
package com.example.partner;

import org.springframework.web.client.RestTemplate;

public class EncryptedPassportSetterClient {

    private final RestTemplate restTemplate;
    private final AesGcmEncryptor encryptor;

    public EncryptedPassportSetterClient(RestTemplate restTemplate, AesGcmEncryptor encryptor) {
        this.restTemplate = restTemplate;
        this.encryptor = encryptor;
    }

    public void send(String passportNumber) {
        String encryptedPassportNumber = encryptor.encrypt(passportNumber);
        PartnerPassportRequest request = new PartnerPassportRequest();
        request.setPassportNumber(encryptedPassportNumber);
        restTemplate.postForEntity(
            "http://partner.example.com/passports",
            request,
            Void.class
        );
    }
}
