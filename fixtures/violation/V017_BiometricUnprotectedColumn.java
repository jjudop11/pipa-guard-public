// pipa-fixture-expect-warn: K-ENC-001/unprotected-column
// 생체인식 템플릿 영속 컬럼에 암호화 연결이 보이지 않는다. 파일 밖의 저장 서비스에서
// 암호화할 가능성을 배제할 수 없으므로 경고로만 고정한다.
package com.example.biometric;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;

@Entity
public class BiometricCredential {

    @Id
    private Long id;

    @Lob
    @Column(name = "biometric_template", nullable = false)
    private byte[] biometricTemplate;
}
