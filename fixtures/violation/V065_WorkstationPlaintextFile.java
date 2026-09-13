// pipa-fixture-expect: K-ENC-005/plaintext-device-storage
// pipa-fixture-config: {"localStoragePolicies":[{"source":"V065_WorkstationPlaintextFile.java#exportProfile","target":"workstation","evidence":"docs/privacy/operator-export.md"}]}
// 개인정보취급자 컴퓨터에서 이용자 성명을 파일에 원문으로 저장한다.
package com.example.export;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class ProfileExportService {
    public void exportProfile(Path destination, String fullName) throws IOException {
        Files.writeString(destination, fullName);
    }
}
