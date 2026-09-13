// pipa-fixture-expect-warn: K-ENC-004/tls-verification-disabled
// HTTPS를 쓰지만 NoopHostnameVerifier를 연결한 클라이언트로 주민등록번호를 전송한다.
// 파일 단위 연결만으로 해당 인스턴스 사용을 완전히 증명할 수 없어 경고로 고정한다.
package com.example.legacy;

import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.ssl.NoopHostnameVerifier;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

public class InsecureHttpsIdentityClient {

    private final RestTemplate restTemplate;

    public InsecureHttpsIdentityClient() {
        CloseableHttpClient httpClient = HttpClients.custom()
            .setSSLHostnameVerifier(NoopHostnameVerifier.INSTANCE)
            .build();
        HttpComponentsClientHttpRequestFactory factory =
            new HttpComponentsClientHttpRequestFactory(httpClient);
        this.restTemplate = new RestTemplate(factory);
    }

    public void send(String residentRegistrationNumber) {
        restTemplate.postForEntity(
            "https://partner.example.com/member-identities",
            residentRegistrationNumber,
            Void.class
        );
    }
}
