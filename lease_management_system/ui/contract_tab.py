"""
合同管理标签页UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from typing import List, Optional

from models.entities import User, LeaseContract, RentPeriod, FreeRentPeriod, ContractType
from services.contract_service import ContractService
from ui.dialogs.contract_dialog import ContractDialog
from ui.dialogs.rent_period_dialog import RentPeriodDialog
from ui.dialogs.free_period_dialog import FreePeriodDialog
from utils.logging import get_logger

logger = get_logger("ContractTab")


class ContractTab(ttk.Frame):
    """合同管理标签页"""
    
    def __init__(self, parent, contract_service: ContractService, current_user: User):
        super().__init__(parent)
        
        self.contract_service = contract_service
        self.current_user = current_user
        self.contracts: List[LeaseContract] = []
        self.selected_contract: Optional[LeaseContract] = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建左右分割的框架
        self._create_left_panel()
        self._create_right_panel()
    
    def _create_left_panel(self):
        """创建左侧面板（合同列表）"""
        # 左侧框架
        left_frame = ttk.Frame(self, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5), pady=5)
        left_frame.pack_propagate(False)
        
        # 标题
        ttk.Label(left_frame, text="合同列表", font=("SimHei", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # 搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        search_button = ttk.Button(search_frame, text="搜索", command=self._search_contracts)
        search_button.pack(side=tk.RIGHT)
        
        # 绑定搜索事件
        search_entry.bind('<KeyRelease>', lambda e: self._search_contracts())
        
        # 合同列表
        columns = ("contract_id", "customer_name", "room_number", "status", "create_time")
        self.contract_tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        
        # 设置列标题和宽度
        self.contract_tree.heading("contract_id", text="合同ID")
        self.contract_tree.heading("customer_name", text="客户姓名")
        self.contract_tree.heading("room_number", text="房间号")
        self.contract_tree.heading("status", text="状态")
        self.contract_tree.heading("create_time", text="创建时间")
        
        self.contract_tree.column("contract_id", width=80)
        self.contract_tree.column("customer_name", width=80)
        self.contract_tree.column("room_number", width=60)
        self.contract_tree.column("status", width=60)
        self.contract_tree.column("create_time", width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.contract_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.contract_tree.configure(yscrollcommand=scrollbar.set)
        self.contract_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 绑定选择事件
        self.contract_tree.bind('<<TreeviewSelect>>', self._on_contract_select)
        self.contract_tree.bind('<Double-1>', self._on_contract_double_click)
        
        # 按钮框架
        if self.current_user.can_edit():
            button_frame = ttk.Frame(left_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            ttk.Button(button_frame, text="新增合同", command=self._add_contract).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="编辑合同", command=self._edit_contract).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="删除合同", command=self._delete_contract).pack(side=tk.LEFT, padx=(0, 5))
            
            # 第二行按钮
            button_frame2 = ttk.Frame(left_frame)
            button_frame2.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Button(button_frame2, text="标记生效", command=self._mark_effective).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame2, text="批量生效", command=self._batch_mark_effective).pack(side=tk.LEFT)
    
    def _create_right_panel(self):
        """创建右侧面板（合同详情）"""
        # 右侧框架
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        
        # 标题
        ttk.Label(right_frame, text="合同详情", font=("SimHei", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # 创建笔记本组件用于多个标签页
        self.detail_notebook = ttk.Notebook(right_frame)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基本信息标签页
        self._create_basic_info_tab()
        
        # 租金期标签页
        self._create_rent_periods_tab()
        
        # 免租期标签页
        self._create_free_periods_tab()
    
    def _create_basic_info_tab(self):
        """创建基本信息标签页"""
        basic_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(basic_frame, text="基本信息")
        
        # 创建滚动框架
        canvas = tk.Canvas(basic_frame)
        scrollbar = ttk.Scrollbar(basic_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 基本信息表单
        info_frame = ttk.LabelFrame(scrollable_frame, text="合同基本信息", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 使用网格布局
        row = 0
        
        # 合同ID
        ttk.Label(info_frame, text="合同ID:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.contract_id_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.contract_id_var, state="readonly", width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 客户姓名
        ttk.Label(info_frame, text="客户姓名:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.customer_name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.customer_name_var, state="readonly", width=20).grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 房间号
        ttk.Label(info_frame, text="房间号:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.room_number_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.room_number_var, state="readonly", width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 租赁面积
        ttk.Label(info_frame, text="租赁面积(m²):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.area_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.area_var, state="readonly", width=20).grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 对方付款名称
        ttk.Label(info_frame, text="对方付款名称:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.payment_name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.payment_name_var, state="readonly", width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # EAS代码
        ttk.Label(info_frame, text="EAS代码:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.eas_code_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.eas_code_var, state="readonly", width=20).grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 税率
        ttk.Label(info_frame, text="税率(%):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.tax_rate_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.tax_rate_var, state="readonly", width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 需要调整收入
        ttk.Label(info_frame, text="需要调整收入:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.need_adjust_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.need_adjust_var, state="readonly", width=20).grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 合同总租金
        ttk.Label(info_frame, text="合同总租金(元):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.total_rent_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.total_rent_var, state="readonly", width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 合同押金
        ttk.Label(info_frame, text="合同押金(元):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.deposit_amount_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.deposit_amount_var, state="readonly", width=20).grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 初始印花税
        ttk.Label(info_frame, text="初始印花税(元):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.stamp_duty_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.stamp_duty_var, state="readonly", width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 合同状态
        ttk.Label(info_frame, text="合同状态:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.contract_status_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.contract_status_var, state="readonly", width=20).grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 创建时间
        ttk.Label(info_frame, text="创建时间:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.create_time_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.create_time_var, state="readonly", width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 创建人
        ttk.Label(info_frame, text="创建人:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.created_by_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.created_by_var, state="readonly", width=20).grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_rent_periods_tab(self):
        """创建租金期标签页"""
        rent_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(rent_frame, text="租金期")
        
        # 标题和按钮
        header_frame = ttk.Frame(rent_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="租金期列表", font=("SimHei", 10, "bold")).pack(side=tk.LEFT)
        
        if self.current_user.can_edit():
            ttk.Button(header_frame, text="添加租金期", command=self._add_rent_period).pack(side=tk.RIGHT)
        
        # 租金期列表
        rent_columns = ("start_date", "end_date", "monthly_rent")
        self.rent_tree = ttk.Treeview(rent_frame, columns=rent_columns, show="headings")
        
        self.rent_tree.heading("start_date", text="开始日期")
        self.rent_tree.heading("end_date", text="结束日期")
        self.rent_tree.heading("monthly_rent", text="月租金(元)")
        
        self.rent_tree.column("start_date", width=120)
        self.rent_tree.column("end_date", width=120)
        self.rent_tree.column("monthly_rent", width=120, anchor=tk.E)
        
        # 滚动条
        rent_scrollbar = ttk.Scrollbar(rent_frame, orient="vertical", command=self.rent_tree.yview)
        rent_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rent_tree.configure(yscrollcommand=rent_scrollbar.set)
        self.rent_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def _create_free_periods_tab(self):
        """创建免租期标签页"""
        free_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(free_frame, text="免租期")
        
        # 标题和按钮
        header_frame = ttk.Frame(free_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="免租期列表", font=("SimHei", 10, "bold")).pack(side=tk.LEFT)
        
        if self.current_user.can_edit():
            ttk.Button(header_frame, text="添加免租期", command=self._add_free_period).pack(side=tk.RIGHT)
        
        # 免租期列表
        free_columns = ("start_date", "end_date")
        self.free_tree = ttk.Treeview(free_frame, columns=free_columns, show="headings")
        
        self.free_tree.heading("start_date", text="开始日期")
        self.free_tree.heading("end_date", text="结束日期")
        
        self.free_tree.column("start_date", width=150)
        self.free_tree.column("end_date", width=150)
        
        # 滚动条
        free_scrollbar = ttk.Scrollbar(free_frame, orient="vertical", command=self.free_tree.yview)
        free_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.free_tree.configure(yscrollcommand=free_scrollbar.set)
        self.free_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def _search_contracts(self):
        """搜索合同"""
        search_term = self.search_var.get().strip().lower()
        self._populate_contract_list(search_term)
    
    def _populate_contract_list(self, search_term: str = ""):
        """填充合同列表"""
        # 清空现有数据
        for item in self.contract_tree.get_children():
            self.contract_tree.delete(item)
        
        # 添加合同数据
        for contract in self.contracts:
            # 搜索过滤
            if search_term and search_term not in contract.contract_id.lower() and \
               search_term not in contract.customer_name.lower() and \
               search_term not in contract.room_number.lower():
                continue
            
            # 确定状态
            status = "已生效" if contract.is_effective else "未生效"
            
            self.contract_tree.insert("", tk.END, values=(
                contract.contract_id,
                contract.customer_name,
                contract.room_number,
                status,
                contract.create_time.strftime("%Y-%m-%d")
            ))
    
    def _on_contract_select(self, event):
        """合同选择事件"""
        selection = self.contract_tree.selection()
        if not selection:
            self.selected_contract = None
            self._clear_contract_details()
            return
        
        # 获取选中的合同ID
        item = selection[0]
        contract_id = self.contract_tree.item(item, "values")[0]
        
        # 查找合同对象
        self.selected_contract = next((c for c in self.contracts if c.contract_id == contract_id), None)
        
        if self.selected_contract:
            self._show_contract_details(self.selected_contract)
    
    def _on_contract_double_click(self, event):
        """合同双击事件"""
        if self.selected_contract and self.current_user.can_edit():
            self._edit_contract()
    
    def _show_contract_details(self, contract: LeaseContract):
        """显示合同详情"""
        # 更新基本信息
        self.contract_id_var.set(contract.contract_id)
        self.customer_name_var.set(contract.customer_name)
        self.room_number_var.set(contract.room_number)
        self.area_var.set(f"{contract.area:.2f}")
        self.payment_name_var.set(contract.payment_name)
        self.eas_code_var.set(contract.eas_code)
        self.tax_rate_var.set(f"{contract.tax_rate*100:.2f}%")
        self.need_adjust_var.set("是" if contract.need_adjust_income else "否")
        self.total_rent_var.set(f"{contract.total_rent:.2f}")
        self.deposit_amount_var.set(f"{contract.deposit_amount:.2f}")
        self.stamp_duty_var.set(f"{contract.initial_stamp_duty:.2f}")
        
        # 合同状态
        if contract.is_effective:
            status_text = f"已生效（生效日期：{contract.effective_date.strftime('%Y-%m-%d')}）"
        else:
            status_text = "未生效"
        self.contract_status_var.set(status_text)
        
        self.create_time_var.set(contract.create_time.strftime("%Y-%m-%d %H:%M"))
        self.created_by_var.set(contract.created_by)
        
        # 更新租金期列表
        for item in self.rent_tree.get_children():
            self.rent_tree.delete(item)
        
        for rent_period in contract.rent_periods:
            self.rent_tree.insert("", tk.END, values=(
                rent_period.start_date.strftime("%Y-%m-%d"),
                rent_period.end_date.strftime("%Y-%m-%d"),
                f"{rent_period.monthly_rent:.2f}"
            ))
        
        # 更新免租期列表
        for item in self.free_tree.get_children():
            self.free_tree.delete(item)
        
        for free_period in contract.free_rent_periods:
            self.free_tree.insert("", tk.END, values=(
                free_period.start_date.strftime("%Y-%m-%d"),
                free_period.end_date.strftime("%Y-%m-%d")
            ))
    
    def _clear_contract_details(self):
        """清空合同详情"""
        vars_to_clear = [
            self.contract_id_var, self.customer_name_var, self.room_number_var,
            self.area_var, self.payment_name_var, self.eas_code_var,
            self.tax_rate_var, self.need_adjust_var, self.total_rent_var,
            self.deposit_amount_var, self.stamp_duty_var, self.contract_status_var,
            self.create_time_var, self.created_by_var
        ]
        
        for var in vars_to_clear:
            var.set("")
        
        # 清空列表
        for item in self.rent_tree.get_children():
            self.rent_tree.delete(item)
        
        for item in self.free_tree.get_children():
            self.free_tree.delete(item)
    
    def _add_contract(self):
        """添加新合同"""
        dialog = ContractDialog(self, None, self.current_user)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                self.contract_service.create_contract(dialog.result, self.current_user.username)
                messagebox.showinfo("成功", "合同创建成功")
                self.refresh()
            except Exception as e:
                messagebox.showerror("错误", f"创建合同失败: {str(e)}")
    
    def _edit_contract(self):
        """编辑选中的合同"""
        if not self.selected_contract:
            messagebox.showwarning("提示", "请先选择一个合同")
            return
        
        dialog = ContractDialog(self, self.selected_contract, self.current_user)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                self.contract_service.update_contract(
                    self.selected_contract.contract_id,
                    dialog.result,
                    self.current_user.username
                )
                messagebox.showinfo("成功", "合同更新成功")
                self.refresh()
            except Exception as e:
                messagebox.showerror("错误", f"更新合同失败: {str(e)}")
    
    def _delete_contract(self):
        """删除选中的合同"""
        if not self.selected_contract:
            messagebox.showwarning("提示", "请先选择一个合同")
            return
        
        if messagebox.askyesno("确认", f"确定要删除合同 {self.selected_contract.contract_id} 吗？\n此操作将删除所有关联数据且不可恢复！"):
            try:
                self.contract_service.delete_contract(self.selected_contract.contract_id, self.current_user.username)
                messagebox.showinfo("成功", "合同删除成功")
                self.refresh()
            except Exception as e:
                messagebox.showerror("错误", f"删除合同失败: {str(e)}")
    
    def _mark_effective(self):
        """标记合同生效"""
        if not self.selected_contract:
            messagebox.showwarning("提示", "请先选择一个合同")
            return
        
        if self.selected_contract.is_effective:
            messagebox.showinfo("提示", "合同已生效，无需重复操作")
            return
        
        # 简单的日期输入对话框
        effective_date = datetime.date.today()
        
        try:
            self.contract_service.mark_contract_effective(
                self.selected_contract.contract_id,
                effective_date,
                self.current_user.username
            )
            messagebox.showinfo("成功", f"合同已标记为生效\n生效日期：{effective_date.strftime('%Y-%m-%d')}")
            self.refresh()
        except Exception as e:
            messagebox.showerror("错误", f"标记生效失败: {str(e)}")
    
    def _batch_mark_effective(self):
        """批量标记合同生效"""
        # TODO: 实现批量标记生效功能
        messagebox.showinfo("提示", "批量标记生效功能待实现")
    
    def _add_rent_period(self):
        """添加租金期"""
        if not self.selected_contract:
            messagebox.showwarning("提示", "请先选择一个合同")
            return
        
        dialog = RentPeriodDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                start_date, end_date, monthly_rent = dialog.result
                rent_period = RentPeriod(start_date, end_date, monthly_rent)
                
                self.contract_service.add_rent_period(
                    self.selected_contract.contract_id,
                    rent_period,
                    self.current_user.username
                )
                messagebox.showinfo("成功", "租金期添加成功")
                self.refresh()
            except Exception as e:
                messagebox.showerror("错误", f"添加租金期失败: {str(e)}")
    
    def _add_free_period(self):
        """添加免租期"""
        if not self.selected_contract:
            messagebox.showwarning("提示", "请先选择一个合同")
            return
        
        dialog = FreePeriodDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                start_date, end_date = dialog.result
                free_period = FreeRentPeriod(start_date, end_date)
                
                self.contract_service.add_free_rent_period(
                    self.selected_contract.contract_id,
                    free_period,
                    self.current_user.username
                )
                messagebox.showinfo("成功", "免租期添加成功")
                self.refresh()
            except Exception as e:
                messagebox.showerror("错误", f"添加免租期失败: {str(e)}")
    
    def refresh(self):
        """刷新数据"""
        try:
            self.contracts = self.contract_service.get_all_contracts()
            self._populate_contract_list()
            self._clear_contract_details()
            self.selected_contract = None
        except Exception as e:
            logger.error(f"刷新合同数据失败: {str(e)}")
            messagebox.showerror("错误", f"刷新数据失败: {str(e)}")