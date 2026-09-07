// pipa-fixture-expect-clean
// 개인정보가 아닌 응답에는 출력 정책을 요구하지 않는다.
package com.example.order;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

record OrderStatusResponse(String orderNo, String status) {}

@RestController
public class OrderStatusController {

    @GetMapping("/orders/status")
    public OrderStatusResponse status() {
        return new OrderStatusResponse("synthetic-order", "READY");
    }
}
