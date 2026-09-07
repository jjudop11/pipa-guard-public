// pipa-fixture-expect-clean
// Spring HTTP Service 프록시가 성명 원문을 HTTPS endpoint로 전송한다.
package com.example.member;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.annotation.PostExchange;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

interface SecureMemberService {
    @PostExchange("/members")
    void send(@RequestBody String fullName);
}

public class SecureSpringHttpServiceClient {

    public void send(String fullName) {
        RestClient restClient = RestClient.builder()
            .baseUrl("https://partner.example.com")
            .build();
        HttpServiceProxyFactory factory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(restClient))
            .build();
        SecureMemberService client =
            factory.createClient(SecureMemberService.class);
        client.send(fullName);
    }
}
