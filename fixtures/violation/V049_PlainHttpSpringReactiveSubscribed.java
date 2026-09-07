// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// Spring reactive HTTP Service 반환값을 block하여 외부 평문 HTTP 송신을 실행한다.
package com.example.member;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.annotation.PostExchange;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;
import reactor.core.publisher.Mono;

interface BlockingReactiveMemberService {
    @PostExchange("/members")
    Mono<Void> send(@RequestBody String fullName);
}

public class BlockingSpringHttpServiceClient {

    public void send(String fullName) {
        RestClient restClient = RestClient.builder()
            .baseUrl("http://partner.example.com")
            .build();
        HttpServiceProxyFactory factory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(restClient))
            .build();
        BlockingReactiveMemberService client =
            factory.createClient(BlockingReactiveMemberService.class);
        client.send(fullName).block();
    }
}
