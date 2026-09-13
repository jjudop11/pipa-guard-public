// pipa-fixture-expect: K-ENC-002/weak-hash
// 실제 헤드리스 세션이 생성한 코드에서 온 fixture다. V006과 위반 내용은 같지만
// 알고리즘 리터럴이 상수에 들어가고 인스턴스는 팩토리 메서드가 만든다.
//   ALGORITHM = "SHA-1"  →  getInstance(ALGORITHM)  →  newDigest()  →  md.digest(rawLoginPin)
// 두 겹의 간접 참조 때문에 초기 엔진은 이 형태를 놓쳤다. 미검출 회귀 방어선이다.
// salt를 붙였더라도 SHA-1 자체가 '안전한 암호 알고리즘'이 아니므로 위반이다.
package com.example.payment.pin;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Base64;

public class PinService {

    private static final String ALGORITHM = "SHA-1";
    private static final int SALT_LENGTH = 16;

    private final SecureRandom secureRandom = new SecureRandom();

    public String hash(String rawLoginPin) {
        byte[] salt = new byte[SALT_LENGTH];
        secureRandom.nextBytes(salt);
        byte[] hashed = digest(rawLoginPin, salt);
        Base64.Encoder encoder = Base64.getEncoder();
        return encoder.encodeToString(salt) + "$" + encoder.encodeToString(hashed);
    }

    private byte[] digest(String rawLoginPin, byte[] salt) {
        MessageDigest md = newDigest();
        md.update(salt);
        return md.digest(rawLoginPin.getBytes(StandardCharsets.UTF_8));
    }

    private static MessageDigest newDigest() {
        try {
            return MessageDigest.getInstance(ALGORITHM);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(ALGORITHM + " 알고리즘을 사용할 수 없습니다.", e);
        }
    }
}
