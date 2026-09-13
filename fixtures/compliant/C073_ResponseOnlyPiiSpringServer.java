// pipa-fixture-expect-clean
// 응답 반환값의 개인정보 이름은 서버 수신 sink가 아니다. 응답 유출 규칙과 섞지 않는다.
package com.example.member;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class MemberResponseController {

    @GetMapping("/members/name")
    public String fullName() {
        return "synthetic-name";
    }
}
