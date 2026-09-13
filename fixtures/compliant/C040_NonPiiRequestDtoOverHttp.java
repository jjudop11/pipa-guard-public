// pipa-fixture-expect-clean
// 개인정보 후보가 아닌 주문번호만 요청 DTO에 담아 외부 HTTP로 전송한다.
package com.example.order;

import org.springframework.web.client.RestTemplate;

public class OrderDtoClient {

    private final RestTemplate restTemplate;

    public OrderDtoClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String orderNo) {
        OrderStatusRequest request = new OrderStatusRequest(orderNo);
        restTemplate.postForEntity(
            "http://partner.example.com/orders",
            request,
            Void.class
        );
    }
}
