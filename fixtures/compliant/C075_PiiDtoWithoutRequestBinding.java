// pipa-fixture-expect-clean
// 개인정보 DTO와 endpoint가 같은 파일에 있어도 DTO가 요청 인자로 바인딩되지 않으면 수신하지 않는다.
package com.example.member;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

record MemberRequest(String fullName) {}

@RestController
public class MemberStatusController {

    @GetMapping("/members/status")
    public String status() {
        return "ok";
    }
}
