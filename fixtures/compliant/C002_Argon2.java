// Argon2도 salt와 작업계수를 내장한 일방향 해시다. 제7조 제1항 단서를 충족한다.
package com.example.member;

import org.springframework.security.crypto.argon2.Argon2PasswordEncoder;

public class MemberCredential {

    private final String loginId;
    private String password;

    public MemberCredential(String loginId) {
        this.loginId = loginId;
    }

    public void applyPassword(String rawPassword) {
        Argon2PasswordEncoder encoder = Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8();
        this.password = encoder.encode(rawPassword);
    }

    public String getPassword() {
        return password;
    }
}
