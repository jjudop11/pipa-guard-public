// pipa-fixture-expect: K-ENC-001/plaintext-sized-column
// Kotlin 엔티티가 신용카드번호를 원문 크기의 문자열 컬럼에 그대로 저장한다.
package com.example.payment

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id

@Entity
class PaymentCard {
    @Id
    var id: Long = 0

    @field:Column(name = "credit_card_no", nullable = false, length = 19)
    var creditCardNo: String = ""
}
