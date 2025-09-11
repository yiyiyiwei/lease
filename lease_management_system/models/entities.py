"""
实体模型定义
"""
import datetime
import calendar
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from config.settings import config


class ContractType(Enum):
    """合同类型枚举"""
    NEW = "新增"
    RENEWAL = "续租"
    CHANGE = "变更"


class RecordType(Enum):
    """记录类型枚举"""
    RECEIVE = "收取"
    RETURN = "退还"


class PaymentType(Enum):
    """付款类型枚举"""
    RENT = "租金"
    DEPOSIT = "押金"


@dataclass
class User:
    """用户实体"""
    username: str
    role: str
    created_at: Optional[datetime.datetime] = None
    
    def is_admin(self) -> bool:
        return self.role == 'admin'
    
    def can_edit(self) -> bool:
        return self.role in ['admin', 'operator']


@dataclass
class RentPeriod:
    """租金期实体"""
    start_date: datetime.date
    end_date: datetime.date
    monthly_rent: float
    id: Optional[int] = None
    
    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")
        if self.monthly_rent <= 0:
            raise ValueError("月租金必须大于0")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "monthly_rent": self.monthly_rent
        }


@dataclass
class FreeRentPeriod:
    """免租期实体"""
    start_date: datetime.date
    end_date: datetime.date
    id: Optional[int] = None
    
    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d")
        }


@dataclass
class PaymentRecord:
    """收款记录实体"""
    date: datetime.date
    amount: float
    contract_id: str
    payment_type: str
    id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("金额必须大于0")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "amount": self.amount,
            "contract_id": self.contract_id,
            "payment_type": self.payment_type,
            "created_by": self.created_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


@dataclass
class DepositRecord:
    """押金记录实体"""
    date: datetime.date
    amount: float
    contract_id: str
    record_type: str
    remark: str = ""
    id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("金额必须大于0")
        if self.record_type not in [RecordType.RECEIVE.value, RecordType.RETURN.value]:
            raise ValueError("记录类型必须是'收取'或'退还'")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "amount": self.amount,
            "contract_id": self.contract_id,
            "record_type": self.record_type,
            "remark": self.remark,
            "created_by": self.created_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


@dataclass
class InvoiceRecord:
    """开票记录实体"""
    date: datetime.date
    amount: float
    tax_amount: float
    invoice_number: str
    contract_id: str
    id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("金额必须大于0")
        if self.tax_amount < 0:
            raise ValueError("税额不能为负数")
        if not self.invoice_number.strip():
            raise ValueError("发票号不能为空")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "amount": self.amount,
            "tax_amount": self.tax_amount,
            "invoice_number": self.invoice_number,
            "contract_id": self.contract_id,
            "created_by": self.created_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


