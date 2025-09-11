"""
核心核算类 - 租赁合同会计与税法处理
"""
import datetime
import calendar
import uuid
from utils.logging import get_logger

logger = get_logger("LeaseAccounting")


class LeaseAccounting:
    """
    租赁合同核算核心类：接收lease_base的LeaseContract实例，实现核算逻辑
    不修改原有LeaseContract，通过组合模式复用基础数据
    """
    
    def __init__(self, contract, db):
        # 验证合同数据完整性
        if not hasattr(contract, "rent_periods") or not contract.rent_periods:
            raise ValueError(f"合同{contract.contract_id}无租金期数据，无法初始化核算逻辑")
        if not hasattr(contract, "tax_rate") or contract.tax_rate <= 0:
            raise ValueError(f"合同{contract.contract_id}税率无效（{contract.tax_rate}），无法计算增值税")

        # 组合原有合同和数据库实例
        self.contract = contract
        self.db = db
        self.contract_id = contract.contract_id
        self.tax_rate = contract.tax_rate
        self.is_adjust_income = contract.need_adjust_income
        self.income_tax_rate = 0.25  # 企业所得税税率（默认25%，可配置）

    def calculate_monthly_income(self, target_year: int, target_month: int) -> tuple[float, float]:
        """计算指定月份的会计和税法收入"""
        # 步骤1：计算税法口径核心数据（有效租赁天数+含税租金）
        valid_days, total_tax_rent = self._get_valid_rent_data(target_year, target_month)
        
        # 步骤2：税法口径不含税收入 = 含税租金 / (1+税率)
        tax_income = round(total_tax_rent / (1 + self.tax_rate), 2) if (1 + self.tax_rate) != 0 else 0.0
        
        # 步骤3：会计口径不含税收入（分"是否调整"两种场景）
        if not self.is_adjust_income:
            accounting_income = tax_income  # 无需调整：与税法一致
        else:
            accounting_income = self._calculate_adjusted_income(target_year, target_month, valid_days)
        
        # 步骤4：存储结果到月度收入表（避免重复存储）
        self._save_monthly_income(target_year, target_month, accounting_income, tax_income)
        
        # 步骤5：触发超收税额冲回
        if tax_income > 0:
            self._calculate_overpaid_vat_reverse(target_year, target_month, tax_income)
        
        return accounting_income, tax_income

    def calculate_vat(self, relate_type: str, relate_date: datetime.date, amount: float, relate_id) -> tuple[float, int]:
        """计算增值税（收款/开票/应收孰早原则）"""
        if amount <= 0 or self.tax_rate <= 0:
            return 0.0, -1
        
        base_vat = round(amount / (1 + self.tax_rate) * self.tax_rate, 2)
        overpaid_vat = 0.0
        
        if not isinstance(relate_date, datetime.date):
            logger.error(f"relate_date类型错误：{type(relate_date)}，应为date类型")
            return 0.0, -1
        
        # 修正纳税义务日期计算
        month_end = datetime.date(relate_date.year, relate_date.month,
                                 calendar.monthrange(relate_date.year, relate_date.month)[1])
        
        # 应收款按收款义务发生日（当月最后一天）
        if relate_type == "receivable":
            tax_obligation_date = month_end
        # 收款/开票按孰早原则（实际日期与当月最后一天取早）
        elif relate_type in ["payment", "invoice"]:
            tax_obligation_date = min(relate_date, month_end)
        else:
            tax_obligation_date = month_end
        
        # 仅收款类型触发超收增值税计算
        if relate_type == "payment":
            overpaid_vat = self._calculate_overpaid_vat(relate_date, amount)

        # 存储正常增值税记录
        base_vat_id = -1
        if base_vat > 0:
            base_vat_id = self.db.execute_return_id('''
            INSERT INTO vat_records (contract_id, relate_type, relate_id, vat_amount, tax_obligation_date, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (self.contract_id, relate_type, str(relate_id), base_vat, tax_obligation_date.strftime("%Y-%m-%d")))

        # 存储超收增值税记录
        overpaid_vat_id = -1
        if overpaid_vat > 0:
            overpaid_relate_id = str(uuid.uuid4())
            overpaid_vat_id = self.db.execute_return_id('''
            INSERT INTO vat_records (contract_id, relate_type, relate_id, vat_amount, tax_obligation_date, status, remark)
            VALUES (?, 'overpaid', ?, ?, ?, 'pending', ?)
            ''', (self.contract_id, overpaid_relate_id, overpaid_vat, 
                  tax_obligation_date.strftime("%Y-%m-%d"), f"超收租金增值税（收款{amount:.2f}元）"))
            logger.info(f"合同{self.contract_id}生成超收增值税记录：{overpaid_vat:.2f}元，关联ID：{overpaid_relate_id}")

        total_vat = base_vat + overpaid_vat
        return total_vat, overpaid_vat_id if overpaid_vat_id != -1 else base_vat_id

    def calculate_tax_diff(self, year: int, month: int) -> dict:
        """计算指定月份的税会差异及递延所得税"""
        # 先获取当月会计/税法收入
        accounting_income, tax_income = self.calculate_monthly_income(year, month)
        
        # 1. 税会差异金额（会计收入 - 税法收入）
        diff_amount = round(accounting_income - tax_income, 2)
        # 2. 待转销项税额（按会计收入计算：会计收入 × 税率）
        to_be_settled_vat = round(accounting_income * self.tax_rate, 2)
        # 3. 冲减待转销项税额（按税法收入计算：税法收入 × 税率）
        adjust_vat = round(tax_income * self.tax_rate, 2)
        # 4. 递延所得税（税会差异 × 企业所得税税率）
        deferred_tax = round(diff_amount * self.income_tax_rate, 2)

        # 存储税会差异记录到数据库
        self._save_tax_diff(year, month, accounting_income, tax_income, 
                           diff_amount, deferred_tax, to_be_settled_vat, adjust_vat)

        return {
            "contract_id": self.contract_id,
            "customer_name": self.contract.customer_name,
            "room_number": self.contract.room_number,
            "year": year,
            "month": month,
            "accounting_income": accounting_income,
            "tax_income": tax_income,
            "diff_amount": diff_amount,
            "deferred_tax": deferred_tax,
            "to_be_settled_vat": to_be_settled_vat,
            "adjust_vat": adjust_vat,
            "is_adjust": self.is_adjust_income
        }

    def calculate_stamp_duty(self) -> float:
        """计算合同印花税：合同含税总租金 × 0.001"""
        total_contract_rent = self.contract.total_rent
        stamp_duty = round(total_contract_rent * 0.001, 2)
        
        # 首次计算时，更新原有合同的印花税
        if self.contract.initial_stamp_duty == 0:
            self.contract.initial_stamp_duty = stamp_duty
            self.db.execute('''
            UPDATE contracts SET initial_stamp_duty = ? WHERE contract_id = ?
            ''', (stamp_duty, self.contract_id))
        
        logger.info(f"合同{self.contract_id}印花税计算完成：{stamp_duty:.2f}元")
        return stamp_duty

    def create_invoice_record(self, invoice_number: str, invoice_date: datetime.date, 
                             total_amount: float, relate_payment_id: int = None,
                             relate_income_year: int = None, relate_income_month: int = None):
        """生成发票记录并同步到invoice_details表，同时触发增值税计算"""
        if total_amount <= 0:
            raise ValueError("发票含税金额必须大于0")
        
        vat_amount = round(total_amount / (1 + self.tax_rate) * self.tax_rate, 2)
        
        try:
            self.db.connect()
            invoice_id = self.db.execute_return_id('''
            INSERT INTO invoice_details (
                invoice_number, contract_id, invoice_date, total_amount, vat_amount,
                relate_payment_id, relate_income_year, relate_income_month
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (invoice_number, self.contract_id, invoice_date.strftime("%Y-%m-%d"),
                  total_amount, vat_amount, relate_payment_id,
                  relate_income_year, relate_income_month))
            
            # 调用calculate_vat生成invoice类型增值税记录
            _, vat_record_id = self.calculate_vat(
                relate_type="invoice",
                relate_date=invoice_date,
                amount=total_amount,
                relate_id=invoice_number
            )
            
            logger.info(f"合同{self.contract_id}生成发票：{invoice_number}，含税金额{total_amount:.2f}元，税额{vat_amount:.2f}元")
            return invoice_id
            
        except Exception as e:
            if self.db.conn:
                self.db.conn.rollback()
            logger.error(f"创建发票记录失败：{str(e)}")
            return -1
        finally:
            self.db.close()

    def create_receivable_vat(self, receivable_date: datetime.date, receivable_amount: float, receivable_id: int):
        """当应收款产生时调用，生成receivable类型的增值税记录"""
        if receivable_amount <= 0 or self.tax_rate <= 0:
            logger.warning(f"合同{self.contract_id}应收款金额无效，不生成增值税记录")
            return
        
        total_vat, vat_id = self.calculate_vat(
            relate_type="receivable",
            relate_date=receivable_date,
            amount=receivable_amount,
            relate_id=receivable_id
        )
        
        if vat_id != -1:
            logger.info(f"合同{self.contract_id}生成应收款增值税记录（ID:{vat_id}），税额：{total_vat:.2f}元")

    # 私有辅助方法
    def _get_valid_rent_data(self, year: int, month: int) -> tuple[int, float]:
        """计算指定月份的有效租赁天数和含税租金"""
        month_start = datetime.date(year, month, 1)
        month_end = datetime.date(year, month, calendar.monthrange(year, month)[1])
        
        total_valid_days = 0
        total_tax_rent = 0.0

        for rp in sorted(self.contract.rent_periods, key=lambda x: x.start_date):
            # 租金期与目标月份的重叠区间
            rp_overlap_start = max(rp.start_date, month_start)
            rp_overlap_end = min(rp.end_date, month_end)
            if rp_overlap_start > rp_overlap_end:
                continue

            # 该租金期在当月的总天数
            rp_total_days = (rp_overlap_end - rp_overlap_start).days + 1
            # 该租金期在当月的免租期天数
            rp_free_days = self._get_free_days_in_period(rp_overlap_start, rp_overlap_end)
            # 有效天数 = 租金期天数 - 免租期天数
            rp_valid_days = max(rp_total_days - rp_free_days, 0)
            total_valid_days += rp_valid_days

            # 税法口径含税租金 = 月租金 × 有效天数 / 当月总天数
            month_total_days = (month_end - month_start).days + 1
            rp_tax_rent = rp.monthly_rent * rp_valid_days / month_total_days
            total_tax_rent += rp_tax_rent

        return total_valid_days, round(total_tax_rent, 2)

    def _calculate_adjusted_income(self, target_year: int, target_month: int, valid_days: int) -> float:
        """计算调整收入（会计口径）"""
        if not self.contract.rent_periods:
            logger.warning(f"合同{self.contract_id}无租金期，收入为0")
            return 0.0

        # 判断合同是否已到租期
        overall_start = min(rp.start_date for rp in self.contract.rent_periods)
        target_month_last_day = datetime.date(target_year, target_month, 
                                             calendar.monthrange(target_year, target_month)[1])
        
        if overall_start > target_month_last_day:
            logger.info(f"合同{self.contract_id}未到租期（{overall_start}），{target_year}年{target_month}月会计收入为0")
            return 0.0

        # 计算首月比例
        first_month_year = overall_start.year
        first_month = overall_start.month
        first_month_total_days = calendar.monthrange(first_month_year, first_month)[1]
        first_month_valid_days = (datetime.date(first_month_year, first_month, first_month_total_days) - overall_start).days + 1
        first_month_ratio = first_month_valid_days / first_month_total_days

        # 计算尾月比例
        overall_end = max(rp.end_date for rp in self.contract.rent_periods)
        last_month_year = overall_end.year
        last_month = overall_end.month
        last_month_total_days = calendar.monthrange(last_month_year, last_month)[1]
        last_month_valid_days = (overall_end - datetime.date(last_month_year, last_month, 1)).days + 1
        last_month_ratio = last_month_valid_days / last_month_total_days

        # 修正中间整月数计算
        total_month_diff = (last_month_year - first_month_year) * 12 + (last_month - first_month)
        middle_full_months = max(total_month_diff - 1, 0)

        # 总租赁月数
        total_lease_months = first_month_ratio + middle_full_months + last_month_ratio
        if total_lease_months <= 0:
            return 0.0

        # 计算会计租金
        total_contract_rent = self.contract.total_rent
        try:
            monthly_accounting_rent = (total_contract_rent / (1 + self.tax_rate)) / total_lease_months
            return round(monthly_accounting_rent, 2)
        except:
            return 0.0

    def _calculate_overpaid_vat(self, payment_date: datetime.date, payment_amount: float) -> float:
        """计算超收租金的增值税"""
        # 累计应收租金（截至付款当月，含税）
        total_receivable = 0.0
        first_rent_year = self.contract.rent_periods[0].start_date.year
        for year in range(first_rent_year, payment_date.year + 1):
            for month in range(1, 13):
                if year == payment_date.year and month > payment_date.month:
                    break
                _, monthly_receivable = self._get_valid_rent_data(year, month)
                total_receivable += monthly_receivable

        # 累计已收租金（截至付款日期，含税，仅租金类型）
        total_paid = sum(p.amount for p in self.contract.payment_records 
                        if p.payment_type == "租金" and p.date <= payment_date)
        
        # 超收金额 = 本次收款后累计已收 - 累计应收
        overpaid = max((total_paid + payment_amount) - total_receivable, 0.0)
        if overpaid <= 0:
            return 0.0

        # 超收部分的增值税
        overpaid_vat = round(overpaid / (1 + self.tax_rate) * self.tax_rate, 2)
        logger.info(f"合同{self.contract_id}超收租金{overpaid:.2f}元，新增增值税{overpaid_vat:.2f}元")
        return overpaid_vat

    def _calculate_overpaid_vat_reverse(self, target_year: int, target_month: int, tax_income: float):
        """后续月份确认收入时，冲回超收租金对应的增值税"""
        if tax_income <= 0:
            return 0.0
        
        max_reverse_vat = round(tax_income * self.tax_rate, 2)
        if max_reverse_vat <= 0:
            return 0.0
        
        # 查询截至当月的未冲回超收增值税记录
        unpaid_overpaid_records = self.db.query('''
            SELECT id, vat_amount, tax_obligation_date 
            FROM vat_records
            WHERE contract_id = ? 
              AND relate_type = 'overpaid'
              AND status = 'pending'
              AND id NOT IN (
                  SELECT relate_id FROM vat_records 
                  WHERE contract_id = ? AND relate_type = 'overpaid_reverse'
              )
            ORDER BY tax_obligation_date ASC
        ''', (self.contract_id, self.contract_id))
        
        if not unpaid_overpaid_records:
            return 0.0
        
        total_unpaid_vat = sum(record['vat_amount'] for record in unpaid_overpaid_records)
        actual_reverse_vat = min(max_reverse_vat, total_unpaid_vat)
        remaining_reverse = actual_reverse_vat
        
        tax_obligation_date = datetime.date(target_year, target_month, 
                                           calendar.monthrange(target_year, target_month)[1])
        
        for record in unpaid_overpaid_records:
            if remaining_reverse <= 0:
                break
            
            record_reverse = min(record['vat_amount'], remaining_reverse)
            reverse_vat_neg = -record_reverse
            
            self.db.execute_return_id('''
            INSERT INTO vat_records (
                contract_id, relate_type, relate_id, vat_amount, 
                tax_obligation_date, status, remark
            ) VALUES (?, 'overpaid_reverse', ?, ?, ?, 'pending', ?)
            ''', (
                self.contract_id,
                str(record['id']),
                reverse_vat_neg,
                tax_obligation_date.strftime("%Y-%m-%d"),
                f"冲回超收增值税：原超收记录ID={record['id']}，对应{target_year}年{target_month}月收入"
            ))
            
            logger.info(f"合同{self.contract_id}冲回超收增值税：{record_reverse:.2f}元，原超收记录ID={record['id']}")
            remaining_reverse -= record_reverse
        
        return -actual_reverse_vat

    def _save_monthly_income(self, year: int, month: int, accounting_income: float, tax_income: float):
        """存储月度收入到数据库"""
        existing = self.db.query(
            "SELECT id FROM monthly_income WHERE contract_id=? AND year=? AND month=?",
            (self.contract_id, year, month)
        )
        if existing:
            return  # 已存在，不重复存储

        # 插入新记录
        self.db.execute('''
        INSERT INTO monthly_income (contract_id, year, month, accounting_income, tax_income, tax_rate, is_adjust)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (self.contract_id, year, month, accounting_income, tax_income,
              self.tax_rate, 1 if self.is_adjust_income else 0))

        income_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
        self.db.execute('''
        INSERT INTO income_records (
            contract_id, income_date, accounting_income, tax_income,
            source_type, source_id
        ) VALUES (?, ?, ?, ?, 'monthly', ?)
        ''', (self.contract_id, income_date.strftime("%Y-%m-%d"),
              accounting_income, tax_income,
              # 获取刚插入的monthly_income记录ID
              self.db.cursor.lastrowid))

    def _save_tax_diff(self, year: int, month: int, accounting_income: float, tax_income: float,
                      diff_amount: float, deferred_tax: float, to_be_settled_vat: float, adjust_vat: float):
        """存储税会差异记录到数据库"""
        existing = self.db.query(
            "SELECT id FROM tax_diff WHERE contract_id=? AND year=? AND month=?",
            (self.contract_id, year, month)
        )
        if existing:
            return

        self.db.execute('''
        INSERT INTO tax_diff (contract_id, year, month, accounting_income, tax_income, 
                             diff_amount, deferred_tax, to_be_settled_vat, adjust_vat)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.contract_id, year, month, accounting_income, tax_income,
              diff_amount, deferred_tax, to_be_settled_vat, adjust_vat))

    def _get_free_days_in_period(self, start_date: datetime.date, end_date: datetime.date) -> int:
        """计算指定时间段内的免租期总天数"""
        free_days = 0
        for fp in sorted(self.contract.free_rent_periods, key=lambda x: x.start_date):
            # 免租期与指定时间段的重叠区间
            overlap_start = max(start_date, fp.start_date)
            overlap_end = min(end_date, fp.end_date)
            if overlap_start > overlap_end:
                continue  # 无重叠，跳过
            # 累加重叠天数
            free_days += (overlap_end - overlap_start).days + 1
        return free_days