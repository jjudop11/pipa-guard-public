// pipa-fixture-expect-warn: K-LEAK-002/unverified-api-output-purpose
// pipa-fixture-config: {"outputPolicies":[{"sink":"api","source":"V062_DuplicateApiOutputPolicy.java#profile","purpose":"회원 이름 조회","allowedItems":["fullName"],"evidence":"docs/privacy/member-name.md"},{"sink":"api","source":"V062_DuplicateApiOutputPolicy.java#profile","purpose":"회원 프로필 조회","allowedItems":["fullName","emailAddress"],"evidence":"docs/privacy/member-profile.md"}]}
// 같은 파일#메서드에 중복된 정책은 넓은 허용 근거로 선택하지 않고 경고한다.
package com.example.member;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

record MemberProfileResponse(String fullName, String emailAddress) {}

@RestController
public class MemberProfileController {

    @GetMapping("/members/profile")
    public MemberProfileResponse profile() {
        return new MemberProfileResponse("synthetic-name", "synthetic@example.test");
    }
}
