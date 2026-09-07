// pipa-fixture-expect-clean
// V010과 같은 SHA-256 해시지만 salt와 반복 횟수가 있다. unsalted-hash 판정은 문장이
// 아니라 파일 단위로 salt/반복 신호를 보는데, 그 게이트가 없으면 이 파일이 경고로
// 새어 나온다. 경고 0건까지 고정하는 방어선이다.
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
