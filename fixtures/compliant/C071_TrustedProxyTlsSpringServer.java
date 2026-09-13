// pipa-fixture-expect-clean
// pipa-fixture-config: {"inboundTransport":{"exposure":"internet","tlsTermination":"trusted_proxy","httpsOnly":true,"evidence":"deploy/k8s/member-ingress.yaml"}}
// 신뢰하는 경계 프록시가 외부 HTTPS만 받고 애플리케이션에는 내부 HTTP로 전달한다.
package com.example.member;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

record MemberRequest(String fullName) {}

@RestController
public class ProxiedMemberController {

    @PostMapping("/members")
    public void register(@RequestBody MemberRequest request) {
        // 등록 생략
    }
}
