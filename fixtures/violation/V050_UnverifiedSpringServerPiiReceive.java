// pipa-fixture-expect-warn: K-ENC-004/unverified-server-receive-tls
// 개인정보 요청 endpoint는 보이지만 외부 수신 구간의 TLS 종단을 확인할 설정이 없다.
package com.example.member;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class MemberLookupController {

    @PostMapping("/members/lookup")
    public void lookup(@RequestParam String residentNumber) {
        // 조회 생략
    }
}
