// pipa-fixture-expect-warn: K-ENC-001/unprotected-column
// 여권번호 영속 컬럼에 @Convert·@ColumnTransformer가 보이지 않는다. 다만 다른 계층에서
// 암호화한 값을 넣을 가능성을 이 파일만으로 배제할 수 없으므로 차단하지 않고 경고한다.
package com.example.identity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class PassportRecord {

    @Id
    private Long id;

    @Column(name = "passport_no", nullable = false, length = 255)
    private String passportNumber;
}
