"""
合同编辑对话框UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from typing import Optional, Dict, Any

from models.entities import LeaseContract, User, ContractType
from utils.logging import get_logger

logger = get_logger("ContractDialog")


class ContractDialog(tk.Toplevel):
    """合同编辑对话框"""
    
    def __init__(self, parent, contract: Optional[LeaseContract], current_user: User):
        super().__init__(parent)
        
        self.parent = parent
        self.contract = contract
        self.current_user = current_user
        self.result: Optional[Dict[str, Any]] = None
        
        # 配置对话框
        self.title("编辑合同" if contract else "新增合同")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # 创建界面
        self._create_widgets()
        self._load_data()
        self._center_window()
        
        # 绑定回车键
        self.bind('<Return>', lambda e: self._save())
        self.bind('<Escape>', lambda e: self._cancel())
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动框架
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 基本信息组
        basic_frame = ttk.LabelFrame(scrollable_frame, text="基本信息", padding="10")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 合同ID
        ttk.Label(basic_frame, text="合同ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.contract_id_var = tk.StringVar()
        contract_id_entry = ttk.Entry(basic_frame, textvariable=self.contract_id_var, width=20)
        contract_id_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 客户姓名
        ttk.Label(basic_frame, text="客户姓名:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.customer_name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.customer_name_var, width=20).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 房间号
        ttk.Label(basic_frame, text="房间号:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.room_number_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.room_number_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 租赁面积
        ttk.Label(basic_frame, text="租赁面积(m²):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.area_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.area_var, width=20).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 对方付款名称
        ttk.Label(basic_frame, text="对方付款名称:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.payment_name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.payment_name_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # EAS代码
        ttk.Label(basic_frame, text="EAS代码:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.eas_code_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.eas_code_var, width=20).grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 财务信息组
        finance_frame = ttk.LabelFrame(scrollable_frame, text="财务信息", padding="10")
        finance_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 税率
        ttk.Label(finance_frame, text="税率(%):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.tax_rate_var = tk.StringVar()
        ttk.Entry(finance_frame, textvariable=self.tax_rate_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 需要调整收入
        ttk.Label(finance_frame, text="需要调整收入:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.need_adjust_var = tk.BooleanVar()
        ttk.Checkbutton(finance_frame, variable=self.need_adjust_var).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 合同押金
        ttk.Label(finance_frame, text="合同押金(元):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.deposit_amount_var = tk.StringVar()
        ttk.Entry(finance_frame, textvariable=self.deposit_amount_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 合同类型组
        type_frame = ttk.LabelFrame(scrollable_frame, text="合同类型", padding="10")
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 合同类型
        ttk.Label(type_frame, text="合同类型:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.contract_type_var = tk.StringVar()
        contract_type_combo = ttk.Combobox(
            type_frame, 
            textvariable=self.contract_type_var,
            values=[e.value for e in ContractType],
            state="readonly",
            width=18
        )
        contract_type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        contract_type_combo.bind('<<ComboboxSelected>>', self._on_contract_type_change)
        
        # 原合同ID（续租/变更时显示）
        ttk.Label(type_frame, text="原合同ID:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.original_contract_id_var = tk.StringVar()
        self.original_contract_entry = ttk.Entry(type_frame, textvariable=self.original_contract_id_var, width=20)
        self.original_contract_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 保存按钮
        ttk.Button(button_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.LEFT)
        
        # 如果是编辑模式，禁用合同ID输入
        if self.contract:
            contract_id_entry.config(state="readonly")
    
    def _on_contract_type_change(self, event):
        """合同类型改变事件"""
        contract_type = self.contract_type_var.get()
        
        # 根据合同类型决定是否显示原合同ID字段
        if contract_type in [ContractType.RENEWAL.value, ContractType.CHANGE.value]:
            self.original_contract_entry.config(state="normal")
        else:
            self.original_contract_entry.config(state="disabled")
            self.original_contract_id_var.set("")
    
    def _load_data(self):
        """加载数据到表单"""
        if self.contract:
            # 编辑模式，加载现有数据
            self.contract_id_var.set(self.contract.contract_id)
            self.customer_name_var.set(self.contract.customer_name)
            self.room_number_var.set(self.contract.room_number)
            self.area_var.set(str(self.contract.area))
            self.payment_name_var.set(self.contract.payment_name)
            self.eas_code_var.set(self.contract.eas_code)
            self.tax_rate_var.set(str(self.contract.tax_rate * 100))
            self.need_adjust_var.set(self.contract.need_adjust_income)
            self.deposit_amount_var.set(str(self.contract.deposit_amount))
            self.contract_type_var.set(self.contract.contract_type)
            
            if self.contract.original_contract_id:
                self.original_contract_id_var.set(self.contract.original_contract_id)
        else:
            # 新增模式，设置默认值
            self.tax_rate_var.set("5.0")  # 默认税率5%
            self.contract_type_var.set(ContractType.NEW.value)
            self.area_var.set("0.0")
            self.deposit_amount_var.set("0.0")
        
        # 触发合同类型变更事件
        self._on_contract_type_change(None)
    
    def _center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        
        # 获取窗口尺寸
        width = self.winfo_width()
        height = self.winfo_height()
        
        # 获取屏幕尺寸
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _validate_input(self) -> bool:
        """验证输入数据"""
        try:
            # 验证必填字段
            if not self.contract_id_var.get().strip():
                messagebox.showerror("错误", "合同ID不能为空")
                return False
            
            if not self.customer_name_var.get().strip():
                messagebox.showerror("错误", "客户姓名不能为空")
                return False
            
            if not self.room_number_var.get().strip():
                messagebox.showerror("错误", "房间号不能为空")
                return False
            
            if not self.payment_name_var.get().strip():
                messagebox.showerror("错误", "对方付款名称不能为空")
                return False
            
            if not self.eas_code_var.get().strip():
                messagebox.showerror("错误", "EAS代码不能为空")
                return False
            
            # 验证数值字段
            try:
                area = float(self.area_var.get())
                if area < 0:
                    messagebox.showerror("错误", "租赁面积不能为负数")
                    return False
            except ValueError:
                messagebox.showerror("错误", "租赁面积必须是有效数字")
                return False
            
            try:
                tax_rate = float(self.tax_rate_var.get())
                if tax_rate < 0 or tax_rate > 100:
                    messagebox.showerror("错误", "税率必须在0-100%之间")
                    return False
            except ValueError:
                messagebox.showerror("错误", "税率必须是有效数字")
                return False
            
            try:
                deposit_amount = float(self.deposit_amount_var.get())
                if deposit_amount < 0:
                    messagebox.showerror("错误", "押金金额不能为负数")
                    return False
            except ValueError:
                messagebox.showerror("错误", "押金金额必须是有效数字")
                return False
            
            # 验证合同类型相关字段
            contract_type = self.contract_type_var.get()
            if contract_type in [ContractType.RENEWAL.value, ContractType.CHANGE.value]:
                if not self.original_contract_id_var.get().strip():
                    messagebox.showerror("错误", "续租/变更类型合同必须指定原合同ID")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"输入验证失败: {str(e)}")
            messagebox.showerror("错误", f"输入验证失败: {str(e)}")
            return False
    
    def _save(self):
        """保存数据"""
        if not self._validate_input():
            return
        
        try:
            # 构建结果数据
            self.result = {
                "contract_id": self.contract_id_var.get().strip(),
                "customer_name": self.customer_name_var.get().strip(),
                "room_number": self.room_number_var.get().strip(),
                "area": float(self.area_var.get()),
                "payment_name": self.payment_name_var.get().strip(),
                "eas_code": self.eas_code_var.get().strip(),
                "tax_rate": float(self.tax_rate_var.get()) / 100,  # 转换为小数
                "need_adjust_income": self.need_adjust_var.get(),
                "deposit_amount": float(self.deposit_amount_var.get()),
                "contract_type": self.contract_type_var.get(),
                "original_contract_id": self.original_contract_id_var.get().strip() or None
            }
            
            logger.info(f"合同数据保存: {self.result}")
            self.destroy()
            
        except Exception as e:
            logger.error(f"保存合同数据失败: {str(e)}")
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def _cancel(self):
        """取消编辑"""
        self.result = None
        self.destroy()
