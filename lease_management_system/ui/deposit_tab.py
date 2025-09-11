"""
押金管理标签页UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from typing import List, Optional

from models.entities import User, DepositRecord, RecordType
from services.payment_service import PaymentService
from services.contract_service import ContractService
from utils.logging import get_logger

logger = get_logger("DepositTab")


class DepositTab(ttk.Frame):
    """押金管理标签页"""
    
    def __init__(self, parent, payment_service: PaymentService, 
                 contract_service: ContractService, current_user: User):
        super().__init__(parent)
        
        self.payment_service = payment_service
        self.contract_service = contract_service
        self.current_user = current_user
        self.deposit_records: List[DepositRecord] = []
        self.selected_record: Optional[DepositRecord] = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建左右分割的框架
        self._create_left_panel()
        self._create_right_panel()
    
    def _create_left_panel(self):
        """创建左侧面板（押金记录列表）"""
        # 左侧框架
        left_frame = ttk.Frame(self, width=600)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)
        
        # 标题
        ttk.Label(left_frame, text="押金记录列表", font=("SimHei", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # 搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        search_button = ttk.Button(search_frame, text="搜索", command=self._search_records)
        search_button.pack(side=tk.RIGHT)
        
        # 绑定搜索事件
        search_entry.bind('<KeyRelease>', lambda e: self._search_records())
        
        # 押金记录列表
        columns = ("date", "contract_id", "record_type", "amount", "created_by", "remark")
        self.deposit_tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        
        # 设置列标题和宽度
        self.deposit_tree.heading("date", text="日期")
        self.deposit_tree.heading("contract_id", text="合同ID")
        self.deposit_tree.heading("record_type", text="类型")
        self.deposit_tree.heading("amount", text="金额(元)")
        self.deposit_tree.heading("created_by", text="操作人")
        self.deposit_tree.heading("remark", text="备注")
        
        self.deposit_tree.column("date", width=100)
        self.deposit_tree.column("contract_id", width=80)
        self.deposit_tree.column("record_type", width=60)
        self.deposit_tree.column("amount", width=80, anchor=tk.E)
        self.deposit_tree.column("created_by", width=80)
        self.deposit_tree.column("remark", width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.deposit_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.deposit_tree.configure(yscrollcommand=scrollbar.set)
        self.deposit_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 绑定选择事件
        self.deposit_tree.bind('<<TreeviewSelect>>', self._on_record_select)
        
        # 操作按钮框架
        if self.current_user.can_edit():
            button_frame = ttk.Frame(left_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            ttk.Button(button_frame, text="新增押金记录", command=self._add_deposit_record).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="删除记录", command=self._delete_record).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="刷新", command=self.refresh).pack(side=tk.RIGHT)
    
    def _create_right_panel(self):
        """创建右侧面板（押金余额查询）"""
        # 右侧框架
        right_frame = ttk.Frame(self, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0), pady=5)
        right_frame.pack_propagate(False)
        
        # 标题
        ttk.Label(right_frame, text="押金余额查询", font=("SimHei", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # 查询框架
        query_frame = ttk.LabelFrame(right_frame, text="余额查询", padding="10")
        query_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 合同ID输入
        ttk.Label(query_frame, text="合同ID:").pack(anchor=tk.W, pady=(0, 5))
        self.query_contract_var = tk.StringVar()
        query_entry = ttk.Entry(query_frame, textvariable=self.query_contract_var)
        query_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 查询按钮
        ttk.Button(query_frame, text="查询余额", command=self._query_balance).pack(fill=tk.X)
        
        # 结果显示框架
        result_frame = ttk.LabelFrame(right_frame, text="查询结果", padding="10")
        result_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 合同信息显示
        ttk.Label(result_frame, text="客户姓名:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.customer_name_var = tk.StringVar()
        ttk.Label(result_frame, textvariable=self.customer_name_var, foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(result_frame, text="房间号:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.room_number_var = tk.StringVar()
        ttk.Label(result_frame, textvariable=self.room_number_var, foreground="blue").grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(result_frame, text="押金余额:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.balance_var = tk.StringVar()
        balance_label = ttk.Label(result_frame, textvariable=self.balance_var, foreground="red", font=("SimHei", 10, "bold"))
        balance_label.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 详细记录框架
        detail_frame = ttk.LabelFrame(right_frame, text="详细记录", padding="10")
        detail_frame.pack(fill=tk.BOTH, expand=True)
        
        # 详细记录列表
        detail_columns = ("date", "type", "amount")
        self.detail_tree = ttk.Treeview(detail_frame, columns=detail_columns, show="headings", height=8)
        
        self.detail_tree.heading("date", text="日期")
        self.detail_tree.heading("type", text="类型")
        self.detail_tree.heading("amount", text="金额(元)")
        
        self.detail_tree.column("date", width=80)
        self.detail_tree.column("type", width=50)
        self.detail_tree.column("amount", width=80, anchor=tk.E)
        
        # 详细记录滚动条
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient="vertical", command=self.detail_tree.yview)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_tree.configure(yscrollcommand=detail_scrollbar.set)
        self.detail_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    
    def _search_records(self):
        """搜索押金记录"""
        search_term = self.search_var.get().strip().lower()
        self._populate_record_list(search_term)
    
    def _populate_record_list(self, search_term: str = ""):
        """填充押金记录列表"""
        # 清空现有数据
        for item in self.deposit_tree.get_children():
            self.deposit_tree.delete(item)
        
        # 添加押金记录数据
        for record in self.deposit_records:
            # 搜索过滤
            if search_term:
                if (search_term not in record.contract_id.lower() and
                    search_term not in record.record_type.lower() and
                    search_term not in record.remark.lower()):
                    continue
            
            # 格式化显示
            amount_str = f"{record.amount:.2f}"
            if record.record_type == RecordType.RETURN.value:
                amount_str = f"-{amount_str}"
            
            self.deposit_tree.insert("", tk.END, values=(
                record.date.strftime("%Y-%m-%d"),
                record.contract_id,
                record.record_type,
                amount_str,
                record.created_by or "",
                record.remark
            ))
    
    def _on_record_select(self, event):
        """押金记录选择事件"""
        selection = self.deposit_tree.selection()
        if not selection:
            self.selected_record = None
            return
        
        # 获取选中的记录
        item = selection[0]
        values = self.deposit_tree.item(item, "values")
        date_str = values[0]
        contract_id = values[1]
        
        # 查找对应的记录对象
        self.selected_record = next(
            (r for r in self.deposit_records 
             if r.contract_id == contract_id and r.date.strftime("%Y-%m-%d") == date_str),
            None
        )
    
    def _add_deposit_record(self):
        """添加押金记录"""
        dialog = DepositRecordDialog(self, self.contract_service)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                contract_id, record_type, amount, remark, date = dialog.result
                
                # 检查押金余额（如果是退还）
                current_balance = 0.0
                if record_type == RecordType.RETURN.value:
                    current_balance = self.payment_service.get_deposit_balance(contract_id)
                
                # 创建押金记录
                deposit_record = DepositRecord(
                    date=date,
                    amount=amount,
                    contract_id=contract_id,
                    record_type=record_type,
                    remark=remark
                )
                
                # 保存记录
                if self.payment_service.add_deposit_record(deposit_record, self.current_user.username, current_balance):
                    messagebox.showinfo("成功", "押金记录添加成功")
                    self.refresh()
                else:
                    messagebox.showerror("错误", "添加押金记录失败")
                    
            except Exception as e:
                messagebox.showerror("错误", f"添加押金记录失败: {str(e)}")
    
    def _delete_record(self):
        """删除选中的押金记录"""
        if not self.selected_record:
            messagebox.showwarning("提示", "请先选择一条记录")
            return
        
        if messagebox.askyesno("确认", f"确定要删除这条押金记录吗？\n日期：{self.selected_record.date}\n合同ID：{self.selected_record.contract_id}\n金额：{self.selected_record.amount:.2f}元"):
            try:
                if self.payment_service.delete_deposit_record(self.selected_record.id, self.current_user.username):
                    messagebox.showinfo("成功", "押金记录删除成功")
                    self.refresh()
                else:
                    messagebox.showerror("错误", "删除押金记录失败")
            except Exception as e:
                messagebox.showerror("错误", f"删除押金记录失败: {str(e)}")
    
    def _query_balance(self):
        """查询押金余额"""
        contract_id = self.query_contract_var.get().strip()
        if not contract_id:
            messagebox.showwarning("提示", "请输入合同ID")
            return
        
        try:
            # 获取合同信息
            contract = self.contract_service.get_contract_by_id(contract_id)
            if not contract:
                messagebox.showwarning("提示", "合同不存在")
                self._clear_query_result()
                return
            
            # 显示合同基本信息
            self.customer_name_var.set(contract.customer_name)
            self.room_number_var.set(contract.room_number)
            
            # 获取押金余额
            balance = self.payment_service.get_deposit_balance(contract_id)
            self.balance_var.set(f"{balance:.2f} 元")
            
            # 获取详细记录
            deposit_records = self.payment_service.get_deposit_records(contract_id)
            
            # 清空详细记录列表
            for item in self.detail_tree.get_children():
                self.detail_tree.delete(item)
            
            # 填充详细记录
            for record in deposit_records:
                amount_str = f"{record.amount:.2f}"
                if record.record_type == RecordType.RETURN.value:
                    amount_str = f"-{amount_str}"
                
                self.detail_tree.insert("", tk.END, values=(
                    record.date.strftime("%Y-%m-%d"),
                    record.record_type,
                    amount_str
                ))
                
        except Exception as e:
            logger.error(f"查询押金余额失败: {str(e)}")
            messagebox.showerror("错误", f"查询失败: {str(e)}")
            self._clear_query_result()
    
    def _clear_query_result(self):
        """清空查询结果"""
        self.customer_name_var.set("")
        self.room_number_var.set("")
        self.balance_var.set("")
        
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
    
    def refresh(self):
        """刷新数据"""
        try:
            self.deposit_records = self.payment_service.get_deposit_records()
            self._populate_record_list()
            self.selected_record = None
        except Exception as e:
            logger.error(f"刷新押金数据失败: {str(e)}")
            messagebox.showerror("错误", f"刷新数据失败: {str(e)}")


class DepositRecordDialog(tk.Toplevel):
    """押金记录对话框"""
    
    def __init__(self, parent, contract_service: ContractService):
        super().__init__(parent)
        
        self.parent = parent
        self.contract_service = contract_service
        self.result = None
        
        # 配置对话框
        self.title("新增押金记录")
        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._center_window()
        
        # 绑定快捷键
        self.bind('<Return>', lambda e: self._save())
        self.bind('<Escape>', lambda e: self._cancel())
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表单框架
        form_frame = ttk.LabelFrame(main_frame, text="押金记录信息", padding="15")
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 合同ID
        ttk.Label(form_frame, text="合同ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.contract_id_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.contract_id_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 记录类型
        ttk.Label(form_frame, text="记录类型:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.record_type_var = tk.StringVar()
        type_combo = ttk.Combobox(
            form_frame,
            textvariable=self.record_type_var,
            values=[RecordType.RECEIVE.value, RecordType.RETURN.value],
            state="readonly",
            width=18
        )
        type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        type_combo.set(RecordType.RECEIVE.value)  # 默认选择收取
        
        # 金额
        ttk.Label(form_frame, text="金额(元):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 日期
        ttk.Label(form_frame, text="日期:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        date_frame = ttk.Frame(form_frame)
        date_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.day_var = tk.StringVar()
        
        # 年份
        ttk.Label(date_frame, text="年:").pack(side=tk.LEFT)
        year_combo = ttk.Combobox(
            date_frame,
            textvariable=self.year_var,
            values=[str(year) for year in range(2020, 2030)],
            width=6,
            state="readonly"
        )
        year_combo.pack(side=tk.LEFT, padx=2)
        
        # 月份
        ttk.Label(date_frame, text="月:").pack(side=tk.LEFT, padx=(10, 0))
        month_combo = ttk.Combobox(
            date_frame,
            textvariable=self.month_var,
            values=[f"{month:02d}" for month in range(1, 13)],
            width=4,
            state="readonly"
        )
        month_combo.pack(side=tk.LEFT, padx=2)
        
        # 日期
        ttk.Label(date_frame, text="日:").pack(side=tk.LEFT, padx=(10, 0))
        day_combo = ttk.Combobox(
            date_frame,
            textvariable=self.day_var,
            values=[f"{day:02d}" for day in range(1, 32)],
            width=4,
            state="readonly"
        )
        day_combo.pack(side=tk.LEFT, padx=2)
        
        # 备注
        ttk.Label(form_frame, text="备注:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.remark_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.remark_var, width=30).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 错误消息标签
        self.message_var = tk.StringVar()
        message_label = ttk.Label(
            form_frame,
            textvariable=self.message_var,
            foreground="red",
            font=("SimHei", 9)
        )
        message_label.grid(row=5, column=0, columnspan=2, pady=10)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 保存按钮
        ttk.Button(button_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.LEFT)
        
        # 设置默认值
        today = datetime.date.today()
        self.year_var.set(str(today.year))
        self.month_var.set(f"{today.month:02d}")
        self.day_var.set(f"{today.day:02d}")
    
    def _center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"+{x}+{y}")
    
    def _validate_input(self) -> bool:
        """验证输入数据"""
        try:
            self.message_var.set("")
            
            # 验证合同ID
            contract_id = self.contract_id_var.get().strip()
            if not contract_id:
                self.message_var.set("请输入合同ID")
                return False
            
            # 验证合同是否存在
            contract = self.contract_service.get_contract_by_id(contract_id)
            if not contract:
                self.message_var.set("合同不存在")
                return False
            
            # 验证金额
            try:
                amount = float(self.amount_var.get())
                if amount <= 0:
                    self.message_var.set("金额必须大于0")
                    return False
            except ValueError:
                self.message_var.set("金额必须是有效数字")
                return False
            
            # 验证日期
            try:
                year = int(self.year_var.get())
                month = int(self.month_var.get())
                day = int(self.day_var.get())
                datetime.date(year, month, day)
            except ValueError:
                self.message_var.set("日期格式错误")
                return False
            
            return True
            
        except Exception as e:
            self.message_var.set(f"验证失败: {str(e)}")
            return False
    
    def _save(self):
        """保存数据"""
        if not self._validate_input():
            return
        
        try:
            contract_id = self.contract_id_var.get().strip()
            record_type = self.record_type_var.get()
            amount = float(self.amount_var.get())
            remark = self.remark_var.get().strip()
            
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            date = datetime.date(year, month, day)
            
            self.result = (contract_id, record_type, amount, remark, date)
            self.destroy()
            
        except Exception as e:
            self.message_var.set(f"保存失败: {str(e)}")
    
    def _cancel(self):
        """取消编辑"""
        self.result = None
        self.destroy()