// pipa-fixture-expect: K-LEAK-002/excessive-api-response
// pipa-fixture-config: {"outputPolicies":[{"sink":"api","source":"V055_ExcessiveSpringApiResponse.java#profile","purpose":"회원 이름 조회","allowedItems":["fullName"],"evidence":"docs/privacy/member-profile.md"}]}
// 이름만 허용한 응답 정책에 여권번호까지 포함한 DTO를 반환한다.
package com.example.member;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

class MemberProfileResponse {
    private String fullName;
    private String passportNumber;
}

@RestController
public class MemberProfileController {

    @GetMapping("/members/profile")
    public MemberProfileResponse profile() {
        return new MemberProfileResponse();
    }
}
