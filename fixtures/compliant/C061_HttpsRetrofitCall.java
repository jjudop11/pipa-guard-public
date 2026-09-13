// pipa-fixture-expect-clean
// Retrofit Call이 사용자 이메일 주소 원문을 HTTPS endpoint로 전송한다.
package com.example.member;

import java.io.IOException;
import retrofit2.Call;
import retrofit2.Retrofit;
import retrofit2.http.Body;
import retrofit2.http.POST;

interface SecureMemberApi {
    @POST("members")
    Call<Void> send(@Body String userEmailAddress);
}

public class SecureRetrofitMemberClient {

    public void send(String userEmailAddress) throws IOException {
        Retrofit retrofit = new Retrofit.Builder()
            .baseUrl("https://partner.example.com/")
            .build();
        SecureMemberApi api = retrofit.create(SecureMemberApi.class);
        api.send(userEmailAddress).execute();
    }
}
