// pipa-fixture-expect-warn: K-ENC-002/plaintext-compare
// 저장된 비밀번호를 입력값과 equals()로 직접 비교한다. 저장값이 평문이라는 뜻이므로
// 제7조 제1항 단서 위반이다. 다만 확인 입력 검증(C008)과 구조가 같아서 구별할 수
// 없으므로 차단하지 않고 경고만 한다. high로 올라가면 harness가 실패한다. (D-03)
package com.example.auth;

public class LegacyLoginService {

    private final MemberRepository members;

    public LegacyLoginService(MemberRepository members) {
        this.members = members;
    }

    public boolean login(String loginId, String inputPassword) {
        Member found = members.findByLoginId(loginId);
        if (found == null) {
            return false;
        }
        return found.getPassword().equals(inputPassword);
    }
}
