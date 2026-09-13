// pipa-fixture-expect-clean
// 결제 API 공개 규격에 따라 시스템 시크릿 키를 Basic 인증용으로 Base64 인코딩한다.
package com.example.payment;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

record PaymentProviderProperties(String secretKey) {
}

public class C093_PaymentProviderBasicAuthCredential {
    private final PaymentProviderProperties properties;

    public C093_PaymentProviderBasicAuthCredential(PaymentProviderProperties properties) {
        this.properties = properties;
    }

    public String basicAuthorization() {
        String credential = properties.secretKey() + ":";
        String encoded = Base64.getEncoder().encodeToString(credential.getBytes(StandardCharsets.UTF_8));
        return "Basic " + encoded;
    }
}
