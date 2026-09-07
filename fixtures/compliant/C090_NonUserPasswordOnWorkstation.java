// pipa-fixture-expect-clean
// pipa-fixture-config: {"subjectType":"non_user","localStoragePolicies":[{"source":"C090_NonUserPasswordOnWorkstation.java#writeMigrationValue","target":"workstation","evidence":"docs/privacy/non-user-migration.md"}]}
// 제7조 제5항의 비이용자 범위는 고유식별정보와 생체인식정보이며 이 이름은 인증 처리도 아니다.
package com.example.migration;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class NonUserMigrationService {
    public void writeMigrationValue(Path destination, String password) throws IOException {
        Files.writeString(destination, password);
    }
}
