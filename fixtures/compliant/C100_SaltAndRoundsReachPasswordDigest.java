// pipa-fixture-expect-clean
// SHA-256을 직접 사용하지만 salt가 실제 digest 수신자에 입력되고 같은 메서드의 반복
// 라운드에서 결과를 다시 해시한다. 파일 전체의 단어가 아니라 이 흐름을 근거로 통과한다.
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public class SaltedRepeatedPasswordDigest {

    private static final int ROUNDS = 120000;

    public String hash(String rawPassword, byte[] salt) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        md.update(salt);
        byte[] out = md.digest(rawPassword.getBytes(StandardCharsets.UTF_8));
        for (int round = 1; round < ROUNDS; round++) {
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
