// pipa-fixture-expect-clean
// pipa-fixture-config: {"localStoragePolicies":[{"source":"C089_EncryptedWorkstationFile.java#exportResident","target":"workstation","evidence":"docs/privacy/operator-export.md"}]}
// 이용자 주민등록번호는 실제 암호화 결과만 개인정보취급자 컴퓨터의 파일에 저장한다.
package com.example.export;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class EncryptedResidentExportService {
    private final AesGcmEncryptor encryptor;

    public EncryptedResidentExportService(AesGcmEncryptor encryptor) {
        this.encryptor = encryptor;
    }

    public void exportResident(Path destination, String residentRegistrationNumber)
            throws IOException {
        String encryptedResidentRegistrationNumber =
                encryptor.encrypt(residentRegistrationNumber);
        Files.writeString(destination, encryptedResidentRegistrationNumber);
    }
}
