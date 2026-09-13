// 같은 클래스에 SHA-1 팩토리와 비밀번호 저장이 함께 있다.
// SHA-1은 첨부파일 무결성 체크섬용이고 개인정보에 닿지 않는다. 비밀번호는 BCrypt다.
// 상수·팩토리 전파가 "파일 안에 SHA-1이 있다"는 이유로 비밀번호 문장까지 물들이면
// 이 fixture가 깨진다. 새 전파의 오탐 방어선이다.
package com.example.attachment;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

import org.springframework.security.crypto.password.PasswordEncoder;

public class AttachmentService {

    private static final String CHECKSUM_ALGORITHM = "SHA-1";

    private final PasswordEncoder passwordEncoder;

    public AttachmentService(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
    }

    // 첨부파일 무결성 확인용 체크섬. 개인정보가 아니다.
    public byte[] checksum(Path path) throws IOException, NoSuchAlgorithmException {
        MessageDigest digest = newChecksumDigest();
        return digest.digest(Files.readAllBytes(path));
    }

    private static MessageDigest newChecksumDigest() throws NoSuchAlgorithmException {
        return MessageDigest.getInstance(CHECKSUM_ALGORITHM);
    }

    // 비밀번호는 일방향 해시로 저장한다. 위 SHA-1과 무관하다.
    public String encodePassword(String rawPassword) {
        return passwordEncoder.encode(rawPassword);
    }

    public boolean verifyPassword(String rawPassword, String storedPassword) {
        return passwordEncoder.matches(rawPassword, storedPassword);
    }
}
