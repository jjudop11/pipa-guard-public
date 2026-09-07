// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// OpenFeign 프록시가 사용자 휴대전화번호 원문을 외부 평문 HTTP로 실제 호출한다.
package com.example.member;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@FeignClient(name = "memberPartner", url = "http://partner.example.com")
interface MemberPartnerClient {
    @PostMapping("/members/mobile")
    void send(@RequestBody String userMobilePhoneNumber);
}

public class FeignMemberService {

    private final MemberPartnerClient client;

    public FeignMemberService(MemberPartnerClient client) {
        this.client = client;
    }

    public void send(String userMobilePhoneNumber) {
        client.send(userMobilePhoneNumber);
    }
}
