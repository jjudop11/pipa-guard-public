// pipa-fixture-expect: K-ENC-002/two-way
// 비밀번호를 AES로 양방향 암호화하여 엔티티에 저장한다. 제7조 제1항 단서 위반.
package com.example.member;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

@Entity
public class Member {

    @Id
    private Long id;

    @Column(name = "login_id", nullable = false)
    private String loginId;

    @Column(name = "password", nullable = false, length = 256)
    private String password;

    public void changePassword(String rawPassword, byte[] key) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"));
        this.password = new String(cipher.doFinal(rawPassword.getBytes()));
    }
}
