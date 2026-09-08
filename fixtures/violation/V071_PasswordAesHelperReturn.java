// pipa-fixture-expect: K-ENC-002/two-way
// 실제 모델이 자주 만드는 형태다. AES 적용과 비밀번호 저장이 보조 메서드 경계를 사이에 두고,
// 암호문을 Base64 문자열로 바꿔 반환해도 복호화 가능한 비밀번호 저장이라는 사실은 변하지 않는다.
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class Member {
    private static final byte[] KEY = new byte[16];
    private static final byte[] IV = new byte[16];

    private String encryptedPassword;

    public Member(String rawPassword) throws Exception {
        this.encryptedPassword = encrypt(rawPassword);
    }

    private String encrypt(String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
        cipher.init(Cipher.ENCRYPT_MODE,
                new SecretKeySpec(KEY, "AES"), new IvParameterSpec(IV));
        byte[] encrypted = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(encrypted);
    }
}
