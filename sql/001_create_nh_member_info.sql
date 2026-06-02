-- NH MDM: 조합원 인사 테이블
-- PostgreSQL 13+ (gen_random_uuid() 내장)

CREATE SCHEMA IF NOT EXISTS nh;

CREATE TABLE IF NOT EXISTS nh.nh_member_info (
    nh_member_id      VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::text,  -- 랜덤 PK
    nh_member_name    VARCHAR(50)  NOT NULL,                                     -- 성명
    nh_member_ssn     VARCHAR(12)  NOT NULL UNIQUE,                              -- 실명번호 (ex. 123456-1234567)
    nh_customer_no    VARCHAR(12)  NOT NULL UNIQUE,                              -- 고객번호
    nh_member_phone   VARCHAR(13)  NOT NULL,                                     -- 핸드폰 (ex. 010-1234-5678)
    is_active         VARCHAR(1)   NOT NULL DEFAULT 'Y',                         -- 유지 여부 (Y: 사용, N: 미사용)
    CONSTRAINT chk_nh_member_info_is_active CHECK (is_active IN ('Y', 'N'))
);

COMMENT ON TABLE nh.nh_member_info IS '조합원 인사';
COMMENT ON COLUMN nh.nh_member_info.nh_member_id IS '랜덤 PK';
COMMENT ON COLUMN nh.nh_member_info.nh_member_name IS '성명';
COMMENT ON COLUMN nh.nh_member_info.nh_member_ssn IS '실명번호 (ex. 123456-1234567)';
COMMENT ON COLUMN nh.nh_member_info.nh_customer_no IS '고객번호';
COMMENT ON COLUMN nh.nh_member_info.nh_member_phone IS '핸드폰 (ex. 010-1234-5678)';
COMMENT ON COLUMN nh.nh_member_info.is_active IS '유지 여부 (Y: 사용, N: 미사용)';
