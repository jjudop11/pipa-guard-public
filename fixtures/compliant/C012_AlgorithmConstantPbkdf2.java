// 알고리즘 이름을 상수에 담고 팩토리 메서드로 인스턴스를 만드는 형태다.
// V008과 구조가 같지만 상수 값이 PBKDF2이므로 제7조 제1항 단서를 충족한다.
// 상수·팩토리 전파가 알고리즘 종류를 무시하고 발동하면 이 fixture가 깨진다.
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.spec.InvalidKeySpecException;
import java.util.Base64;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

public class PasswordKdfService {

    private static final String ALGORITHM = "PBKDF2WithHmacSHA256";
    private static final int ITERATIONS = 210_000;
    private static final int KEY_LENGTH = 256;
    private static final int SALT_LENGTH = 16;

    private final SecureRandom secureRandom = new SecureRandom();

    public String hash(String rawPassword) throws Exception {
        byte[] salt = new byte[SALT_LENGTH];
        secureRandom.nextBytes(salt);
        byte[] derived = derive(rawPassword, salt);
        Base64.Encoder encoder = Base64.getEncoder();
        return encoder.encodeToString(salt) + "$" + encoder.encodeToString(derived);
    }

    private byte[] derive(String rawPassword, byte[] salt)
            throws InvalidKeySpecException, NoSuchAlgorithmException {
        SecretKeyFactory factory = newFactory();
        PBEKeySpec spec = new PBEKeySpec(
                rawPassword.toCharArray(), salt, ITERATIONS, KEY_LENGTH);
        return factory.generateSecret(spec).getEncoded();
    }

    private static SecretKeyFactory newFactory() throws NoSuchAlgorithmException {
        return SecretKeyFactory.getInstance(ALGORITHM);
    }

    public byte[] fingerprint(String rawPassword) throws Exception {
        // 문자열 인코딩만 한다. 저장 경로가 아니다.
        return rawPassword.getBytes(StandardCharsets.UTF_8);
    }
}
