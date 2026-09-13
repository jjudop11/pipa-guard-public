// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// Kotlin Retrofit suspend 함수가 성명 원문을 외부 평문 HTTP로 실제 호출한다.
package com.example.member

import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.POST

interface KotlinMemberApi {
    @POST("members")
    suspend fun send(@Body fullName: String)
}

class KotlinRetrofitMemberClient {
    suspend fun send(fullName: String) {
        val retrofit = Retrofit.Builder()
            .baseUrl("http://partner.example.com/")
            .build()
        val api = retrofit.create(KotlinMemberApi::class.java)
        api.send(fullName)
    }
}
