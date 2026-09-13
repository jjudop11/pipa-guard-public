// pipa-fixture-expect-clean
// reactive HTTP Service의 Mono를 만들기만 하고 구독하지 않아 아직 송신되지 않는다.
package com.example.member;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.annotation.PostExchange;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;
import reactor.core.publisher.Mono;

interface ReactiveMemberService {
    @PostExchange("/members")
    Mono<Void> send(@RequestBody String fullName);
}

public class DeferredSpringHttpServiceClient {

    public Mono<Void> prepare(String fullName) {
        RestClient restClient = RestClient.builder()
            .baseUrl("http://partner.example.com")
            .build();
        HttpServiceProxyFactory factory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(restClient))
            .build();
        ReactiveMemberService client =
            factory.createClient(ReactiveMemberService.class);
        return client.send(fullName);
    }
}
