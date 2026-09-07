// pipa-fixture-expect-warn: K-LEAK-002/unverified-api-output-purpose
// pipa-fixture-config: {"outputPolicies":[{"sink":"api","source":"V061_UnknownApiOutputPolicyItem.java#profile","purpose":"회원 이름 조회","allowedItems":["full_name"],"evidence":"docs/privacy/member-profile.md"}]}
// 사전에 없는 allowedItems 오타는 허용 근거로 인정하지 않고 경고한다.
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
