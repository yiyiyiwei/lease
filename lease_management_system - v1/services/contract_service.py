"""
合同业务逻辑服务
"""
import datetime
from typing import List, Dict, Any, Optional

from database.manager import DatabaseManager
from models.entities import LeaseContract, RentPeriod, FreeRentPeriod, ContractType
from utils.logging import get_logger

logger = get_logger("ContractService")


class ContractService:
    """合同业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_contract(self, contract_data: Dict[str, Any], user: str) -> LeaseContract:
        """创建新合同"""
        try:
            # 验证合同ID唯一性
            if self.get_contract_by_id(contract_data["contract_id"]):
                raise ValueError(f"合同ID {contract_data['contract_id']} 已存在")
            
            # 验证续租/变更合同的原合同
            if contract_data.get("contract_type") in [ContractType.RENEWAL.value, ContractType.CHANGE.value]:
                original_id = contract_data.get("original_contract_id")
                if not original_id:
                    raise ValueError("续租/变更类型需要指定原合同ID")
                if not self.get_contract_by_id(original_id):
                    raise ValueError(f"原合同{original_id}不存在")
            
            # 创建合同实体
            contract = LeaseContract(
                contract_id=contract_data["contract_id"],
                customer_name=contract_data["customer_name"],
                room_number=contract_data["room_number"],
                payment_name=contract_data["payment_name"],
                eas_code=contract_data["eas_code"],
                created_by=user,
                area=contract_data.get("area", 0.0),
                tax_rate=contract_data.get("tax_rate", 0.05),
                need_adjust_income=contract_data.get("need_adjust_income", False),
                deposit_amount=contract_data.get("deposit_amount", 0.0),
                contract_type=contract_data.get("contract_type", ContractType.NEW.value),
                original_contract_id=contract_data.get("original_contract_id"),
                create_time=contract_data.get("create_time", datetime.datetime.now())
            )
            
            # 保存到数据库
            contract_dict = contract.to_dict()
            sql = '''
                INSERT INTO contracts (
                    contract_id, customer_name, room_number, area, total_rent,
                    initial_total_rent, payment_name, eas_code, tax_rate,
                    need_adjust_income, deposit_amount, create_time,
                    initial_stamp_duty, created_by, contract_type, original_contract_id,
                    is_effective, effective_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            if not self.db.execute_command(sql, (
                contract_dict['contract_id'],
                contract_dict['customer_name'],
                contract_dict['room_number'],
                contract_dict['area'],
                contract_dict['total_rent'],
                contract_dict['initial_total_rent'],
                contract_dict['payment_name'],
                contract_dict['eas_code'],
                contract_dict['tax_rate'],
                contract_dict['need_adjust_income'],
                contract_dict['deposit_amount'],
                contract_dict['create_time'],
                contract_dict['initial_stamp_duty'],
                contract_dict['created_by'],
                contract_dict['contract_type'],
                contract_dict['original_contract_id'],
                contract_dict['is_effective'],
                contract_dict['effective_date']
            )):
                raise Exception("保存合同到数据库失败")
            
            # 记录操作日志
            self.db.log_operation(user, 'create', 'contract', contract.contract_id, '创建新合同')
            logger.info(f"用户 {user} 创建了新合同: {contract.contract_id}")
            
            return contract
            
        except Exception as e:
            logger.error(f"创建合同失败: {str(e)}")
            raise
    
    def get_contract_by_id(self, contract_id: str) -> Optional[LeaseContract]:
        """根据ID获取合同"""
        try:
            contracts = self.db.execute_query(
                "SELECT * FROM contracts WHERE contract_id = ?",
                (contract_id,)
            )
            if not contracts:
                return None
            
            contract_data = contracts[0]
            contract = self._build_contract_from_dict(contract_data)
            self._load_contract_relations(contract)
            return contract
            
        except Exception as e:
            logger.error(f"获取合同失败: contract_id={contract_id}, 错误={str(e)}")
            return None
    
    def get_all_contracts(self) -> List[LeaseContract]:
        """获取所有合同"""
        try:
            contracts = self.db.execute_query("SELECT * FROM contracts ORDER BY create_time DESC")
            result = []
            
            for contract_data in contracts:
                contract = self._build_contract_from_dict(contract_data)
                self._load_contract_relations(contract)
                result.append(contract)
            
            return result
            
        except Exception as e:
            logger.error(f"获取所有合同失败: {str(e)}")
            return []
    
    def update_contract(self, contract_id: str, update_data: Dict[str, Any], user: str) -> bool:
        """更新合同"""
        try:
            # 构建更新SQL
            set_clauses = []
            params = []
            
            for field, value in update_data.items():
                if field in ['customer_name', 'room_number', 'area', 'payment_name', 
                           'eas_code', 'tax_rate', 'need_adjust_income', 'deposit_amount']:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return True  # 没有需要更新的字段
            
            params.append(contract_id)
            sql = f"UPDATE contracts SET {', '.join(set_clauses)} WHERE contract_id = ?"
            
            if not self.db.execute_command(sql, params):
                raise Exception("更新合同失败")
            
            # 记录操作日志
            self.db.log_operation(user, 'update', 'contract', contract_id, '更新合同基础信息')
            logger.info(f"用户 {user} 更新了合同: {contract_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"更新合同失败: contract_id={contract_id}, 错误={str(e)}")
            return False
    
    def delete_contract(self, contract_id: str, user: str) -> bool:
        """删除合同"""
        try:
            # 检查合同是否存在
            if not self.get_contract_by_id(contract_id):
                raise ValueError(f"合同 {contract_id} 不存在")
            
            # 删除合同（级联删除相关记录）
            if not self.db.execute_command("DELETE FROM contracts WHERE contract_id = ?", (contract_id,)):
                raise Exception("删除合同失败")
            
            # 记录操作日志
            self.db.log_operation(user, 'delete', 'contract', contract_id, '删除合同及关联数据')
            logger.info(f"用户 {user} 删除了合同: {contract_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"删除合同失败: contract_id={contract_id}, 错误={str(e)}")
            return False
    
    def mark_contract_effective(self, contract_id: str, effective_date: datetime.date, user: str) -> bool:
        """标记合同生效"""
        try:
            contract = self.get_contract_by_id(contract_id)
            if not contract:
                raise ValueError(f"合同 {contract_id} 不存在")
            
            if contract.is_effective:
                raise ValueError("合同已生效，无需重复操作")
            
            # 更新数据库
            sql = "UPDATE contracts SET is_effective = 1, effective_date = ? WHERE contract_id = ?"
            if not self.db.execute_command(sql, (effective_date.strftime("%Y-%m-%d"), contract_id)):
                raise Exception("更新合同生效状态失败")
            
            # 记录操作日志
            self.db.log_operation(user, 'update', 'contract', contract_id, 
                                f'标记合同生效，生效日期：{effective_date.strftime("%Y-%m-%d")}')
            logger.info(f"用户 {user} 标记合同 {contract_id} 为生效")
            
            return True
            
        except Exception as e:
            logger.error(f"标记合同生效失败: contract_id={contract_id}, 错误={str(e)}")
            return False
    
    def add_rent_period(self, contract_id: str, rent_period: RentPeriod, user: str) -> bool:
        """添加租金期"""
        try:
            contract = self.get_contract_by_id(contract_id)
            if not contract:
                raise ValueError(f"合同 {contract_id} 不存在")
            
            # 检查期间重叠
            self._check_period_overlap(rent_period, contract.rent_periods, "租金期")
            
            # 保存到数据库
            sql = '''
                INSERT INTO rent_periods (contract_id, start_date, end_date, monthly_rent)
                VALUES (?, ?, ?, ?)
            '''
            
            if not self.db.execute_command(sql, (
                contract_id,
                rent_period.start_date.strftime("%Y-%m-%d"),
                rent_period.end_date.strftime("%Y-%m-%d"),
                rent_period.monthly_rent
            )):
                raise Exception("保存租金期失败")
            
            # 重新计算合同总租金
            contract.rent_periods.append(rent_period)
            total_rent = contract.calculate_total_rent()
            
            # 更新合同总租金
            self.db.execute_command(
                "UPDATE contracts SET total_rent = ?, initial_total_rent = ?, initial_stamp_duty = ? WHERE contract_id = ?",
                (total_rent, contract.initial_total_rent, contract.initial_stamp_duty, contract_id)
            )
            
            # 记录操作日志
            self.db.log_operation(user, 'create', 'rent_period', contract_id, 
                                f'添加租金期：{rent_period.start_date} - {rent_period.end_date}')
            logger.info(f"用户 {user} 为合同 {contract_id} 添加了租金期")
            
            return True
            
        except Exception as e:
            logger.error(f"添加租金期失败: contract_id={contract_id}, 错误={str(e)}")
            return False
    
    def add_free_rent_period(self, contract_id: str, free_period: FreeRentPeriod, user: str) -> bool:
        """添加免租期"""
        try:
            contract = self.get_contract_by_id(contract_id)
            if not contract:
                raise ValueError(f"合同 {contract_id} 不存在")
            
            # 检查期间重叠
            self._check_period_overlap(free_period, contract.free_rent_periods, "免租期")
            
            # 保存到数据库
            sql = '''
                INSERT INTO free_periods (contract_id, start_date, end_date)
                VALUES (?, ?, ?)
            '''
            
            if not self.db.execute_command(sql, (
                contract_id,
                free_period.start_date.strftime("%Y-%m-%d"),
                free_period.end_date.strftime("%Y-%m-%d")
            )):
                raise Exception("保存免租期失败")
            
            # 重新计算合同总租金
            contract.free_rent_periods.append(free_period)
            total_rent = contract.calculate_total_rent()
            
            # 更新合同总租金
            self.db.execute_command(
                "UPDATE contracts SET total_rent = ?, initial_total_rent = ?, initial_stamp_duty = ? WHERE contract_id = ?",
                (total_rent, contract.initial_total_rent, contract.initial_stamp_duty, contract_id)
            )
            
            # 记录操作日志
            self.db.log_operation(user, 'create', 'free_period', contract_id,
                                f'添加免租期：{free_period.start_date} - {free_period.end_date}')
            logger.info(f"用户 {user} 为合同 {contract_id} 添加了免租期")
            
            return True
            
        except Exception as e:
            logger.error(f"添加免租期失败: contract_id={contract_id}, 错误={str(e)}")
            return False
    
    def _build_contract_from_dict(self, data: Dict[str, Any]) -> LeaseContract:
        """从字典构建合同对象"""
        contract = LeaseContract(
            contract_id=data['contract_id'],
            customer_name=data['customer_name'],
            room_number=data['room_number'],
            payment_name=data['payment_name'],
            eas_code=data['eas_code'],
            created_by=data['created_by'],
            area=data.get('area', 0.0),
            tax_rate=data.get('tax_rate', 0.05),
            need_adjust_income=bool(data.get('need_adjust_income', 0)),
            deposit_amount=data.get('deposit_amount', 0.0),
            create_time=datetime.datetime.fromisoformat(data['create_time']) if data.get('create_time') else datetime.datetime.now(),
            contract_type=data.get('contract_type', ContractType.NEW.value),
            original_contract_id=data.get('original_contract_id')
        )
        
        # 设置计算字段
        contract.total_rent = data.get('total_rent', 0.0)
        contract.initial_total_rent = data.get('initial_total_rent', 0.0)
        contract.initial_stamp_duty = data.get('initial_stamp_duty', 0.0)
        contract.is_effective = bool(data.get('is_effective', 0))
        
        if data.get('effective_date'):
            contract.effective_date = datetime.datetime.strptime(data['effective_date'], "%Y-%m-%d").date()
        
        return contract
    
    def _load_contract_relations(self, contract: LeaseContract):
        """加载合同关联数据"""
        # 加载租金期
        rent_periods = self.db.execute_query(
            "SELECT * FROM rent_periods WHERE contract_id = ? ORDER BY start_date",
            (contract.contract_id,)
        )
        for rp_data in rent_periods:
            rent_period = RentPeriod(
                start_date=datetime.datetime.strptime(rp_data['start_date'], "%Y-%m-%d").date(),
                end_date=datetime.datetime.strptime(rp_data['end_date'], "%Y-%m-%d").date(),
                monthly_rent=rp_data['monthly_rent'],
                id=rp_data['id']
            )
            contract.rent_periods.append(rent_period)
        
        # 加载免租期
        free_periods = self.db.execute_query(
            "SELECT * FROM free_periods WHERE contract_id = ? ORDER BY start_date",
            (contract.contract_id,)
        )
        for fp_data in free_periods:
            free_period = FreeRentPeriod(
                start_date=datetime.datetime.strptime(fp_data['start_date'], "%Y-%m-%d").date(),
                end_date=datetime.datetime.strptime(fp_data['end_date'], "%Y-%m-%d").date(),
                id=fp_data['id']
            )
            contract.free_rent_periods.append(free_period)
    
    def _check_period_overlap(self, new_period, existing_periods: List, period_type: str):
        """检查期间重叠"""
        for existing_period in existing_periods:
            is_overlap = (new_period.start_date <= existing_period.end_date) and \
                        (new_period.end_date >= existing_period.start_date)
            if is_overlap:
                raise ValueError(
                    f"新增{period_type}与已存在{period_type}重叠：\n"
                    f"已存在：{existing_period.start_date} ~ {existing_period.end_date}\n"
                    f"新添加：{new_period.start_date} ~ {new_period.end_date}"
                )
    