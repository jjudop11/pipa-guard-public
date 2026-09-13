// 주석 안의 위반 코드는 검출하지 않는다. 주석 제거가 동작하는지 확인하는 fixture다.
package com.example.member;

import org.springframework.security.crypto.password.PasswordEncoder;

public class MemberMigrationService {

    private final PasswordEncoder passwordEncoder;

    public MemberMigrationService(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
    }

    /*
     * 과거 구현. 아래처럼 AES로 저장하고 있었다.
     *
     * Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
     * this.password = new String(cipher.doFinal(rawPassword.getBytes()));
     */
    public String migrate(String rawPassword) {
        // return aesUtil.encrypt(rawPassword);
        return passwordEncoder.encode(rawPassword);
    }
}
