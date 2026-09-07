// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// Retrofit Call이 사용자 이메일 주소 원문을 외부 평문 HTTP로 실행한다.
package com.example.member;

import java.io.IOException;
import retrofit2.Call;
import retrofit2.Retrofit;
import retrofit2.http.Body;
import retrofit2.http.POST;

interface MemberApi {
    @POST("members")
    Call<Void> send(@Body String userEmailAddress);
}

public class RetrofitMemberClient {

    public void send(String userEmailAddress) throws IOException {
        Retrofit retrofit = new Retrofit.Builder()
            .baseUrl("http://partner.example.com/")
            .build();
        MemberApi api = retrofit.create(MemberApi.class);
        api.send(userEmailAddress).execute();
    }
}
