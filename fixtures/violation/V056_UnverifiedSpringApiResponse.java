// pipa-fixture-expect-warn: K-LEAK-002/unverified-api-output-purpose
// 개인정보 응답은 보이지만 출력 용도와 허용 항목의 근거가 없다.
package com.example.member;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class MemberEmailController {
    private String userEmailAddress;

    @GetMapping("/members/email")
    public String email() {
        return userEmailAddress;
    }
}
