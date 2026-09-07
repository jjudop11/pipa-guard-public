// pipa-fixture-expect-clean
// V026과 같은 Kotlin WebClient 줄바꿈 체인이지만 endpoint가 HTTPS이므로 통과해야 한다.
package com.example.partner

import org.springframework.web.reactive.function.client.WebClient

class SecurePassportPartnerClient(private val webClient: WebClient) {

    fun send(passportNumber: String) {
        webClient.post()
            .uri("https://partner.example.com/passports")
            .bodyValue(passportNumber)
            .retrieve()
            .toBodilessEntity()
            .block()
    }
}
