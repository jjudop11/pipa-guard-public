// pipa-fixture-expect-clean
// pipa-fixture-config: {"localStoragePolicies":[{"source":"C092_OneWayPasswordWorkstationFile.java#exportCredential","target":"workstation","evidence":"docs/privacy/operator-credential-export.md"}]}
// 이용자 비밀번호는 PasswordEncoder의 일방향 결과만 개인정보취급자 컴퓨터에 저장한다.
package com.example.export;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.springframework.security.crypto.password.PasswordEncoder;

public class CredentialExportService {
    private final PasswordEncoder passwordEncoder;

    public CredentialExportService(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
    }

    public void exportCredential(Path destination, String password) throws IOException {
        String encodedPassword = passwordEncoder.encode(password);
        Files.writeString(destination, encodedPassword);
    }
}
