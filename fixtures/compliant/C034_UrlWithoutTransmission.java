// pipa-fixture-expect-clean
// 외부 HTTP URL과 여권번호 형식 검사가 같은 파일에 있어도 실제 네트워크 sink가 없다.
package com.example.validation;

public class PassportLinkValidator {

    private static final String HELP_URL = "http://help.example.com/passports";

    public boolean valid(String passportNumber) {
        return passportNumber != null && passportNumber.length() >= 8;
    }

    public String helpUrl() {
        return HELP_URL;
    }
}
