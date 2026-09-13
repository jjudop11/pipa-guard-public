// pipa-fixture-expect: K-ENC-002/two-way
// C098과 같은 보조 메서드의 암호 처리 인자 자리에 비밀번호를 전달하면 차단한다.
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import java.util.Base64;

class SelectedPasswordArgument {
    private SecretKey key;
    private String password;

    public void store(String rawPassword) throws Exception {
        this.password = this.wrap("합성 표시명", rawPassword);
    }

    String wrap(String unused, String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key);
        byte[] encrypted = cipher.doFinal(plaintext.getBytes());
        return Base64.getEncoder().encodeToString(encrypted);
    }
}
