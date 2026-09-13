// pipa-fixture-expect-clean
// pipa-fixture-config: {"inboundTransport":{"exposure":"internet","tlsTermination":"trusted_proxy","httpsOnly":true,"evidence":"deploy/k8s/member-ingress.yaml"}}
// 애플리케이션의 내부 HTTP connector만 보고 외부 평문 수신으로 오인하면 안 된다.
package com.example.member;

import org.apache.catalina.connector.Connector;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ProxiedEmbeddedController {

    public Connector internalConnector() {
        Connector connector = new Connector();
        connector.setScheme("http");
        connector.setSecure(false);
        connector.setPort(8080);
        return connector;
    }

    @PostMapping("/members")
    public void register(@RequestParam String fullName) {
        // 등록 생략
    }
}
