// 제7조 제1항 단서를 충족한다. PasswordEncoder로 일방향 해시하고 matches()로 검증한다.
package com.example.member;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class MemberPasswordService {

    private final PasswordEncoder passwordEncoder;
    private final MemberRepository memberRepository;

    public MemberPasswordService(PasswordEncoder passwordEncoder,
                                 MemberRepository memberRepository) {
        this.passwordEncoder = passwordEncoder;
        this.memberRepository = memberRepository;
    }

    public void changePassword(Long memberId, String rawPassword) {
        Member member = memberRepository.findById(memberId).orElseThrow();
        member.applyPassword(passwordEncoder.encode(rawPassword));
    }

    public boolean authenticate(Member member, String rawPassword) {
        return passwordEncoder.matches(rawPassword, member.getPassword());
    }
}
