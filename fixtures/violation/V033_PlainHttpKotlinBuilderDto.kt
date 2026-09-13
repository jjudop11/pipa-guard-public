// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 운전면허번호가 Kotlin builder 호출을 거쳐 요청 DTO에 들어가 외부 HTTP로 전송된다.
package com.example.contractor

import org.springframework.web.reactive.function.client.WebClient

class LicenseDtoClient(private val webClient: WebClient) {

    fun send(driverLicenseNumber: String) {
        val request = DriverLicenseRequest.builder()
            .driverLicenseNumber(driverLicenseNumber)
            .build()

        webClient.post()
            .uri("http://partner.example.com/licenses")
            .bodyValue(request)
            .retrieve()
            .toBodilessEntity()
            .block()
    }
}
