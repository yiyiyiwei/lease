"""
月度报告标签页UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
from typing import Dict, Any, List

from models.entities import User
from services.contract_service import ContractService
from services.payment_service import PaymentService
from utils.logging import get_logger

logger = get_logger("ReportTab")


class ReportTab(ttk.Frame):
    """月度报告标签页"""
    
    def __init__(self, parent, contract_service: ContractService, 
                 payment_service: PaymentService, current_user: User):
        super().__init__(parent)
        
        self.contract_service = contract_service
        self.payment_service = payment_service
        self.current_user = current_user
        
        self._create_widgets()
        self._load_current_month()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建左右分割的框架
        self._create_left_panel()
        self._create_right_panel()
    
    def _create_left_panel(self):
        """创建左侧面板（查询条件）"""
        # 左侧框架
        left_frame = ttk.Frame(self, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 5), pady=5)
        left_frame.pack_propagate(False)
        
        # 标题
        ttk.Label(left_frame, text="报告查询", font=("SimHei", 12, "bold")).pack(anchor=tk.W, pady=(0, 20))
        
        # 查询条件框架
        query_frame = ttk.LabelFrame(left_frame, text="查询条件", padding="15")
        query_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 年份选择
        ttk.Label(query_frame, text="年份:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.year_var = tk.StringVar()
        year_combo = ttk.Combobox(
            query_frame,
            textvariable=self.year_var,
            values=[str(year) for year in range(2020, 2030)],
            width=10,
            state="readonly"
        )
        year_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 月份选择
        ttk.Label(query_frame, text="月份:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.month_var = tk.StringVar()
        month_combo = ttk.Combobox(
            query_frame,
            textvariable=self.month_var,
            values=[f"{month:02d}" for month in range(1, 13)],
            width=10,
            state="readonly"
        )
        month_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 查询按钮
        query_button = ttk.Button(query_frame, text="生成报告", command=self._generate_report)
        query_button.grid(row=2, column=0, columnspan=2, pady=(15, 0), sticky=tk.EW)
        
        # 导出按钮框架
        export_frame = ttk.LabelFrame(left_frame, text="报告导出", padding="15")
        export_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Button(export_frame, text="导出为Excel", command=self._export_excel).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(export_frame, text="导出为PDF", command=self._export_pdf).pack(fill=tk.X)
        
        # 统计信息框架
        stats_frame = ttk.LabelFrame(left_frame, text="统计信息", padding="15")
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # 统计数据显示
        ttk.Label(stats_frame, text="总合同数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.total_contracts_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.total_contracts_var, foreground="blue").grid(row=0, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(stats_frame, text="有效合同数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.effective_contracts_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.effective_contracts_var, foreground="green").grid(row=1, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(stats_frame, text="总租金收入:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.total_rent_var = tk.StringVar(value="0.00元")
        ttk.Label(stats_frame, textvariable=self.total_rent_var, foreground="red").grid(row=2, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(stats_frame, text="押金余额:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.deposit_balance_var = tk.StringVar(value="0.00元")
        ttk.Label(stats_frame, textvariable=self.deposit_balance_var, foreground="orange").grid(row=3, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(stats_frame, text="开票总额:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.invoice_total_var = tk.StringVar(value="0.00元")
        ttk.Label(stats_frame, textvariable=self.invoice_total_var, foreground="purple").grid(row=4, column=1, sticky=tk.E, pady=2)
    
    def _create_right_panel(self):
        """创建右侧面板（报告内容）"""
        # 右侧框架
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        
        # 标题
        self.report_title_var = tk.StringVar(value="月度报告")
        title_label = ttk.Label(right_frame, textvariable=self.report_title_var, font=("SimHei", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建笔记本组件用于多个报告页面
        self.report_notebook = ttk.Notebook(right_frame)
        self.report_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 收款明细标签页
        self._create_payment_detail_tab()
        
        # 押金明细标签页
        self._create_deposit_detail_tab()
        
        # 开票明细标签页
        self._create_invoice_detail_tab()
        
        # 合同统计标签页
        self._create_contract_stats_tab()
    
    def _create_payment_detail_tab(self):
        """创建收款明细标签页"""
        payment_frame = ttk.Frame(self.report_notebook)
        self.report_notebook.add(payment_frame, text="收款明细")
        
        # 收款明细列表
        payment_columns = ("date", "contract_id", "customer_name", "amount", "payment_type")
        self.payment_detail_tree = ttk.Treeview(payment_frame, columns=payment_columns, show="headings")
        
        # 设置列标题和宽度
        self.payment_detail_tree.heading("date", text="日期")
        self.payment_detail_tree.heading("contract_id", text="合同ID")
        self.payment_detail_tree.heading("customer_name", text="客户姓名")
        self.payment_detail_tree.heading("amount", text="金额(元)")
        self.payment_detail_tree.heading("payment_type", text="付款类型")
        
        self.payment_detail_tree.column("date", width=100)
        self.payment_detail_tree.column("contract_id", width=100)
        self.payment_detail_tree.column("customer_name", width=120)
        self.payment_detail_tree.column("amount", width=100, anchor=tk.E)
        self.payment_detail_tree.column("payment_type", width=100)
        
        # 滚动条
        payment_detail_scrollbar = ttk.Scrollbar(payment_frame, orient="vertical", command=self.payment_detail_tree.yview)
        payment_detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.payment_detail_tree.configure(yscrollcommand=payment_detail_scrollbar.set)
        self.payment_detail_tree.pack(fill=tk.BOTH, expand=True)
    
    def _create_deposit_detail_tab(self):
        """创建押金明细标签页"""
        deposit_frame = ttk.Frame(self.report_notebook)
        self.report_notebook.add(deposit_frame, text="押金明细")
        
        # 押金明细列表
        deposit_columns = ("date", "contract_id", "customer_name", "record_type", "amount", "remark")
        self.deposit_detail_tree = ttk.Treeview(deposit_frame, columns=deposit_columns, show="headings")
        
        # 设置列标题和宽度
        self.deposit_detail_tree.heading("date", text="日期")
        self.deposit_detail_tree.heading("contract_id", text="合同ID")
        self.deposit_detail_tree.heading("customer_name", text="客户姓名")
        self.deposit_detail_tree.heading("record_type", text="类型")
        self.deposit_detail_tree.heading("amount", text="金额(元)")
        self.deposit_detail_tree.heading("remark", text="备注")
        
        self.deposit_detail_tree.column("date", width=100)
        self.deposit_detail_tree.column("contract_id", width=100)
        self.deposit_detail_tree.column("customer_name", width=120)
        self.deposit_detail_tree.column("record_type", width=60)
        self.deposit_detail_tree.column("amount", width=100, anchor=tk.E)
        self.deposit_detail_tree.column("remark", width=150)
        
        # 滚动条
        deposit_detail_scrollbar = ttk.Scrollbar(deposit_frame, orient="vertical", command=self.deposit_detail_tree.yview)
        deposit_detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.deposit_detail_tree.configure(yscrollcommand=deposit_detail_scrollbar.set)
        self.deposit_detail_tree.pack(fill=tk.BOTH, expand=True)
    
    def _create_invoice_detail_tab(self):
        """创建开票明细标签页"""
        invoice_frame = ttk.Frame(self.report_notebook)
        self.report_notebook.add(invoice_frame, text="开票明细")
        
        # 开票明细列表
        invoice_columns = ("date", "contract_id", "customer_name", "invoice_number", "amount", "tax_amount")
        self.invoice_detail_tree = ttk.Treeview(invoice_frame, columns=invoice_columns, show="headings")
        
        # 设置列标题和宽度
        self.invoice_detail_tree.heading("date", text="日期")
        self.invoice_detail_tree.heading("contract_id", text="合同ID")
        self.invoice_detail_tree.heading("customer_name", text="客户姓名")
        self.invoice_detail_tree.heading("invoice_number", text="发票号")
        self.invoice_detail_tree.heading("amount", text="开票金额(元)")
        self.invoice_detail_tree.heading("tax_amount", text="税额(元)")
        
        self.invoice_detail_tree.column("date", width=100)
        self.invoice_detail_tree.column("contract_id", width=100)
        self.invoice_detail_tree.column("customer_name", width=120)
        self.invoice_detail_tree.column("invoice_number", width=120)
        self.invoice_detail_tree.column("amount", width=100, anchor=tk.E)
        self.invoice_detail_tree.column("tax_amount", width=80, anchor=tk.E)
        
        # 滚动条
        invoice_detail_scrollbar = ttk.Scrollbar(invoice_frame, orient="vertical", command=self.invoice_detail_tree.yview)
        invoice_detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.invoice_detail_tree.configure(yscrollcommand=invoice_detail_scrollbar.set)
        self.invoice_detail_tree.pack(fill=tk.BOTH, expand=True)
    
    def _create_contract_stats_tab(self):
        """创建合同统计标签页"""
        stats_frame = ttk.Frame(self.report_notebook)
        self.report_notebook.add(stats_frame, text="合同统计")
        
        # 合同统计列表
        contract_columns = ("contract_id", "customer_name", "room_number", "total_rent", "status", "effective_date")
        self.contract_stats_tree = ttk.Treeview(stats_frame, columns=contract_columns, show="headings")
        
        # 设置列标题和宽度
        self.contract_stats_tree.heading("contract_id", text="合同ID")
        self.contract_stats_tree.heading("customer_name", text="客户姓名")
        self.contract_stats_tree.heading("room_number", text="房间号")
        self.contract_stats_tree.heading("total_rent", text="合同总租金(元)")
        self.contract_stats_tree.heading("status", text="状态")
        self.contract_stats_tree.heading("effective_date", text="生效日期")
        
        self.contract_stats_tree.column("contract_id", width=100)
        self.contract_stats_tree.column("customer_name", width=120)
        self.contract_stats_tree.column("room_number", width=80)
        self.contract_stats_tree.column("total_rent", width=120, anchor=tk.E)
        self.contract_stats_tree.column("status", width=80)
        self.contract_stats_tree.column("effective_date", width=100)
        
        # 滚动条
        contract_stats_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=self.contract_stats_tree.yview)
        contract_stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.contract_stats_tree.configure(yscrollcommand=contract_stats_scrollbar.set)
        self.contract_stats_tree.pack(fill=tk.BOTH, expand=True)
    
    def _load_current_month(self):
        """加载当前月份"""
        today = datetime.date.today()
        self.year_var.set(str(today.year))
        self.month_var.set(f"{today.month:02d}")
        self._generate_report()
    
    def _generate_report(self):
        """生成报告"""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            
            # 更新报告标题
            self.report_title_var.set(f"{year}年{month:02d}月度报告")
            
            # 获取月度汇总数据
            monthly_summary = self.payment_service.get_monthly_summary(year, month)
            
            # 获取合同数据
            contracts = self.contract_service.get_all_contracts()
            
            # 获取收款记录
            payment_records = self.payment_service.get_payment_records()
            
            # 获取押金记录
            deposit_records = self.payment_service.get_deposit_records()
            
            # 获取开票记录
            invoice_records = self.payment_service.get_invoice_records()
            
            # 过滤指定月份的数据
            start_date = datetime.date(year, month, 1)
            if month == 12:
                end_date = datetime.date(year, 12, 31)
            else:
                next_month = datetime.date(year, month + 1, 1)
                end_date = next_month - datetime.timedelta(days=1)
            
            # 过滤收款记录
            filtered_payments = [
                p for p in payment_records
                if start_date <= p.date <= end_date
            ]
            
            # 过滤押金记录
            filtered_deposits = [
                d for d in deposit_records
                if start_date <= d.date <= end_date
            ]
            
            # 过滤开票记录
            filtered_invoices = [
                i for i in invoice_records
                if start_date <= i.date <= end_date
            ]
            
            # 更新统计信息
            self._update_statistics(contracts, monthly_summary)
            
            # 更新明细列表
            self._update_payment_details(filtered_payments, contracts)
            self._update_deposit_details(filtered_deposits, contracts)
            self._update_invoice_details(filtered_invoices, contracts)
            self._update_contract_stats(contracts)
            
            logger.info(f"已生成{year}年{month:02d}月的月度报告")
            
        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            messagebox.showerror("错误", f"生成报告失败: {str(e)}")
    
    def _update_statistics(self, contracts: List, monthly_summary: Dict[str, Any]):
        """更新统计信息"""
        # 合同统计
        total_contracts = len(contracts)
        effective_contracts = len([c for c in contracts if c.is_effective])
        
        # 收款统计
        total_rent_income = sum(monthly_summary.get('payments', {}).values())
        
        # 押金统计  
        deposit_received = monthly_summary.get('deposits', {}).get('收取', 0) or 0
        deposit_returned = monthly_summary.get('deposits', {}).get('退还', 0) or 0
        deposit_balance = deposit_received - deposit_returned
        
        # 开票统计
        invoice_total = monthly_summary.get('invoices', {}).get('total_amount', 0) or 0
        
        # 更新显示
        self.total_contracts_var.set(str(total_contracts))
        self.effective_contracts_var.set(str(effective_contracts))
        self.total_rent_var.set(f"{total_rent_income:.2f}元")
        self.deposit_balance_var.set(f"{deposit_balance:.2f}元")
        self.invoice_total_var.set(f"{invoice_total:.2f}元")
    
    def _update_payment_details(self, payments: List, contracts: List):
        """更新收款明细"""
        # 清空现有数据
        for item in self.payment_detail_tree.get_children():
            self.payment_detail_tree.delete(item)
        
        # 创建合同ID到客户姓名的映射
        contract_map = {c.contract_id: c.customer_name for c in contracts}
        
        # 添加收款明细数据
        for payment in payments:
            customer_name = contract_map.get(payment.contract_id, "未知客户")
            self.payment_detail_tree.insert("", tk.END, values=(
                payment.date.strftime("%Y-%m-%d"),
                payment.contract_id,
                customer_name,
                f"{payment.amount:.2f}",
                payment.payment_type
            ))
    
    def _update_deposit_details(self, deposits: List, contracts: List):
        """更新押金明细"""
        # 清空现有数据
        for item in self.deposit_detail_tree.get_children():
            self.deposit_detail_tree.delete(item)
        
        # 创建合同ID到客户姓名的映射
        contract_map = {c.contract_id: c.customer_name for c in contracts}
        
        # 添加押金明细数据
        for deposit in deposits:
            customer_name = contract_map.get(deposit.contract_id, "未知客户")
            self.deposit_detail_tree.insert("", tk.END, values=(
                deposit.date.strftime("%Y-%m-%d"),
                deposit.contract_id,
                customer_name,
                deposit.record_type,
                f"{deposit.amount:.2f}",
                deposit.remark or ""
            ))
    
    def _update_invoice_details(self, invoices: List, contracts: List):
        """更新开票明细"""
        # 清空现有数据
        for item in self.invoice_detail_tree.get_children():
            self.invoice_detail_tree.delete(item)
        
        # 创建合同ID到客户姓名的映射
        contract_map = {c.contract_id: c.customer_name for c in contracts}
        
        # 添加开票明细数据
        for invoice in invoices:
            customer_name = contract_map.get(invoice.contract_id, "未知客户")
            self.invoice_detail_tree.insert("", tk.END, values=(
                invoice.date.strftime("%Y-%m-%d"),
                invoice.contract_id,
                customer_name,
                invoice.invoice_number,
                f"{invoice.amount:.2f}",
                f"{invoice.tax_amount:.2f}"
            ))
    
    def _update_contract_stats(self, contracts: List):
        """更新合同统计"""
        # 清空现有数据
        for item in self.contract_stats_tree.get_children():
            self.contract_stats_tree.delete(item)
        
        # 添加合同统计数据
        for contract in contracts:
            status = "已生效" if contract.is_effective else "未生效"
            effective_date = contract.effective_date.strftime("%Y-%m-%d") if contract.effective_date else ""
            
            self.contract_stats_tree.insert("", tk.END, values=(
                contract.contract_id,
                contract.customer_name,
                contract.room_number,
                f"{contract.total_rent:.2f}",
                status,
                effective_date
            ))
    
    def _export_excel(self):
        """导出为Excel"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )
            
            if file_path:
                # TODO: 实现Excel导出功能
                # 需要安装openpyxl库
                messagebox.showinfo("提示", "Excel导出功能待实现\n需要安装openpyxl库")
                logger.info(f"用户尝试导出Excel到: {file_path}")
                
        except Exception as e:
            logger.error(f"导出Excel失败: {str(e)}")
            messagebox.showerror("错误", f"导出Excel失败: {str(e)}")
    
    def _export_pdf(self):
        """导出为PDF"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存PDF文件",
                defaultextension=".pdf",
                filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
            )
            
            if file_path:
                # TODO: 实现PDF导出功能
                # 需要安装reportlab库
                messagebox.showinfo("提示", "PDF导出功能待实现\n需要安装reportlab库")
                logger.info(f"用户尝试导出PDF到: {file_path}")
                
        except Exception as e:
            logger.error(f"导出PDF失败: {str(e)}")
            messagebox.showerror("错误", f"导出PDF失败: {str(e)}")
    
    def refresh(self):
        """刷新报告数据"""
        self._generate_report()
