// pipa-fixture-expect: K-ENC-002/two-way
// Kotlin에서도 문자열 이름은 해시가 아니며 this 보조 호출의 인자 흐름을 검사한다.
import javax.crypto.Cipher
import javax.crypto.SecretKey
import java.util.Base64

class KotlinCryptoSafeMarker(private val key: SecretKey) {
    private var password: String = ""

    fun store(rawPassword: String) {
        this.password = this.wrap(rawPassword) + "Argon2"
    }

    private fun wrap(plaintext: String): String {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key)
        val encrypted = cipher.doFinal(plaintext.toByteArray())
        return Base64.getEncoder().encodeToString(encrypted)
    }
}
