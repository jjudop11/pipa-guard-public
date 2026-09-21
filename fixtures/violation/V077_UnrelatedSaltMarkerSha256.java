// pipa-fixture-expect-warn: K-ENC-002/unsalted-hash
// 비밀번호는 salt나 반복 없이 SHA-256으로 한 번만 해시한다. 파일의 무관한 salt·반복·
// BCrypt 라벨을 실제 비밀번호 해시의 보호조치로 인정하면 안 된다.
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public class PasswordDigestWithUnrelatedSaltLabel {

    private static final int ITERATIONS = 100000;
    private static final String ALGORITHM_LABEL = "BCrypt";

    public String digest(String rawPassword) throws Exception {
        String saltLabel = "salt";
        auditLabel(saltLabel, ALGORITHM_LABEL, ITERATIONS);

        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] out = md.digest(rawPassword.getBytes(StandardCharsets.UTF_8));
        return toHex(out);
    }

    private void auditLabel(String label, String algorithm, int iterations) {
        // 합성 fixture의 무관한 화면 라벨 사용을 나타낸다.
    }

    private static String toHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(Character.forDigit((b >> 4) & 0xF, 16));
            sb.append(Character.forDigit(b & 0xF, 16));
        }
        return sb.toString();
    }
}
