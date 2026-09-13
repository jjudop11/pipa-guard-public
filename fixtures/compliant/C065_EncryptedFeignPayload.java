// pipa-fixture-expect-clean
// 외부 평문 HTTP Feign 호출이어도 실제 AES-GCM 암호화 결과만 전달한다.
package com.example.member;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@FeignClient(name = "memberPartner", url = "http://partner.example.com")
interface EncryptedMemberPartnerClient {
    @PostMapping("/members")
    void send(@RequestBody String encryptedFullName);
}

public class EncryptedFeignMemberService {

    private final EncryptedMemberPartnerClient client;
    private final AesGcmEncryptor encryptor;

    public EncryptedFeignMemberService(
        EncryptedMemberPartnerClient client,
        AesGcmEncryptor encryptor
    ) {
        this.client = client;
        this.encryptor = encryptor;
    }

    public void send(String fullName) {
        String encryptedFullName = encryptor.encrypt(fullName);
        client.send(encryptedFullName);
    }
}
