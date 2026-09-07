// pipa-fixture-expect-warn: K-LEAK-002/unverified-api-output-purpose
// pipa-fixture-config: {"outputPolicies":[{"sink":"api","source":"V059_IncompleteApiOutputPolicy.java#profile","purpose":"회원 이름 조회","allowedItems":["fullName"]}]}
// evidence가 빠진 출력 정책은 차단 근거로 인정하지 않고 경고한다.
package com.example.member;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

record MemberNameResponse(String fullName) {}

@RestController
public class MemberNameController {

    @GetMapping("/members/name")
    public MemberNameResponse profile() {
        return new MemberNameResponse("synthetic-name");
    }
}
