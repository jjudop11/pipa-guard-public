// pipa-fixture-expect: K-ENC-002/two-way
// Jasypt StandardPBEStringEncryptor는 양방향 암호화다. 제7조 제1항 단서 위반.
package com.example.member;

import org.jasypt.encryption.pbe.StandardPBEStringEncryptor;
import org.springframework.stereotype.Service;

@Service
public class MemberRegisterService {

    private final StandardPBEStringEncryptor encryptor;
    private final MemberRepository memberRepository;

    public MemberRegisterService(StandardPBEStringEncryptor encryptor,
                                 MemberRepository memberRepository) {
        this.encryptor = encryptor;
        this.memberRepository = memberRepository;
    }

    public void register(String loginId, String rawPassword) {
        String stored = encryptor.encrypt(rawPassword);
        memberRepository.save(new Member(loginId, stored));
    }
}
