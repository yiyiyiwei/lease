"""
收款开票标签页UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from typing import List, Optional

from models.entities import User, PaymentRecord, InvoiceRecord
from services.payment_service import PaymentService
from services.contract_service import ContractService
from utils.logging import get_logger

logger = get_logger("PaymentTab")


class PaymentTab(ttk.Frame):
    """收款开票标签页"""
    
    def __init__(self, parent, payment_service: PaymentService, 
                 contract_service: ContractService, current_user: User):
        super().__init__(parent)
        
        self.payment_service = payment_service
        self.contract_service = contract_service
        self.current_user = current_user
        self.payment_records: List[PaymentRecord] = []
        self.invoice_records: List[InvoiceRecord] = []
        self.selected_payment: Optional[PaymentRecord] = None
        self.selected_invoice: Optional[InvoiceRecord] = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建笔记本组件用于多个标签页
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 收款记录标签页
        self._create_payment_tab()
        
        # 开票记录标签页
        self._create_invoice_tab()
    
    def _create_payment_tab(self):
        """创建收款记录标签页"""
        payment_frame = ttk.Frame(self.notebook)
        self.notebook.add(payment_frame, text="收款记录")
        
        # 标题和操作按钮
        header_frame = ttk.Frame(payment_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="收款记录列表", font=("SimHei", 12, "bold")).pack(side=tk.LEFT)
        
        if self.current_user.can_edit():
            button_frame = ttk.Frame(header_frame)
            button_frame.pack(side=tk.RIGHT)
            
            ttk.Button(button_frame, text="新增收款", command=self._add_payment_record).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="删除记录", command=self._delete_payment_record).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="刷新", command=self.refresh).pack(side=tk.LEFT)
        
        # 搜索框
        search_frame = ttk.Frame(payment_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.payment_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.payment_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        search_button = ttk.Button(search_frame, text="搜索", command=self._search_payments)
        search_button.pack(side=tk.RIGHT)
        
        # 绑定搜索事件
        search_entry.bind('<KeyRelease>', lambda e: self._search_payments())
        
        # 收款记录列表
        payment_columns = ("date", "contract_id", "amount", "payment_type", "created_by")
        self.payment_tree = ttk.Treeview(payment_frame, columns=payment_columns, show="headings", selectmode="browse")
        
        # 设置列标题和宽度
        self.payment_tree.heading("date", text="日期")
        self.payment_tree.heading("contract_id", text="合同ID")
        self.payment_tree.heading("amount", text="金额(元)")
        self.payment_tree.heading("payment_type", text="付款类型")
        self.payment_tree.heading("created_by", text="操作人")
        
        self.payment_tree.column("date", width=100)
        self.payment_tree.column("contract_id", width=100)
        self.payment_tree.column("amount", width=100, anchor=tk.E)
        self.payment_tree.column("payment_type", width=100)
        self.payment_tree.column("created_by", width=100)
        
        # 滚动条
        payment_scrollbar = ttk.Scrollbar(payment_frame, orient="vertical", command=self.payment_tree.yview)
        payment_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.payment_tree.configure(yscrollcommand=payment_scrollbar.set)
        self.payment_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 绑定选择事件
        self.payment_tree.bind('<<TreeviewSelect>>', self._on_payment_select)
    
    def _create_invoice_tab(self):
        """创建开票记录标签页"""
        invoice_frame = ttk.Frame(self.notebook)
        self.notebook.add(invoice_frame, text="开票记录")
        
        # 标题和操作按钮
        header_frame = ttk.Frame(invoice_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="开票记录列表", font=("SimHei", 12, "bold")).pack(side=tk.LEFT)
        
        if self.current_user.can_edit():
            button_frame = ttk.Frame(header_frame)
            button_frame.pack(side=tk.RIGHT)
            
            ttk.Button(button_frame, text="新增开票", command=self._add_invoice_record).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="删除记录", command=self._delete_invoice_record).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="刷新", command=self.refresh).pack(side=tk.LEFT)
        
        # 搜索框
        search_frame = ttk.Frame(invoice_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.invoice_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.invoice_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        search_button = ttk.Button(search_frame, text="搜索", command=self._search_invoices)
        search_button.pack(side=tk.RIGHT)
        
        # 绑定搜索事件
        search_entry.bind('<KeyRelease>', lambda e: self._search_invoices())
        
        # 开票记录列表
        invoice_columns = ("date", "contract_id", "invoice_number", "amount", "tax_amount", "created_by")
        self.invoice_tree = ttk.Treeview(invoice_frame, columns=invoice_columns, show="headings", selectmode="browse")
        
        # 设置列标题和宽度
        self.invoice_tree.heading("date", text="日期")
        self.invoice_tree.heading("contract_id", text="合同ID")
        self.invoice_tree.heading("invoice_number", text="发票号")
        self.invoice_tree.heading("amount", text="开票金额(元)")
        self.invoice_tree.heading("tax_amount", text="税额(元)")
        self.invoice_tree.heading("created_by", text="操作人")
        
        self.invoice_tree.column("date", width=100)
        self.invoice_tree.column("contract_id", width=100)
        self.invoice_tree.column("invoice_number", width=120)
        self.invoice_tree.column("amount", width=100, anchor=tk.E)
        self.invoice_tree.column("tax_amount", width=80, anchor=tk.E)
        self.invoice_tree.column("created_by", width=100)
        
        # 滚动条
        invoice_scrollbar = ttk.Scrollbar(invoice_frame, orient="vertical", command=self.invoice_tree.yview)
        invoice_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.invoice_tree.configure(yscrollcommand=invoice_scrollbar.set)
        self.invoice_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 绑定选择事件
        self.invoice_tree.bind('<<TreeviewSelect>>', self._on_invoice_select)
    
    def _search_payments(self):
        """搜索收款记录"""
        search_term = self.payment_search_var.get().strip().lower()
        self._populate_payment_list(search_term)
    
    def _search_invoices(self):
        """搜索开票记录"""
        search_term = self.invoice_search_var.get().strip().lower()
        self._populate_invoice_list(search_term)
    
    def _populate_payment_list(self, search_term: str = ""):
        """填充收款记录列表"""
        # 清空现有数据
        for item in self.payment_tree.get_children():
            self.payment_tree.delete(item)
        
        # 添加收款记录数据
        for record in self.payment_records:
            # 搜索过滤
            if search_term:
                if (search_term not in record.contract_id.lower() and
                    search_term not in record.payment_type.lower()):
                    continue
            
            self.payment_tree.insert("", tk.END, values=(
                record.date.strftime("%Y-%m-%d"),
                record.contract_id,
                f"{record.amount:.2f}",
                record.payment_type,
                record.created_by or ""
            ))
    
    def _populate_invoice_list(self, search_term: str = ""):
        """填充开票记录列表"""
        # 清空现有数据
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)
        
        # 添加开票记录数据
        for record in self.invoice_records:
            # 搜索过滤
            if search_term:
                if (search_term not in record.contract_id.lower() and
                    search_term not in record.invoice_number.lower()):
                    continue
            
            self.invoice_tree.insert("", tk.END, values=(
                record.date.strftime("%Y-%m-%d"),
                record.contract_id,
                record.invoice_number,
                f"{record.amount:.2f}",
                f"{record.tax_amount:.2f}",
                record.created_by or ""
            ))
    
    def _on_payment_select(self, event):
        """收款记录选择事件"""
        selection = self.payment_tree.selection()
        if not selection:
            self.selected_payment = None
            return
        
        # 获取选中的记录
        item = selection[0]
        values = self.payment_tree.item(item, "values")
        date_str = values[0]
        contract_id = values[1]
        amount_str = values[2]
        
        # 查找对应的记录对象
        self.selected_payment = next(
            (r for r in self.payment_records 
             if (r.contract_id == contract_id and 
                 r.date.strftime("%Y-%m-%d") == date_str and
                 f"{r.amount:.2f}" == amount_str)),
            None
        )
    
    def _on_invoice_select(self, event):
        """开票记录选择事件"""
        selection = self.invoice_tree.selection()
        if not selection:
            self.selected_invoice = None
            return
        
        # 获取选中的记录
        item = selection[0]
        values = self.invoice_tree.item(item, "values")
        date_str = values[0]
        contract_id = values[1]
        invoice_number = values[2]
        
        # 查找对应的记录对象
        self.selected_invoice = next(
            (r for r in self.invoice_records 
             if (r.contract_id == contract_id and 
                 r.date.strftime("%Y-%m-%d") == date_str and
                 r.invoice_number == invoice_number)),
            None
        )
    
    def _add_payment_record(self):
        """添加收款记录"""
        dialog = PaymentRecordDialog(self, self.contract_service)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                contract_id, payment_type, amount, date = dialog.result
                
                # 创建收款记录
                payment_record = PaymentRecord(
                    date=date,
                    amount=amount,
                    contract_id=contract_id,
                    payment_type=payment_type
                )
                
                # 保存记录
                if self.payment_service.add_payment_record(payment_record, self.current_user.username):
                    messagebox.showinfo("成功", "收款记录添加成功")
                    self.refresh()
                else:
                    messagebox.showerror("错误", "添加收款记录失败")
                    
            except Exception as e:
                messagebox.showerror("错误", f"添加收款记录失败: {str(e)}")
    
    def _add_invoice_record(self):
        """添加开票记录"""
        dialog = InvoiceRecordDialog(self, self.contract_service)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                contract_id, invoice_number, amount, tax_amount, date = dialog.result
                
                # 创建开票记录
                invoice_record = InvoiceRecord(
                    date=date,
                    amount=amount,
                    tax_amount=tax_amount,
                    invoice_number=invoice_number,
                    contract_id=contract_id
                )
                
                # 保存记录
                if self.payment_service.add_invoice_record(invoice_record, self.current_user.username):
                    messagebox.showinfo("成功", "开票记录添加成功")
                    self.refresh()
                else:
                    messagebox.showerror("错误", "添加开票记录失败")
                    
            except Exception as e:
                messagebox.showerror("错误", f"添加开票记录失败: {str(e)}")
    
    def _delete_payment_record(self):
        """删除选中的收款记录"""
        if not self.selected_payment:
            messagebox.showwarning("提示", "请先选择一条收款记录")
            return
        
        if messagebox.askyesno("确认", f"确定要删除这条收款记录吗？\n日期：{self.selected_payment.date}\n合同ID：{self.selected_payment.contract_id}\n金额：{self.selected_payment.amount:.2f}元"):
            try:
                if self.payment_service.delete_payment_record(self.selected_payment.id, self.current_user.username):
                    messagebox.showinfo("成功", "收款记录删除成功")
                    self.refresh()
                else:
                    messagebox.showerror("错误", "删除收款记录失败")
            except Exception as e:
                messagebox.showerror("错误", f"删除收款记录失败: {str(e)}")
    
    def _delete_invoice_record(self):
        """删除选中的开票记录"""
        if not self.selected_invoice:
            messagebox.showwarning("提示", "请先选择一条开票记录")
            return
        
        if messagebox.askyesno("确认", f"确定要删除这条开票记录吗？\n发票号：{self.selected_invoice.invoice_number}\n合同ID：{self.selected_invoice.contract_id}\n金额：{self.selected_invoice.amount:.2f}元"):
            try:
                if self.payment_service.delete_invoice_record(self.selected_invoice.id, self.current_user.username):
                    messagebox.showinfo("成功", "开票记录删除成功")
                    self.refresh()
                else:
                    messagebox.showerror("错误", "删除开票记录失败")
            except Exception as e:
                messagebox.showerror("错误", f"删除开票记录失败: {str(e)}")
    
    def refresh(self):
        """刷新数据"""
        try:
            self.payment_records = self.payment_service.get_payment_records()
            self.invoice_records = self.payment_service.get_invoice_records()
            self._populate_payment_list()
            self._populate_invoice_list()
            self.selected_payment = None
            self.selected_invoice = None
        except Exception as e:
            logger.error(f"刷新收款开票数据失败: {str(e)}")
            messagebox.showerror("错误", f"刷新数据失败: {str(e)}")


class PaymentRecordDialog(tk.Toplevel):
    """收款记录对话框"""
    
    def __init__(self, parent, contract_service: ContractService):
        super().__init__(parent)
        
        self.parent = parent
        self.contract_service = contract_service
        self.result = None
        
        # 配置对话框
        self.title("新增收款记录")
        self.geometry("400x300")
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
        form_frame = ttk.LabelFrame(main_frame, text="收款记录信息", padding="15")
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 合同ID
        ttk.Label(form_frame, text="合同ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.contract_id_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.contract_id_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 付款类型
        ttk.Label(form_frame, text="付款类型:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.payment_type_var = tk.StringVar()
        type_combo = ttk.Combobox(
            form_frame,
            textvariable=self.payment_type_var,
            values=["租金", "押金", "其他"],
            width=18
        )
        type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        type_combo.set("租金")  # 默认选择租金
        
        # 金额
        ttk.Label(form_frame, text="金额(元):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 日期选择
        ttk.Label(form_frame, text="日期:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self._create_date_selector(form_frame, 3, 1)
        
        # 错误消息标签
        self.message_var = tk.StringVar()
        message_label = ttk.Label(
            form_frame,
            textvariable=self.message_var,
            foreground="red",
            font=("SimHei", 9)
        )
        message_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 保存按钮
        ttk.Button(button_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.LEFT)
    
    def _create_date_selector(self, parent, row, column):
        """创建日期选择器"""
        date_frame = ttk.Frame(parent)
        date_frame.grid(row=row, column=column, sticky=tk.W, padx=5, pady=5)
        
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
            
            # 验证付款类型
            if not self.payment_type_var.get().strip():
                self.message_var.set("请选择付款类型")
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
            payment_type = self.payment_type_var.get().strip()
            amount = float(self.amount_var.get())
            
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            date = datetime.date(year, month, day)
            
            self.result = (contract_id, payment_type, amount, date)
            self.destroy()
            
        except Exception as e:
            self.message_var.set(f"保存失败: {str(e)}")
    
    def _cancel(self):
        """取消编辑"""
        self.result = None
        self.destroy()


class InvoiceRecordDialog(tk.Toplevel):
    """开票记录对话框"""
    
    def __init__(self, parent, contract_service: ContractService):
        super().__init__(parent)
        
        self.parent = parent
        self.contract_service = contract_service
        self.result = None
        
        # 配置对话框
        self.title("新增开票记录")
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
        form_frame = ttk.LabelFrame(main_frame, text="开票记录信息", padding="15")
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 合同ID
        ttk.Label(form_frame, text="合同ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.contract_id_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.contract_id_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 发票号
        ttk.Label(form_frame, text="发票号:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.invoice_number_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.invoice_number_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 开票金额
        ttk.Label(form_frame, text="开票金额(元):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.amount_var = tk.StringVar()
        amount_entry = ttk.Entry(form_frame, textvariable=self.amount_var, width=20)
        amount_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        amount_entry.bind('<KeyRelease>', self._calculate_tax)
        
        # 税额
        ttk.Label(form_frame, text="税额(元):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.tax_amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.tax_amount_var, width=20).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 日期选择
        ttk.Label(form_frame, text="日期:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self._create_date_selector(form_frame, 4, 1)
        
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
    
    def _create_date_selector(self, parent, row, column):
        """创建日期选择器"""
        date_frame = ttk.Frame(parent)
        date_frame.grid(row=row, column=column, sticky=tk.W, padx=5, pady=5)
        
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
        
        # 设置默认值
        today = datetime.date.today()
        self.year_var.set(str(today.year))
        self.month_var.set(f"{today.month:02d}")
        self.day_var.set(f"{today.day:02d}")
    
    def _calculate_tax(self, event=None):
        """自动计算税额"""
        try:
            amount = float(self.amount_var.get())
            # 假设税率为5%（可以从配置中获取）
            tax_amount = amount * 0.05
            self.tax_amount_var.set(f"{tax_amount:.2f}")
        except ValueError:
            self.tax_amount_var.set("")
    
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
            
            # 验证发票号
            if not self.invoice_number_var.get().strip():
                self.message_var.set("请输入发票号")
                return False
            
            # 验证开票金额
            try:
                amount = float(self.amount_var.get())
                if amount <= 0:
                    self.message_var.set("开票金额必须大于0")
                    return False
            except ValueError:
                self.message_var.set("开票金额必须是有效数字")
                return False
            
            # 验证税额
            try:
                tax_amount = float(self.tax_amount_var.get())
                if tax_amount < 0:
                    self.message_var.set("税额不能为负数")
                    return False
            except ValueError:
                self.message_var.set("税额必须是有效数字")
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
            invoice_number = self.invoice_number_var.get().strip()
            amount = float(self.amount_var.get())
            tax_amount = float(self.tax_amount_var.get())
            
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            date = datetime.date(year, month, day)
            
            self.result = (contract_id, invoice_number, amount, tax_amount, date)
            self.destroy()
            
        except Exception as e:
            self.message_var.set(f"保存失败: {str(e)}")
    
    def _cancel(self):
        """取消编辑"""
        self.result = None
        self.destroy()
