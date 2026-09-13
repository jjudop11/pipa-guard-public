// pipa-fixture-expect-clean
// TLS 경계를 알 수 없어도 개인정보 요청을 받지 않는 endpoint는 제7조 제4항 판정 대상이 아니다.
package com.example.health;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    @GetMapping("/health")
    public String health(@RequestParam String probeId) {
        return "ok";
    }
}
