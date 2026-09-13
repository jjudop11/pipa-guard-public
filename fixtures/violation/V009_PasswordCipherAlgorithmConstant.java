// pipa-fixture-expect: K-ENC-002/two-way
// 양방향 암호에서도 같은 간접 참조가 성립한다.
//   TRANSFORMATION = "AES/GCM/NoPadding"  →  Cipher.getInstance(TRANSFORMATION)
//   →  newCipher()  →  cipher.doFinal(rawPassword)
// 비밀번호는 복호화되지 아니하도록 저장해야 하므로 제7조 제1항 단서 위반이다.
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class MemberPasswordVault {

    private static final String TRANSFORMATION = "AES/GCM/NoPadding";
    private static final int TAG_LENGTH_BIT = 128;

    private final SecretKeySpec key;
    private final byte[] iv;

    public MemberPasswordVault(SecretKeySpec key, byte[] iv) {
        this.key = key;
        this.iv = iv;
    }

    public String store(String rawPassword) throws Exception {
        Cipher cipher = newCipher();
        cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(TAG_LENGTH_BIT, iv));
        byte[] sealed = cipher.doFinal(rawPassword.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(sealed);
    }

    private static Cipher newCipher() throws Exception {
        return Cipher.getInstance(TRANSFORMATION);
    }
}
