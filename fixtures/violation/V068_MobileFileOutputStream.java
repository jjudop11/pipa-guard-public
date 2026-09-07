// pipa-fixture-expect: K-ENC-005/plaintext-device-storage
// pipa-fixture-config: {"localStoragePolicies":[{"source":"V068_MobileFileOutputStream.java#cacheContact","target":"mobile","evidence":"docs/privacy/mobile-offline-cache.md"}]}
// 모바일 기기에서 이용자 이메일 주소를 FileOutputStream에 원문으로 저장한다.
package com.example.mobile;

import static java.nio.charset.StandardCharsets.UTF_8;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

public class OfflineContactCache {
    public void cacheContact(File destination, String userEmailAddress) throws IOException {
        try (FileOutputStream output = new FileOutputStream(destination)) {
            output.write(userEmailAddress.getBytes(UTF_8));
        }
    }
}
