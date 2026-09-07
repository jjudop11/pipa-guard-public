// pipa-fixture-expect-clean
// PIN은 게임문화상품권 번호로도 쓰인다. 인증 문맥이 없는 giftCardPin은 비밀번호로 단정하지 않는다.
package com.example.giftcard;

import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;

public class GiftCardPinTokenService {

    public byte[] protectGiftCardPin(String giftCardPin, byte[] key) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"));
        return cipher.doFinal(giftCardPin.getBytes(StandardCharsets.UTF_8));
    }
}
