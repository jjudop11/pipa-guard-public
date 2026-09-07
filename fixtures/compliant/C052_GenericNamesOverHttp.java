// pipa-fixture-expect-clean
// name만으로는 사람의 성명인지 알 수 없으며 코드·파일·화면의 이름은 개인정보 후보가 아니다.
package com.example.metadata;

import org.springframework.web.client.RestTemplate;

public class MetadataClient {

    private final RestTemplate restTemplate;

    public MetadataClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String name, String className, String fileName, String displayName) {
        String metadata = name + className + fileName + displayName;
        restTemplate.postForEntity(
            "http://partner.example.com/metadata",
            metadata,
            Void.class
        );
    }
}