@dataclass
class LeaseContract:
    """租赁合同实体"""
    contract_id: str
    customer_name: str
    room_number: str
    payment_name: str
    eas_code: str
    created_by: str
    area: float = 0.0
    tax_rate: float = config.business.default_tax_rate
    need_adjust_income: bool = False
    deposit_amount: float = 0.0
    create_time: Optional[datetime.datetime] = None
    contract_type: str = ContractType.NEW.value
    original_contract_id: Optional[str] = None
    is_effective: bool = False
    effective_date: Optional[datetime.date] = None
    
    # 计算字段
    total_rent: float = field(default=0.0, init=False)
    initial_total_rent: float = field(default=0.0, init=False)
    initial_stamp_duty: float = field(default=0.0, init=False)
    
    # 关联数据
    rent_periods: List[RentPeriod] = field(default_factory=list, init=False)
    free_rent_periods: List[FreeRentPeriod] = field(default_factory=list, init=False)
    payment_records: List[PaymentRecord] = field(default_factory=list, init=False)
    deposit_records: List[DepositRecord] = field(default_factory=list, init=False)
    invoice_records: List[InvoiceRecord] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        if not self.contract_id.strip():
            raise ValueError("合同ID不能为空")
        if not self.customer_name.strip():
            raise ValueError("客户姓名不能为空")
        if not self.room_number.strip():
            raise ValueError("房间号不能为空")
        if not self.payment_name.strip():
            raise ValueError("对方付款名称不能为空")
        if not self.eas_code.strip():
            raise ValueError("EAS代码不能为空")
        if self.area < 0:
            raise ValueError("租赁面积不能为负数")
        if self.tax_rate < 0 or self.tax_rate > 1:
            raise ValueError("税率必须在0-100%之间")
        if self.deposit_amount < 0:
            raise ValueError("押金不能为负数")
        if self.create_time is None:
            self.create_time = datetime.datetime.now()
    
    def calculate_total_rent(self) -> float:
        """计算总租金"""
        total = 0.0
        
        sorted_rent_periods = sorted(self.rent_periods, key=lambda x: x.start_date)
        sorted_free_periods = sorted(self.free_rent_periods, key=lambda x: x.start_date)
        
        for rent_period in sorted_rent_periods:
            current_date = rent_period.start_date
            end_date = rent_period.end_date
            monthly_rent = rent_period.monthly_rent
            
            while current_date <= end_date:
                # 获取当前月的最后一天
                month_last_day = datetime.date(
                    current_date.year,
                    current_date.month,
                    calendar.monthrange(current_date.year, current_date.month)[1]
                )
                period_end_in_month = min(end_date, month_last_day)
                
                # 计算当前月内的租金天数
                days_in_month = (period_end_in_month - current_date).days + 1
                
                # 计算当前月的日租金
                daily_rent = monthly_rent / calendar.monthrange(current_date.year, current_date.month)[1]
                
                # 计算当前月的基础租金
                monthly_base_rent = daily_rent * days_in_month
                
                # 扣除当前月内的免租期重叠部分
                for free_period in sorted_free_periods:
                    overlap_start = max(current_date, free_period.start_date)
                    overlap_end = min(period_end_in_month, free_period.end_date)
                    
                    if overlap_start <= overlap_end:
                        overlap_days = (overlap_end - overlap_start).days + 1
                        monthly_base_rent -= daily_rent * overlap_days
                
                total += max(monthly_base_rent, 0.0)
                
                # 进入下一个月
                if current_date.month == 12:
                    current_date = datetime.date(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime.date(current_date.year, current_date.month + 1, 1)
        
        self.total_rent = round(total, 2)
        self.initial_total_rent = self.total_rent
        self.initial_stamp_duty = round(self.initial_total_rent * config.business.stamp_duty_rate, 2)
        
        return self.total_rent
    
    def get_deposit_balance(self) -> float:
        """计算押金余额"""
        balance = 0.0
        for deposit in self.deposit_records:
            if deposit.record_type == RecordType.RECEIVE.value:
                balance += deposit.amount
            else:
                balance -= deposit.amount
        return round(balance, 2)
    
    def mark_effective(self, effective_date: datetime.date):
        """标记合同生效"""
        if self.is_effective:
            raise ValueError("合同已生效，无需重复操作")
        self.is_effective = True
        self.effective_date = effective_date
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "contract_id": self.contract_id,
            "customer_name": self.customer_name,
            "room_number": self.room_number,
            "area": self.area,
            "total_rent": self.total_rent,
            "initial_total_rent": self.initial_total_rent,
            "payment_name": self.payment_name,
            "eas_code": self.eas_code,
            "tax_rate": self.tax_rate,
            "need_adjust_income": 1 if self.need_adjust_income else 0,
            "deposit_amount": self.deposit_amount,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "initial_stamp_duty": self.initial_stamp_duty,
            "created_by": self.created_by,
            "contract_type": self.contract_type,
            "original_contract_id": self.original_contract_id,
            "is_effective": 1 if self.is_effective else 0,
            "effective_date": self.effective_date.strftime("%Y-%m-%d") if self.effective_date else None
        }
