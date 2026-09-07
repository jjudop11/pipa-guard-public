// pipa-fixture-expect-clean
// pipa-fixture-config: {"outputPolicies":[{"sink":"api","source":"C078_AllowedSpringApiResponse.java#profile","purpose":"회원 본인의 프로필 조회","allowedItems":["fullName","emailAddress"],"evidence":"docs/privacy/self-profile.md"}]}
// 응답 DTO의 개인정보 항목이 명시된 출력 용도와 허용 범위 안에 있다.
package com.example.member;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

class SelfProfileResponse {
    private String fullName;
    private String emailAddress;
}

@RestController
public class SelfProfileController {

    @GetMapping("/me/profile")
    public SelfProfileResponse profile() {
        return new SelfProfileResponse();
    }
}
