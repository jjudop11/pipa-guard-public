// pipa-fixture-expect-clean
// 생체인식정보는 제2조 제11호의 인증정보이므로 제7조 제1항 본문의 암호화 대상이고,
// 제7조 제2항 제7호에도 열거되어 있다. 그러나 제1항 단서의 "복호화되지 아니하도록
// 일방향 암호화"는 "비밀번호를 저장하는 경우"만 규율한다. 지문 템플릿을 AES-GCM으로
// 암호화해 저장하는 것은 적법하며 K-ENC-002의 대상이 아니다.
//
// 사전 분류(category)로 대상을 고르면 생체인식정보가 authentication에 걸려 여기가
// 오탐이 된다. 엔진은 encryption == one_way_only 로 고른다. 이 파일이 그 방어선이다.
package com.example.biometric;

import java.util.Base64;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class FingerprintTemplateStore {

    private static final String TRANSFORMATION = "AES/GCM/NoPadding";
    private static final int TAG_LENGTH_BIT = 128;

    private final SecretKeySpec key;
    private final byte[] iv;

    public FingerprintTemplateStore(SecretKeySpec key, byte[] iv) {
        this.key = key;
        this.iv = iv;
    }

    public String seal(byte[] fingerprintTemplate) throws Exception {
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(TAG_LENGTH_BIT, iv));
        return Base64.getEncoder().encodeToString(cipher.doFinal(fingerprintTemplate));
    }

    public byte[] unseal(String sealed) throws Exception {
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(TAG_LENGTH_BIT, iv));
        return cipher.doFinal(Base64.getDecoder().decode(sealed));
    }
}
