// pipa-fixture-expect-clean
// 비밀번호가 호출 인자에 있어도 암호 처리에 사용되지 않는 자리이면 전파하지 않는다.
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import java.util.Base64;

class UnusedPasswordArgument {
    private SecretKey key;

    public String process(String rawPassword, String residentNumber) throws Exception {
        return this.wrap(rawPassword, residentNumber);
    }

    private String wrap(String unused, String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key);
        byte[] encrypted = cipher.doFinal(plaintext.getBytes());
        return Base64.getEncoder().encodeToString(encrypted);
    }
}
