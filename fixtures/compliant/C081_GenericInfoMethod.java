// pipa-fixture-expect-clean
// Logger 문맥이 없는 일반 객체의 info 메서드는 로그 출력 sink가 아니다.
package com.example.metrics;

public class MetricsService {
    private final MetricsRecorder metrics = new MetricsRecorder();

    public void record(String fullName) {
        metrics.info(fullName);
    }
}
