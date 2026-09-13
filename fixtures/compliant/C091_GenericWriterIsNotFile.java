// pipa-fixture-expect-clean
// pipa-fixture-config: {"localStoragePolicies":[{"source":"C091_GenericWriterIsNotFile.java#render","target":"workstation","evidence":"docs/privacy/operator-render.md"}]}
// 일반 객체의 write()는 명시적 파일 저장 sink가 아니다.
package com.example.render;

public class ReportRenderer {
    public void render(ReportWriter writer, String passportNumber) {
        writer.write(passportNumber);
    }
}
