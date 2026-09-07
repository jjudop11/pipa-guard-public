// pipa-fixture-expect-warn: K-ENC-004/unverified-server-receive-tls
// pipa-fixture-config: {"inboundTransport":{"exposure":"internet","tlsTermination":"trusted_proxy","httpsOnly":true}}
// 신뢰 프록시라고 주장하지만 근거가 없어 TLS 보호를 확정할 수 없다.
package com.example.member;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

record MobileRequest(String userMobilePhoneNumber) {}

@RestController
public class IncompleteIngressController {

    @PostMapping("/members/mobile")
    public void register(@RequestBody MobileRequest request) {
        // 등록 생략
    }
}
