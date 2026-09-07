// pipa-fixture-expect-clean
// 제7조 제2항 항목을 AES-GCM으로 암호화한 뒤, 암호문을 별도 문장에서 저장한다.
// K-ENC-001은 저장 문장에 암호 API가 직접 보이지 않더라도 encrypted 변수까지의 얕은
// 값 전파를 따라 보호조치가 있음을 인정해야 한다. 파일에 암호화가 있다는 이유만으로
// 모든 저장을 적법하게 보는 것이 아니라 이 값의 경로만 연결해야 한다.
package com.example.identity;

public class PassportRegistrationService {

    private final AesGcmEncryptor encryptor;
    private final PassportRecordRepository repository;

    public PassportRegistrationService(AesGcmEncryptor encryptor,
                                       PassportRecordRepository repository) {
        this.encryptor = encryptor;
        this.repository = repository;
    }

    public void register(String passportNumber) {
        String encryptedPassportNumber = encryptor.encrypt(passportNumber);
        PassportRecord record = new PassportRecord(encryptedPassportNumber);
        repository.save(record);
    }
}
