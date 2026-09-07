// pipa-fixture-expect-clean
// endpoint 스킴은 이 파일에서 알 수 없지만 암호화 결과만 네트워크 sink에 전달한다.
package com.example.contractor;

import org.springframework.web.client.RestTemplate;

public class EncryptedLicenseClient {

    private final RestTemplate restTemplate;
    private final AesGcmEncryptor encryptor;
    private final String endpoint;

    public EncryptedLicenseClient(
            RestTemplate restTemplate,
            AesGcmEncryptor encryptor,
            String endpoint) {
        this.restTemplate = restTemplate;
        this.encryptor = encryptor;
        this.endpoint = endpoint;
    }

    public void send(String driverLicenseNumber) {
        String encryptedDriverLicenseNumber = encryptor.encrypt(driverLicenseNumber);
        restTemplate.postForEntity(endpoint, encryptedDriverLicenseNumber, Void.class);
    }
}
