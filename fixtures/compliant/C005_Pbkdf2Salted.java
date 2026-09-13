// PBKDF2 + salt + 반복 횟수. 일방향이고 안전한 알고리즘이므로 제7조 제1항 단서를 충족한다.
package com.example.member;

import java.security.spec.KeySpec;
import java.util.Base64;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

public class PasswordHasher {

    private static final int ITERATIONS = 210000;
    private static final int KEY_LENGTH = 256;

    public String hash(String rawPassword, byte[] salt) throws Exception {
        SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        KeySpec spec = new PBEKeySpec(rawPassword.toCharArray(), salt, ITERATIONS, KEY_LENGTH);
        byte[] derived = factory.generateSecret(spec).getEncoded();
        return Base64.getEncoder().encodeToString(derived);
    }
}
