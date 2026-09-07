// pipa-fixture-expect: K-ENC-004/plaintext-server-receive
// pipa-fixture-config: {"inboundTransport":{"exposure":"internet","tlsTermination":"none","httpsOnly":false,"evidence":"deploy/public-http.md"}}
// 일반 Java 요청 DTO의 여권번호 필드가 외부 평문 수신 endpoint에 도달한다.
package com.example.member;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

class PassportRequest {
    private String passportNumber;
}

@RestController
public class PassportController {

    @PostMapping("/members/passport")
    public void register(@RequestBody PassportRequest request) {
        // 등록 생략
    }
}
