// pipa-fixture-expect-clean
// 개인정보 이름의 메서드가 있어도 Spring 요청 매핑과 요청 바인딩이 없으면 수신 endpoint가 아니다.
package com.example.member;

public class LocalMemberFormatter {

    public String normalizeFullName(String fullName) {
        return fullName.trim();
    }
}
