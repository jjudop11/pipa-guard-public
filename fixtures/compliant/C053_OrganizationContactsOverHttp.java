// pipa-fixture-expect-clean
// 회사 대표 이메일 주소와 사무실 전화번호는 살아 있는 개인의 연락처라고 확정할 수 없다.
package com.example.organization;

import org.springframework.web.client.RestTemplate;

public class OrganizationContactClient {

    private final RestTemplate restTemplate;

    public OrganizationContactClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String companyEmailAddress, String officePhoneNumber) {
        OrganizationContact request =
            new OrganizationContact(companyEmailAddress, officePhoneNumber);
        restTemplate.postForEntity(
            "http://partner.example.com/organizations",
            request,
            Void.class
        );
    }
}
