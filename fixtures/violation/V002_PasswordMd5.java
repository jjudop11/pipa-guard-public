// pipa-fixture-expect: K-ENC-002/weak-hash
// 일방향이지만 MD5는 "안전한 암호 알고리즘"이 아니다. 제7조 제1항 단서 위반.
package com.example.member;

import org.apache.commons.codec.digest.DigestUtils;

public class LegacyPasswordService {

    public String encodePassword(String rawPassword) {
        return DigestUtils.md5Hex(rawPassword);
    }
}
