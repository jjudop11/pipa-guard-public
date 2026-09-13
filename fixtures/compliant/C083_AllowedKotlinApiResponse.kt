// pipa-fixture-expect-clean
// pipa-fixture-config: {"outputPolicies":[{"sink":"api","source":"C083_AllowedKotlinApiResponse.kt#profile","purpose":"회원 본인의 연락처 조회","allowedItems":["emailAddress","mobilePhoneNumber"],"evidence":"docs/privacy/self-contact.md"}]}
// Kotlin 응답 DTO도 명시한 출력 허용 범위 안이면 통과한다.
package com.example.member

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController

data class SelfContactResponse(
    val userEmailAddress: String,
    val userMobilePhoneNumber: String,
)

@RestController
class SelfContactController {

    @GetMapping("/me/contact")
    fun profile(): SelfContactResponse =
        SelfContactResponse("synthetic@example.test", "000-0000-0000")
}
