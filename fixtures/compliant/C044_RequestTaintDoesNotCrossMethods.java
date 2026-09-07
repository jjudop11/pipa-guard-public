// pipa-fixture-expect-clean
// 첫 메서드의 개인정보 DTO 지역 변수명 request가 두 번째 메서드의 비개인정보 request로 새면 안 된다.
package com.example.mixed;

import org.springframework.web.client.RestTemplate;

public class ScopedRequestClient {

    private final RestTemplate restTemplate;

    public ScopedRequestClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public PartnerIdentityRequest buildIdentity(String residentRegistrationNumber) {
        PartnerIdentityRequest request =
            new PartnerIdentityRequest(residentRegistrationNumber);
        return request;
    }

    public void sendOrder(String orderNo) {
        OrderStatusRequest request = new OrderStatusRequest(orderNo);
        restTemplate.postForEntity(
            "http://partner.example.com/orders",
            request,
            Void.class
        );
    }
}
