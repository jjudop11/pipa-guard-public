// pipa-fixture-expect-warn: K-ENC-005/unverified-device-storage-target
// pipa-fixture-config: {"localStoragePolicies":[{"source":"V069_IncompleteFileWriterPolicy.java#exportName","target":"workstation"}]}
// FileWriter 저장 위치는 선언했지만 실제 배포·운영 근거 evidence가 없다.
package com.example.export;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class NameExportService {
    public void exportName(File destination, String fullName) throws IOException {
        try (FileWriter writer = new FileWriter(destination)) {
            writer.write(fullName);
        }
    }
}
