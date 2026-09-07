// pipa-fixture-expect-warn: K-ENC-002/unsalted-hash
// SHA-256은 일방향이므로 제7조 제1항 단서의 "복호화되지 아니하도록"은 충족한다.
// 그러나 salt도 반복도 없는 단순 해시는 "안전한 암호 알고리즘"으로 보기 어렵다.
// 구조만으로 확정할 수 없는 판단(내부 용도의 무결성 해시일 수도 있다)이므로 차단하지
// 않고 경고만 한다. high로 올라가면 harness가 실패한다. (D-03)
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public class MemberPasswordDigest {

    public String digest(String rawPassword) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] out = md.digest(rawPassword.getBytes(StandardCharsets.UTF_8));
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
