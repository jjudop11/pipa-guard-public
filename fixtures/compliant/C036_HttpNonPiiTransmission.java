// pipa-fixture-expect-clean
// 외부 평문 HTTP 호출이어도 전달값이 사전의 개인정보 후보가 아니면 이 규칙의 대상이 아니다.
package com.example.order;

import org.springframework.web.client.RestTemplate;

public class OrderStatusClient {

    private final RestTemplate restTemplate;

    public OrderStatusClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String orderNo) {
        restTemplate.postForEntity(
            "http://partner.example.com/orders",
            orderNo,
            Void.class
        );
    }
}
