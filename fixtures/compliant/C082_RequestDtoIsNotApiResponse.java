// pipa-fixture-expect-clean
// pipa-fixture-config: {"inboundTransport":{"exposure":"internet","tlsTermination":"application","httpsOnly":true,"evidence":"config/application.yml"},"outputPolicies":[{"sink":"api","source":"C082_RequestDtoIsNotApiResponse.java#register","purpose":"회원 등록 결과 확인","allowedItems":[],"evidence":"docs/privacy/member-register.md"}]}
// 요청 DTO의 개인정보를 응답 DTO 항목으로 잘못 전파하면 안 된다.
package com.example.member;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

class PassportRegistrationRequest {
    private String passportNumber;
}

@RestController
public class PassportRegistrationController {

    @PostMapping("/members")
    public String register(@RequestBody PassportRegistrationRequest request) {
        return "registered";
    }
}
