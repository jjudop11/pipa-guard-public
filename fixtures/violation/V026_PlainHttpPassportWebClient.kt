// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// Kotlin WebClient 체인에서 여권번호 원문을 외부 평문 HTTP 구간으로 전송한다.
package com.example.partner

import org.springframework.web.reactive.function.client.WebClient

class PassportPartnerClient(private val webClient: WebClient) {

    fun send(passportNumber: String) {
        webClient.post()
            .uri("http://partner.example.com/passports")
            .bodyValue(passportNumber)
            .retrieve()
            .toBodilessEntity()
            .block()
    }
}
