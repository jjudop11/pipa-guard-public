// pipa-fixture-expect-clean
// 제7조 제2항 항목명이 있더라도 영속화 sink에 도달하지 않는다. 메서드 안에서 요청값의
// 형식만 확인하고 반환한다. K-ENC-001은 이름만 보고 저장 위반으로 판정해서는 안 된다.
package com.example.identity;

public class IdentityVerificationInputValidator {

    public boolean hasSupportedFormat(String residentRegistrationNumber,
                                      String passportNumber) {
        boolean residentFormat = residentRegistrationNumber.matches("[0-9-]+");
        boolean passportFormat = !passportNumber.isBlank();
        return residentFormat && passportFormat;
    }
}
