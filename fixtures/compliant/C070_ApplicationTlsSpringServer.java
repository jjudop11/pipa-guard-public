// pipa-fixture-expect-clean
// pipa-fixture-config: {"inboundTransport":{"exposure":"internet","tlsTermination":"application","httpsOnly":true,"evidence":"src/main/resources/application.properties"}}
// 애플리케이션 서버가 HTTPS 전용 TLS 종단임을 근거와 함께 선언했다.
package com.example.member;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class SecureMemberController {

    @PostMapping("/members")
    public void register(@RequestParam String residentNumber) {
        // 등록 생략
    }
}
