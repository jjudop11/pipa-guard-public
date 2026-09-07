// pipa-fixture-expect-clean
// 개인정보 필드가 있는 DTO와 무관한 요청 DTO를 바인딩하면 개인정보 수신으로 전파되면 안 된다.
package com.example.health;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

class MemberRequest {
    private String fullName;
}

class HealthRequest {
    private String probeId;
}

@RestController
public class HealthCheckController {

    @PostMapping("/health/check")
    public void check(@RequestBody HealthRequest request) {
        // 확인 생략
    }
}
