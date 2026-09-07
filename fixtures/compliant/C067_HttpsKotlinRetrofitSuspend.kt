// pipa-fixture-expect-clean
// Kotlin Retrofit suspend 함수가 성명 원문을 HTTPS endpoint로 전송한다.
package com.example.member

import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.POST

interface SecureKotlinMemberApi {
    @POST("members")
    suspend fun send(@Body fullName: String)
}

class SecureKotlinRetrofitMemberClient {
    suspend fun send(fullName: String) {
        val retrofit = Retrofit.Builder()
            .baseUrl("https://partner.example.com/")
            .build()
        val api = retrofit.create(SecureKotlinMemberApi::class.java)
        api.send(fullName)
    }
}
