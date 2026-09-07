// pipa-fixture-expect: K-ENC-005/plaintext-device-storage
// pipa-fixture-config: {"subjectType":"non_user","localStoragePolicies":[{"source":"V067_RemovablePlaintextKotlin.kt#backupTemplate","target":"removable_media","evidence":"docs/privacy/offline-backup.md"}]}
// 이용자가 아닌 정보주체의 생체인식정보를 보조저장매체 파일에 원문으로 저장한다.
package com.example.backup

import java.io.File

class BiometricBackupService {
    fun backupTemplate(destination: String, biometricTemplate: ByteArray) {
        val backupFile = File(destination)
        backupFile.writeBytes(biometricTemplate)
    }
}
