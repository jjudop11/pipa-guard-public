// pipa-fixture-expect: K-ENC-004/plaintext-server-receive
// pipa-fixture-config: {"inboundTransport":{"exposure":"internet","tlsTermination":"none","httpsOnly":false,"evidence":"deploy/public-http.md"}}
// Kotlin 요청 DTO의 사용자 이메일 주소가 외부 평문 수신 endpoint에 도달한다.
package com.example.member

import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

data class MemberRequest(val userEmailAddress: String)

@RestController
class KotlinMemberController {

    @PostMapping("/members")
    fun register(@RequestBody request: MemberRequest) {
        // 등록 생략
    }
}
