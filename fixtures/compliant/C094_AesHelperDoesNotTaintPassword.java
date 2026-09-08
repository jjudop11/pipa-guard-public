// pipa-fixture-expect-clean
// AES 보조 메서드가 같은 파일에 있어도 주민등록번호에만 적용되고 비밀번호는 PasswordEncoder로
// 처리한다면 비밀번호 양방향 암호화로 판정하면 안 된다.
package com.example.member;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.security.crypto.password.PasswordEncoder;

public class MemberSecurityService {
    private final PasswordEncoder passwordEncoder;
    private final SecretKeySpec residentNumberKey;

    public MemberSecurityService(
            PasswordEncoder passwordEncoder, SecretKeySpec residentNumberKey) {
        this.passwordEncoder = passwordEncoder;
        this.residentNumberKey = residentNumberKey;
    }

    public String encodePassword(String rawPassword) {
        return passwordEncoder.encode(rawPassword);
    }

    public String encryptResidentNumber(String residentNumber) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, residentNumberKey);
        byte[] encrypted = cipher.doFinal(residentNumber.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(encrypted);
    }
}
