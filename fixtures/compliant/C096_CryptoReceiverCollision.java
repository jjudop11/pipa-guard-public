// pipa-fixture-expect-clean
// D-41: 독립 합성 검증에서 발견한 암호 보조 메서드 경계의 회귀 방어선.
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import java.util.Base64;
class ReceiverCollision {
    private SecretKey key;
    
    private String wrap(String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key);
        byte[] encrypted = cipher.doFinal(plaintext.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(encrypted);
    }
public boolean inspect(String rawPassword, Validator validator) {
        return validator.wrap(rawPassword);
    }
    static class Validator {
        public boolean wrap(String text) { return text.length() >= 12; }
    }
}
