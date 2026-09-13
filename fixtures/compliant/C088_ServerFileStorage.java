// pipa-fixture-expect-clean
// pipa-fixture-config: {"localStoragePolicies":[{"source":"C088_ServerFileStorage.java#writeReport","target":"server","evidence":"deploy/report-service.yaml"}]}
// 서버 파일 저장은 제7조 제5항의 개인정보취급자 단말·보조저장매체 범위가 아니다.
package com.example.report;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class ServerReportService {
    public void writeReport(Path destination, String fullName) throws IOException {
        Files.writeString(destination, fullName);
    }
}
