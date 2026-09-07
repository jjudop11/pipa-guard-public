// pipa-fixture-expect-clean
// Kotlin JPA use-site target(@field:)로 제7조 제2항 항목에 암호화 컨버터를 연결한다.
// Java의 @Convert만 인식하고 Kotlin의 @field:Convert를 놓치면 적법 코드를 차단하게 된다.
package com.example.identity

import com.example.support.AesGcmStringConverter
import jakarta.persistence.Column
import jakarta.persistence.Convert
import jakarta.persistence.Entity
import jakarta.persistence.Id

@Entity
class EncryptedIdentity(
    @Id
    val id: Long,

    @field:Convert(converter = AesGcmStringConverter::class)
    @field:Column(name = "resident_reg_no_enc", length = 512)
    val residentRegistrationNumber: String,

    @field:Convert(converter = AesGcmStringConverter::class)
    @field:Column(name = "credit_card_no_enc", length = 512)
    val creditCardNo: String,
)
