// pipa-fixture-expect: K-ENC-002/encoding-not-encryption
// 시스템 시크릿 키가 같은 문장에 있어도 정보주체의 비밀번호 Base64 인코딩은 제외하지 않는다.
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

record PaymentProviderProperties(String secretKey) {
}

public class V070_UserPasswordMixedWithSecretKeyBase64 {
    public String encodePassword(String password, PaymentProviderProperties properties) {
        return Base64.getEncoder().encodeToString(
                (password + properties.secretKey()).getBytes(StandardCharsets.UTF_8)
        );
    }
}
