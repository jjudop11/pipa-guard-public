// pipa-fixture-expect-clean
// Retrofit의 Call 객체를 만들기만 하고 execute/enqueue하지 않아 아직 송신되지 않는다.
package com.example.member;

import retrofit2.Call;
import retrofit2.Retrofit;
import retrofit2.http.Body;
import retrofit2.http.POST;

interface DeferredMemberApi {
    @POST("members")
    Call<Void> send(@Body String fullName);
}

public class DeferredRetrofitMemberClient {

    public Call<Void> prepare(String fullName) {
        Retrofit retrofit = new Retrofit.Builder()
            .baseUrl("http://partner.example.com/")
            .build();
        DeferredMemberApi api = retrofit.create(DeferredMemberApi.class);
        return api.send(fullName);
    }
}
