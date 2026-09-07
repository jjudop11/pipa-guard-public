// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// Spring HTTP Service 프록시가 성명 원문을 외부 평문 HTTP로 실제 호출한다.
package com.example.member;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.annotation.PostExchange;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

interface MemberService {
    @PostExchange("/members")
    void send(@RequestBody String fullName);
}

public class SpringHttpServiceClient {

    public void send(String fullName) {
        RestClient restClient = RestClient.builder()
            .baseUrl("http://partner.example.com")
            .build();
        HttpServiceProxyFactory factory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(restClient))
            .build();
        MemberService client = factory.createClient(MemberService.class);
        client.send(fullName);
    }
}
