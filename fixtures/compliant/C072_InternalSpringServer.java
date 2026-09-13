// pipa-fixture-expect-clean
// pipa-fixture-config: {"inboundTransport":{"exposure":"internal","tlsTermination":"none","httpsOnly":false,"evidence":"deploy/network-policy.yaml"}}
// 인터넷망에 노출되지 않는 내부 endpoint는 제7조 제4항의 인터넷망 구간 범위가 아니다.
package com.example.member;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class InternalMemberController {

    @PostMapping("/internal/members")
    public void register(@RequestParam String passportNumber) {
        // 등록 생략
    }
}
