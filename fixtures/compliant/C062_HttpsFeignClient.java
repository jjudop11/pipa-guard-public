// pipa-fixture-expect-clean
// OpenFeign 프록시가 사용자 휴대전화번호 원문을 HTTPS endpoint로 전송한다.
package com.example.member;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@FeignClient(name = "memberPartner", url = "https://partner.example.com")
interface SecureMemberPartnerClient {
    @PostMapping("/members/mobile")
    void send(@RequestBody String userMobilePhoneNumber);
}

public class SecureFeignMemberService {

    private final SecureMemberPartnerClient client;

    public SecureFeignMemberService(SecureMemberPartnerClient client) {
        this.client = client;
    }

    public void send(String userMobilePhoneNumber) {
        client.send(userMobilePhoneNumber);
    }
}
