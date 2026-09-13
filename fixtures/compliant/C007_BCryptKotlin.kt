// Kotlin. BCryptPasswordEncoder로 일방향 해시한다. 제7조 제1항 단서를 충족한다.
package com.example.member

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
import org.springframework.stereotype.Service

@Service
class MemberSignUpService(
    private val passwordEncoder: BCryptPasswordEncoder,
    private val memberRepository: MemberRepository,
) {
    fun signUp(loginId: String, rawPassword: String) {
        val encoded = passwordEncoder.encode(rawPassword)
        memberRepository.save(Member(loginId = loginId, password = encoded))
    }
}
