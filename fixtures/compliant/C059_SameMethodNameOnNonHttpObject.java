// pipa-fixture-expect-clean
// Feign 계약과 같은 send() 이름이어도 수신자 타입이 다른 일반 객체 호출은 HTTP sink가 아니다.
package com.example.audit;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@FeignClient(name = "memberPartner", url = "http://partner.example.com")
interface MemberPartnerContract {
    @PostMapping("/members")
    void send(@RequestBody String fullName);
}

public class LocalAuditService {

    private final AuditWriter client;

    public LocalAuditService(AuditWriter client) {
        this.client = client;
    }

    public void record(String fullName) {
        client.send(fullName);
    }
}
