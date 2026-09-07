// pipa-fixture-expect-warn: K-ENC-003/unprotected-column
// pipa-fixture-config: {"subjectType":"non_user","storageZone":"internal","riskAssessment":null}
// 내부망의 운전면허번호이고 적용범위를 줄인 평가 결과가 없다. 암호화 연결이 보이지 않지만
// 다른 계층에서 암호화했을 가능성은 남으므로 경고로만 나와야 한다.
package com.example.contractor;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class ContractorLicense {

    @Id
    private Long id;

    @Column(name = "driver_license_no", length = 255)
    private String driverLicenseNumber;
}
