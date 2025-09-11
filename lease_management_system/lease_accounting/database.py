"""
数据库扩展模块 - 创建核算相关表
"""
import sqlite3
from utils.logging import get_logger

logger = get_logger("DatabaseExtension")


def init_extended_db(db):
    """初始化核算模块数据库表"""
    try:
        if not hasattr(db, '_is_connected') or not db._is_connected:
            db.connect()

        # 1. 月度收入表（存储会计/税法口径不含税收入）
        db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            accounting_income REAL DEFAULT 0.0,  -- 会计不含税收入
            tax_income REAL DEFAULT 0.0,         -- 税法不含税收入
            tax_rate REAL NOT NULL,              -- 适用税率（如0.05）
            is_adjust INTEGER NOT NULL,          -- 1=需调整收入，0=无需调整
            calculate_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE,
            UNIQUE(contract_id, year, month)     -- 同一合同每月仅一条记录
        )
        ''')

        # 2. 收入记录表
        db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS income_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT NOT NULL,
            income_date DATE NOT NULL,  -- 收入确认日期
            accounting_income REAL NOT NULL,  -- 会计收入
            tax_income REAL NOT NULL,         -- 税法收入
            source_type TEXT NOT NULL,  -- 来源：monthly（月度自动）/manual（手动调整）
            source_id INTEGER,          -- 关联月度收入表ID
            is_invoiced INTEGER DEFAULT 0,  -- 是否已开票
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
        )
        ''')

        # 3. 增值税记录表（收款/开票/应收孰早原则）
        db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS vat_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT NOT NULL,
            relate_type TEXT NOT NULL,  -- 触发类型：receivable(应收)/payment(收款)/invoice(开票)/overpaid/overpaid_reverse
            relate_id TEXT NOT NULL,    -- 关联ID（UUID或对应表ID）
            vat_amount REAL NOT NULL,   -- 增值税额（保留2位小数）
            tax_obligation_date DATE NOT NULL,  -- 纳税义务日期（孰早）
            status TEXT NOT NULL DEFAULT 'pending',  -- pending=待缴，paid=已缴
            payment_date DATE,          -- 实际缴税日期（可为NULL）
            remark TEXT,                -- 备注
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
        )
        ''')

        # 4. 税会差异表（含递延所得税和待转销项税额）
        db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tax_diff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            accounting_income REAL NOT NULL,  -- 会计不含税收入
            tax_income REAL NOT NULL,         -- 税法不含税收入
            diff_amount REAL NOT NULL,        -- 税会差异（会计-税法）
            deferred_tax REAL NOT NULL,       -- 递延所得税（差异×25%）
            to_be_settled_vat REAL NOT NULL,  -- 待转销项税额（会计收入×税率）
            adjust_vat REAL NOT NULL,         -- 冲减待转销项税额（税法收入×税率）
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE,
            UNIQUE(contract_id, year, month)
        )
        ''')

        # 5. 开票详情表（扩展原有开票记录，增加关联字段）
        db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,  -- 发票号（唯一，避免重复开票）
            contract_id TEXT NOT NULL,
            invoice_date DATE NOT NULL,          -- 开票日期
            total_amount REAL NOT NULL,          -- 发票含税总金额
            vat_amount REAL NOT NULL,            -- 发票增值税额
            relate_payment_id INTEGER,           -- 关联收款记录ID（关联payment_records.id）
            relate_income_year INTEGER,          -- 关联收入年份（如2025）
            relate_income_month INTEGER,         -- 关联收入月份（如6）
            status TEXT NOT NULL DEFAULT 'valid', -- valid=有效，invalid=红冲
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE,
            FOREIGN KEY (relate_payment_id) REFERENCES payment_records(id) ON DELETE SET NULL
        )
        ''')

        # 6. 押金明细表（区分应付/实付，补充原有押金记录）
        db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposit_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT NOT NULL,
            planned_deposit REAL NOT NULL,  -- 应付押金（合同约定金额）
            actual_deposit REAL NOT NULL,   -- 实付押金（实际收取金额）
            deposit_date DATE,              -- 实付押金日期（可为NULL）
            remark TEXT,                    -- 备注（如"2025-06-10银行转账"）
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE,
            UNIQUE(contract_id)  -- 一个合同仅一条押金明细
        )
        ''')

        # 创建唯一索引
        db.cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_vat_unique 
        ON vat_records (contract_id, relate_type, relate_id, tax_obligation_date)
        ''')

        db.conn.commit()
        logger.info("✅ 核算模块数据库表创建/验证成功")
        
    except sqlite3.Error as e:
        if db.conn:
            db.conn.rollback()
        logger.error(f"❌ 扩展数据库失败：{str(e)}")
        raise Exception(f"核算模块数据库初始化失败：{str(e)}")
