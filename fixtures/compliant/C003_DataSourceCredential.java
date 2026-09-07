// DB 접속 계정 비밀번호는 제2조 제8호의 "비밀번호"가 아니다. 정보주체나 개인정보취급자가
// 접속 시 입력하는 인증 문자열이 아니라 애플리케이션의 시스템 크리덴셜이므로 양방향
// 암호화가 불가피하고 제7조 제1항 단서의 대상이 아니다. 검출하지 않아야 한다.
package com.example.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class DataSourceCredentialProvider {

    @Value("${spring.datasource.password}")
    private String dbPassword;

    private final AesUtil aesUtil;

    public DataSourceCredentialProvider(AesUtil aesUtil) {
        this.aesUtil = aesUtil;
    }

    public String resolvePassword() {
        return aesUtil.decrypt(dbPassword);
    }
}
