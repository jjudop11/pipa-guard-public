// pipa-fixture-expect: K-ENC-002/encoding-not-encryption
// Base64는 인코딩이며 암호화가 아니다. 누구나 원문으로 되돌릴 수 있다.
package com.example.member

import java.util.Base64

class MemberAccount(
    val loginId: String,
    rawPassword: String,
) {
    val password: String = Base64.getEncoder().encodeToString(rawPassword.toByteArray())
}
