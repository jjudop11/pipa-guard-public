// pipa-fixture-expect-warn: K-ENC-004/unverified-network-transmission
// Spring HTTP Service 프록시 호출은 보이지만 기반 클라이언트의 endpoint 스킴을 확인할 수 없다.
package com.example.member;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.annotation.PostExchange;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

interface UnknownMemberService {
    @PostExchange("/members")
    void send(@RequestBody String fullName);
}

public class UnknownSpringHttpServiceClient {

    public void send(String fullName) {
        RestClient restClient = RestClient.create();
        HttpServiceProxyFactory factory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(restClient))
            .build();
        UnknownMemberService client =
            factory.createClient(UnknownMemberService.class);
        client.send(fullName);
    }
}
