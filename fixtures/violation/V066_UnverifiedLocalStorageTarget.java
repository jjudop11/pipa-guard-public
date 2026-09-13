// pipa-fixture-expect-warn: K-ENC-005/unverified-device-storage-target
// 파일 저장 sink와 이용자 여권번호는 확인되지만 실행·저장 위치 정책이 없다.
package com.example.export;

import static java.nio.charset.StandardCharsets.UTF_8;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class PassportExportService {
    public void exportPassport(Path destination, String passportNumber) throws IOException {
        Files.write(destination, passportNumber.getBytes(UTF_8));
    }
}
