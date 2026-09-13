// pipa-fixture-expect-clean
// 외부 HTTP 선언만 있고 프록시 생성·실제 호출이 없으므로 송신을 단정하지 않는다.
package com.example.contract;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.service.annotation.PostExchange;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.POST;

@FeignClient(name = "memberPartner", url = "http://partner.example.com")
interface UnusedFeignClient {
    @PostMapping("/members")
    void send(@RequestBody String fullName);
}

interface UnusedSpringService {
    @PostExchange("http://partner.example.com/members")
    void send(@RequestBody String fullName);
}

interface UnusedRetrofitApi {
    @POST("http://partner.example.com/members")
    Call<Void> send(@Body String fullName);
}
