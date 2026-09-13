// pipa-fixture-expect-clean
// 외부 평문 HTTP라도 요청에는 실제 AES-GCM 암호화 결과만 담는다.
package com.example.member;

import org.springframework.web.client.RestTemplate;

public class EncryptedMemberNameClient {

    private final RestTemplate restTemplate;
    private final AesGcmEncryptor encryptor;

    public EncryptedMemberNameClient(
        RestTemplate restTemplate,
        AesGcmEncryptor encryptor
    ) {
        this.restTemplate = restTemplate;
        this.encryptor = encryptor;
    }

    public void send(String fullName) {
        String encryptedFullName = encryptor.encrypt(fullName);
        restTemplate.postForEntity(
            "http://partner.example.com/member-names",
            encryptedFullName,
            Void.class
        );
    }
}
