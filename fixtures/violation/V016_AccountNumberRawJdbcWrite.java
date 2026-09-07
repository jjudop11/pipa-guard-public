// pipa-fixture-expect-warn: K-ENC-001/plaintext-sql-write
// accountNo는 은행 계좌번호가 아니라 회계 계정번호일 수 있는 weak 별칭이다. SQL 쓰기
// 구조가 있어도 의미를 확정할 수 없으므로 high로 차단하지 않고 경고만 해야 한다.
package com.example.settlement;

import org.springframework.jdbc.core.JdbcTemplate;

public class SettlementJdbcRepository {

    private final JdbcTemplate jdbcTemplate;

    public SettlementJdbcRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public void insert(Long settlementId, String accountNo) {
        jdbcTemplate.update(
            "INSERT INTO settlement_account (settlement_id, account_no) VALUES (?, ?)",
            settlementId,
            accountNo
        );
    }
}
