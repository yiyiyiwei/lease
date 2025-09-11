"""
支付业务逻辑服务
"""
import datetime
from typing import List, Dict, Any, Optional

from database.manager import DatabaseManager
from models.entities import PaymentRecord, DepositRecord, InvoiceRecord, RecordType
from utils.logging import get_logger

logger = get_logger("PaymentService")


class PaymentService:
    """支付业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_payment_record(self, payment: PaymentRecord, user: str) -> bool:
        """添加收款记录"""
        try:
            sql = '''
                INSERT INTO payment_records (contract_id, date, amount, payment_type, created_by)
                VALUES (?, ?, ?, ?, ?)
            '''
            
            record_id = self.db.execute_command_with_id(sql, (
                payment.contract_id,
                payment.date.strftime("%Y-%m-%d"),
                payment.amount,
                payment.payment_type,
                user
            ))
            
            if record_id is None:
                raise Exception("保存收款记录失败")
            
            payment.id = record_id
            payment.created_by = user
            payment.created_at = datetime.datetime.now()
            
            # 记录操作日志
            self.db.log_operation(user, 'create', 'payment', payment.contract_id,
                                f'添加收款记录：{payment.payment_type} {payment.amount:.2f}元')
            logger.info(f"用户 {user} 添加了收款记录: 合同ID={payment.contract_id}, 金额={payment.amount}")
            
            return True
            
        except Exception as e:
            logger.error(f"添加收款记录失败: {str(e)}")
            return False
    
    def add_deposit_record(self, deposit: DepositRecord, user: str, current_balance: float = 0.0) -> bool:
        """添加押金记录"""
        try:
            # 验证押金余额
            if deposit.record_type == RecordType.RETURN.value and deposit.amount > current_balance:
                raise ValueError(f"押金余额不足！当前余额: {current_balance:.2f}元，尝试退还: {deposit.amount:.2f}元")
            
            sql = '''
                INSERT INTO deposit_records (contract_id, date, amount, record_type, created_by, remark)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            
            record_id = self.db.execute_command_with_id(sql, (
                deposit.contract_id,
                deposit.date.strftime("%Y-%m-%d"),
                deposit.amount,
                deposit.record_type,
                user,
                deposit.remark
            ))
            
            if record_id is None:
                raise Exception("保存押金记录失败")
            
            deposit.id = record_id
            deposit.created_by = user
            deposit.created_at = datetime.datetime.now()
            
            # 记录操作日志
            self.db.log_operation(user, 'create', 'deposit', deposit.contract_id,
                                f'{deposit.record_type}押金 {deposit.amount:.2f}元')
            logger.info(f"用户 {user} 添加了押金记录: 合同ID={deposit.contract_id}, {deposit.record_type} {deposit.amount}")
            
            return True
            
        except Exception as e:
            logger.error(f"添加押金记录失败: {str(e)}")
            return False
    
    def add_invoice_record(self, invoice: InvoiceRecord, user: str) -> bool:
        """添加开票记录"""
        try:
            sql = '''
                INSERT INTO invoice_records (contract_id, date, amount, tax_amount, invoice_number, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            
            record_id = self.db.execute_command_with_id(sql, (
                invoice.contract_id,
                invoice.date.strftime("%Y-%m-%d"),
                invoice.amount,
                invoice.tax_amount,
                invoice.invoice_number,
                user
            ))
            
            if record_id is None:
                raise Exception("保存开票记录失败")
            
            invoice.id = record_id
            invoice.created_by = user
            invoice.created_at = datetime.datetime.now()
            
            # 记录操作日志
            self.db.log_operation(user, 'create', 'invoice', invoice.contract_id,
                                f'添加开票记录：发票号 {invoice.invoice_number}')
            logger.info(f"用户 {user} 添加了开票记录: 合同ID={invoice.contract_id}, 发票号={invoice.invoice_number}")
            
            return True
            
        except Exception as e:
            logger.error(f"添加开票记录失败: {str(e)}")
            return False
    
    def get_payment_records(self, contract_id: Optional[str] = None) -> List[PaymentRecord]:
        """获取收款记录"""
        try:
            if contract_id:
                sql = "SELECT * FROM payment_records WHERE contract_id = ? ORDER BY date DESC"
                records = self.db.execute_query(sql, (contract_id,))
            else:
                sql = "SELECT * FROM payment_records ORDER BY date DESC"
                records = self.db.execute_query(sql)
            
            result = []
            for record_data in records:
                payment = PaymentRecord(
                    date=datetime.datetime.strptime(record_data['date'], "%Y-%m-%d").date(),
                    amount=record_data['amount'],
                    contract_id=record_data['contract_id'],
                    payment_type=record_data['payment_type'],
                    id=record_data['id'],
                    created_by=record_data.get('created_by'),
                    created_at=datetime.datetime.fromisoformat(record_data['created_at']) if record_data.get('created_at') else None
                )
                result.append(payment)
            
            return result
            
        except Exception as e:
            logger.error(f"获取收款记录失败: {str(e)}")
            return []
    
    def get_deposit_records(self, contract_id: Optional[str] = None) -> List[DepositRecord]:
        """获取押金记录"""
        try:
            if contract_id:
                sql = "SELECT * FROM deposit_records WHERE contract_id = ? ORDER BY date DESC"
                records = self.db.execute_query(sql, (contract_id,))
            else:
                sql = "SELECT * FROM deposit_records ORDER BY date DESC"
                records = self.db.execute_query(sql)
            
            result = []
            for record_data in records:
                deposit = DepositRecord(
                    date=datetime.datetime.strptime(record_data['date'], "%Y-%m-%d").date(),
                    amount=record_data['amount'],
                    contract_id=record_data['contract_id'],
                    record_type=record_data['record_type'],
                    remark=record_data.get('remark', ''),
                    id=record_data['id'],
                    created_by=record_data.get('created_by'),
                    created_at=datetime.datetime.fromisoformat(record_data['created_at']) if record_data.get('created_at') else None
                )
                result.append(deposit)
            
            return result
            
        except Exception as e:
            logger.error(f"获取押金记录失败: {str(e)}")
            return []
    
    def get_invoice_records(self, contract_id: Optional[str] = None) -> List[InvoiceRecord]:
        """获取开票记录"""
        try:
            if contract_id:
                sql = "SELECT * FROM invoice_records WHERE contract_id = ? ORDER BY date DESC"
                records = self.db.execute_query(sql, (contract_id,))
            else:
                sql = "SELECT * FROM invoice_records ORDER BY date DESC"
                records = self.db.execute_query(sql)
            
            result = []
            for record_data in records:
                invoice = InvoiceRecord(
                    date=datetime.datetime.strptime(record_data['date'], "%Y-%m-%d").date(),
                    amount=record_data['amount'],
                    tax_amount=record_data['tax_amount'],
                    invoice_number=record_data['invoice_number'],
                    contract_id=record_data['contract_id'],
                    id=record_data['id'],
                    created_by=record_data.get('created_by'),
                    created_at=datetime.datetime.fromisoformat(record_data['created_at']) if record_data.get('created_at') else None
                )
                result.append(invoice)
            
            return result
            
        except Exception as e:
            logger.error(f"获取开票记录失败: {str(e)}")
            return []
    
    def get_deposit_balance(self, contract_id: str) -> float:
        """获取押金余额"""
        try:
            deposits = self.get_deposit_records(contract_id)
            balance = 0.0
            
            for deposit in deposits:
                if deposit.record_type == RecordType.RECEIVE.value:
                    balance += deposit.amount
                else:
                    balance -= deposit.amount
            
            return round(balance, 2)
            
        except Exception as e:
            logger.error(f"计算押金余额失败: contract_id={contract_id}, 错误={str(e)}")
            return 0.0
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """获取月度收支汇总"""
        try:
            # 计算月份的起止日期
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year}-12-31"
            else:
                next_month = datetime.date(year, month + 1, 1)
                end_date = (next_month - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            
            # 收款汇总
            payment_sql = '''
                SELECT payment_type, SUM(amount) as total_amount
                FROM payment_records 
                WHERE date BETWEEN ? AND ?
                GROUP BY payment_type
            '''
            payments = self.db.execute_query(payment_sql, (start_date, end_date))
            
            # 押金汇总
            deposit_sql = '''
                SELECT record_type, SUM(amount) as total_amount
                FROM deposit_records 
                WHERE date BETWEEN ? AND ?
                GROUP BY record_type
            '''
            deposits = self.db.execute_query(deposit_sql, (start_date, end_date))
            
            # 开票汇总
            invoice_sql = '''
                SELECT COUNT(*) as count, SUM(amount) as total_amount, SUM(tax_amount) as total_tax
                FROM invoice_records 
                WHERE date BETWEEN ? AND ?
            '''
            invoices = self.db.execute_query(invoice_sql, (start_date, end_date))
            
            return {
                'payments': {p['payment_type']: p['total_amount'] for p in payments},
                'deposits': {d['record_type']: d['total_amount'] for d in deposits},
                'invoices': invoices[0] if invoices else {'count': 0, 'total_amount': 0, 'total_tax': 0}
            }
            
        except Exception as e:
            logger.error(f"获取月度汇总失败: year={year}, month={month}, 错误={str(e)}")
            return {'payments': {}, 'deposits': {}, 'invoices': {'count': 0, 'total_amount': 0, 'total_tax': 0}}
    
    def delete_payment_record(self, record_id: int, user: str) -> bool:
        """删除收款记录"""
        try:
            if not self.db.execute_command("DELETE FROM payment_records WHERE id = ?", (record_id,)):
                raise Exception("删除收款记录失败")
            
            # 记录操作日志
            self.db.log_operation(user, 'delete', 'payment', str(record_id), '删除收款记录')
            logger.info(f"用户 {user} 删除了收款记录: ID={record_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"删除收款记录失败: record_id={record_id}, 错误={str(e)}")
            return False
    
    def delete_deposit_record(self, record_id: int, user: str) -> bool:
        """删除押金记录"""
        try:
            if not self.db.execute_command("DELETE FROM deposit_records WHERE id = ?", (record_id,)):
                raise Exception("删除押金记录失败")
            
            # 记录操作日志
            self.db.log_operation(user, 'delete', 'deposit', str(record_id), '删除押金记录')
            logger.info(f"用户 {user} 删除了押金记录: ID={record_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"删除押金记录失败: record_id={record_id}, 错误={str(e)}")
            return False
    
    def delete_invoice_record(self, record_id: int, user: str) -> bool:
        """删除开票记录"""
        try:
            if not self.db.execute_command("DELETE FROM invoice_records WHERE id = ?", (record_id,)):
                raise Exception("删除开票记录失败")
            
            # 记录操作日志
            self.db.log_operation(user, 'delete', 'invoice', str(record_id), '删除开票记录')
            logger.info(f"用户 {user} 删除了开票记录: ID={record_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"删除开票记录失败: record_id={record_id}, 错误={str(e)}")
            return False