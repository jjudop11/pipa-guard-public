// pipa-fixture-expect: K-ENC-002/two-way
// 알고리즘 선택과 적용이 서로 다른 문장에 있는 형태다. 문장 하나만 보면 어느 쪽도
// 위반으로 보이지 않지만, 합치면 비밀번호를 복호화 가능한 방식으로 처리하고 있다.
package com.example.member;

import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

public class PasswordVault {

    public byte[] seal(String rawPassword, SecretKeySpec key) throws Exception {
        Cipher aes = Cipher.getInstance("AES/CBC/PKCS5Padding");
        aes.init(Cipher.ENCRYPT_MODE, key);
        aes.update(rawPassword.getBytes("UTF-8"));
        return aes.doFinal();
    }
}
