// pipa-fixture-expect-clean
// 파일에 JDK HttpClient 타입이 있어도 일반 작업 실행기의 execute()를 네트워크 sink로 보면 안 된다.
package com.example.batch;

import java.net.http.HttpClient;

public class PassportBatchJob {

    private final HttpClient healthCheckClient = HttpClient.newHttpClient();
    private final TaskExecutor executor;

    public PassportBatchJob(TaskExecutor executor) {
        this.executor = executor;
    }

    public void run(String passportNumber) {
        executor.execute(passportNumber);
    }
}
