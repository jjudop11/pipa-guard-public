// pipa-fixture-expect-clean
// 비밀번호 확인 입력 검증이다. 저장값과의 비교가 아니므로 평문 저장 신호가 아니다.
// equals() 사용만으로 검출해서는 안 된다. plaintext-compare가 경고로도 나오면 안 되므로
// 경고 0건까지 고정한다. 위반 쪽 대응 fixture는 V011이다.
package com.example.member;

public class PasswordChangeRequest {

    private final String rawPassword;
    private final String confirmPassword;

    public PasswordChangeRequest(String rawPassword, String confirmPassword) {
        this.rawPassword = rawPassword;
        this.confirmPassword = confirmPassword;
    }

    public void validate() {
        if (!rawPassword.equals(confirmPassword)) {
            throw new IllegalArgumentException("비밀번호 확인이 일치하지 않습니다.");
        }
    }
}
