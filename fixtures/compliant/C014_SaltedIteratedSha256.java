// pipa-fixture-expect-clean
// V010과 같은 SHA-256 해시지만 salt가 digest 수신자에 입력되고 같은 메서드에서
// 반복 처리된다. 경고 0건까지 고정하는 방어선이다.
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;

public class MemberPasswordHasher {

    private static final int ITERATIONS = 100000;

    private final SecureRandom random = new SecureRandom();

    public byte[] newSalt() {
        byte[] salt = new byte[32];
        random.nextBytes(salt);
        return salt;
    }

    public String hash(String rawPassword, byte[] salt) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        md.update(salt);
        byte[] out = md.digest(rawPassword.getBytes(StandardCharsets.UTF_8));
        for (int i = 1; i < ITERATIONS; i++) {
            md.update(salt);
            out = md.digest(out);
        }
        return toHex(out);
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
