// pipa-fixture-expect: K-ENC-004/plaintext-server-receive
// pipa-fixture-config: {"inboundTransport":{"exposure":"internet","tlsTermination":"none","httpsOnly":false,"evidence":"deploy/public-http.md"}}
// 외부 인터넷망 endpoint가 성명 원문을 TLS 없이 수신한다고 명시했다.
package com.example.member;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PublicMemberController {

    @PostMapping("/members")
    public void register(@RequestParam String fullName) {
        // 등록 생략
    }
}
