// pipa-fixture-expect-clean
// Feign 필드와 이름이 같은 지역 일반 객체가 가려진 경우 지역 send()를 HTTP 호출로 보지 않는다.
package com.example.audit;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@FeignClient(name = "memberPartner", url = "http://partner.example.com")
interface ShadowedMemberClient {
    @PostMapping("/members")
    void send(@RequestBody String fullName);
}

public class ShadowedAuditService {

    private final ShadowedMemberClient client;

    public ShadowedAuditService(ShadowedMemberClient client) {
        this.client = client;
    }

    public void writeLocally(String fullName) {
        AuditWriter client = new AuditWriter();
        client.send(fullName);
    }
}
