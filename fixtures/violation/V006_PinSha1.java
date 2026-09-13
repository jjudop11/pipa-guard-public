// pipa-fixture-expect: K-ENC-002/weak-hash
// 간편결제 PIN도 제2조 제8호·제11호의 인증정보다. SHA-1은 안전한 알고리즘이 아니다.
package com.example.payment;

import java.security.MessageDigest;

public class SimplePinService {

    public String hashLoginPin(String rawLoginPin) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-1");
        byte[] result = digest.digest(rawLoginPin.getBytes("UTF-8"));
        return toHex(result);
    }

    private String toHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
