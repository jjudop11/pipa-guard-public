// 같은 클래스에 비밀번호 일방향 해시와 주민등록번호 양방향 암호화가 함께 있어도
// 각각 적법하다. 비밀번호는 제7조 제1항 단서, 주민등록번호는 제7조 제2항 제1호다.
// 알고리즘 변수 전파가 무관한 문장으로 새어 나가지 않는지 확인하는 fixture다.
package com.example.member;

import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.security.crypto.password.PasswordEncoder;

public class MemberSecurityService {

    private final PasswordEncoder passwordEncoder;
    private final SecretKeySpec residentNumberKey;

    public MemberSecurityService(PasswordEncoder passwordEncoder, SecretKeySpec residentNumberKey) {
        this.passwordEncoder = passwordEncoder;
        this.residentNumberKey = residentNumberKey;
    }

    public String encodePassword(String rawPassword) {
        return passwordEncoder.encode(rawPassword);
    }

    public boolean verifyPassword(String rawPassword, String encodedPassword) {
        return passwordEncoder.matches(rawPassword, encodedPassword);
    }

    // 주민등록번호는 복호화가 필요한 항목이므로 양방향 암호화가 적법하다.
    public byte[] encryptResidentNumber(String residentNumber) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, residentNumberKey);
        return cipher.doFinal(residentNumber.getBytes("UTF-8"));
    }
}
