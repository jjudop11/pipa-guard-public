// 억제 지시자가 동작하는지 확인하는 fixture다. 이유 없는 억제는 무시된다.
package com.example.legacy;

import javax.crypto.Cipher;

public class LegacyBridge {

    // pipa-guard:ignore K-ENC-002 2026-12-31까지 유지되는 구 시스템 연동 어댑터. 신규 저장 경로 아님. 티켓 SEC-412
    public String bridgePassword(String rawPassword, Cipher cipher) throws Exception {
        return new String(cipher.doFinal(rawPassword.getBytes("UTF-8")));
    }
}
