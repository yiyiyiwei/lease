"""
印花税查询标签页UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

from models.entities import User, LeaseContract
from services.contract_service import ContractService
from config.settings import config
from utils.logging import get_logger

logger = get_logger("StampTab")


class StampTab(ttk.Frame):
    """印花税查询标签页"""
    
    def __init__(self, parent, contract_service: ContractService, current_user: User):
        super().__init__(parent)
        
        self.contract_service = contract_service
        self.current_user = current_user
        self.contracts: List[LeaseContract] = []
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建上下分割的框架
        self._create_top_panel()
        self._create_bottom_panel()
    
    def _create_top_panel(self):
        """创建上部面板（查询条件和统计）"""
        # 上部框架
        top_frame = ttk.Frame(self, height=200)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 标题
        ttk.Label(top_frame, text="印花税查询与统计", font=("SimHei", 14, "bold")).pack(pady=(0, 15))
        
        # 创建左右分割
        content_frame = ttk.Frame(top_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：查询条件
        query_frame = ttk.LabelFrame(content_frame, text="查询条件", padding="15")
        query_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 合同ID查询
        ttk.Label(query_frame, text="合同ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.contract_id_var = tk.StringVar()
        contract_entry = ttk.Entry(query_frame, textvariable=self.contract_id_var, width=15)
        contract_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # 客户姓名查询
        ttk.Label(query_frame, text="客户姓名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.customer_name_var = tk.StringVar()
        customer_entry = ttk.Entry(query_frame, textvariable=self.customer_name_var, width=15)
        customer_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # 查询按钮
        query_button = ttk.Button(query_frame, text="查询", command=self._search_contracts)
        query_button.grid(row=2, column=0, columnspan=2, pady=(15, 0), sticky=tk.EW)
        
        # 重置按钮
        reset_button = ttk.Button(query_frame, text="重置", command=self._reset_search)
        reset_button.grid(row=3, column=0, columnspan=2, pady=(5, 0), sticky=tk.EW)
        
        # 右侧：印花税统计
        stats_frame = ttk.LabelFrame(content_frame, text="印花税统计", padding="15")
        stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 创建统计网格
        # 印花税率
        ttk.Label(stats_frame, text="印花税率:", font=("SimHei", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.stamp_rate_var = tk.StringVar()
        self.stamp_rate_var.set(f"{config.business.stamp_duty_rate * 100:.1f}‰")
        ttk.Label(stats_frame, textvariable=self.stamp_rate_var, foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 合同总数
        ttk.Label(stats_frame, text="合同总数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.total_contracts_var = tk.StringVar()
        ttk.Label(stats_frame, textvariable=self.total_contracts_var, foreground="green").grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 租金总额
        ttk.Label(stats_frame, text="租金总额:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.total_rent_var = tk.StringVar()
        ttk.Label(stats_frame, textvariable=self.total_rent_var, foreground="orange").grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 印花税总额
        ttk.Label(stats_frame, text="印花税总额:", font=("SimHei", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.total_stamp_duty_var = tk.StringVar()
        ttk.Label(stats_frame, textvariable=self.total_stamp_duty_var, foreground="red", font=("SimHei", 10, "bold")).grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 平均印花税
        ttk.Label(stats_frame, text="平均印花税:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        self.avg_stamp_duty_var = tk.StringVar()
        ttk.Label(stats_frame, textvariable=self.avg_stamp_duty_var, foreground="purple").grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 最高印花税
        ttk.Label(stats_frame, text="最高印花税:").grid(row=2, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        self.max_stamp_duty_var = tk.StringVar()
        ttk.Label(stats_frame, textvariable=self.max_stamp_duty_var, foreground="darkred").grid(row=2, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 最低印花税
        ttk.Label(stats_frame, text="最低印花税:").grid(row=3, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        self.min_stamp_duty_var = tk.StringVar()
        ttk.Label(stats_frame, textvariable=self.min_stamp_duty_var, foreground="darkgreen").grid(row=3, column=3, sticky=tk.W, padx=(10, 0), pady=5)
    
    def _create_bottom_panel(self):
        """创建下部面板（合同印花税明细）"""
        # 下部框架
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # 标题和操作按钮
        header_frame = ttk.Frame(bottom_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="合同印花税明细", font=("SimHei", 12, "bold")).pack(side=tk.LEFT)
        
        # 导出按钮
        export_frame = ttk.Frame(header_frame)
        export_frame.pack(side=tk.RIGHT)
        
        ttk.Button(export_frame, text="导出明细", command=self._export_details).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="刷新", command=self.refresh).pack(side=tk.LEFT)
        
        # 合同印花税明细列表
        columns = ("contract_id", "customer_name", "room_number", "total_rent", "stamp_duty", "status", "effective_date")
        self.stamp_tree = ttk.Treeview(bottom_frame, columns=columns, show="headings", selectmode="browse")
        
        # 设置列标题和宽度
        self.stamp_tree.heading("contract_id", text="合同ID")
        self.stamp_tree.heading("customer_name", text="客户姓名")
        self.stamp_tree.heading("room_number", text="房间号")
        self.stamp_tree.heading("total_rent", text="合同总租金(元)")
        self.stamp_tree.heading("stamp_duty", text="印花税(元)")
        self.stamp_tree.heading("status", text="合同状态")
        self.stamp_tree.heading("effective_date", text="生效日期")
        
        self.stamp_tree.column("contract_id", width=100)
        self.stamp_tree.column("customer_name", width=120)
        self.stamp_tree.column("room_number", width=80)
        self.stamp_tree.column("total_rent", width=120, anchor=tk.E)
        self.stamp_tree.column("stamp_duty", width=100, anchor=tk.E)
        self.stamp_tree.column("status", width=80)
        self.stamp_tree.column("effective_date", width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=self.stamp_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stamp_tree.configure(yscrollcommand=scrollbar.set)
        self.stamp_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 绑定双击事件
        self.stamp_tree.bind('<Double-1>', self._on_double_click)
    
    def _search_contracts(self):
        """搜索合同"""
        contract_id = self.contract_id_var.get().strip().lower()
        customer_name = self.customer_name_var.get().strip().lower()
        
        self._populate_contract_list(contract_id, customer_name)
        self._update_statistics()
    
    def _reset_search(self):
        """重置搜索条件"""
        self.contract_id_var.set("")
        self.customer_name_var.set("")
        self._populate_contract_list()
        self._update_statistics()
    
    def _populate_contract_list(self, search_contract_id: str = "", search_customer_name: str = ""):
        """填充合同列表"""
        # 清空现有数据
        for item in self.stamp_tree.get_children():
            self.stamp_tree.delete(item)
        
        # 添加合同数据
        for contract in self.contracts:
            # 搜索过滤
            if search_contract_id and search_contract_id not in contract.contract_id.lower():
                continue
            if search_customer_name and search_customer_name not in contract.customer_name.lower():
                continue
            
            # 计算印花税
            stamp_duty = contract.initial_total_rent * config.business.stamp_duty_rate
            
            # 确定状态
            status = "已生效" if contract.is_effective else "未生效"
            
            # 生效日期
            effective_date = contract.effective_date.strftime("%Y-%m-%d") if contract.effective_date else ""
            
            self.stamp_tree.insert("", tk.END, values=(
                contract.contract_id,
                contract.customer_name,
                contract.room_number,
                f"{contract.total_rent:.2f}",
                f"{stamp_duty:.2f}",
                status,
                effective_date
            ))
    
    def _update_statistics(self):
        """更新统计信息"""
        try:
            # 获取当前显示的合同（经过搜索过滤的）
            displayed_contracts = []
            for item in self.stamp_tree.get_children():
                values = self.stamp_tree.item(item, "values")
                contract_id = values[0]
                contract = next((c for c in self.contracts if c.contract_id == contract_id), None)
                if contract:
                    displayed_contracts.append(contract)
            
            if not displayed_contracts:
                # 如果没有显示的合同，清空统计
                self.total_contracts_var.set("0")
                self.total_rent_var.set("0.00元")
                self.total_stamp_duty_var.set("0.00元")
                self.avg_stamp_duty_var.set("0.00元")
                self.max_stamp_duty_var.set("0.00元")
                self.min_stamp_duty_var.set("0.00元")
                return
            
            # 计算统计数据
            total_contracts = len(displayed_contracts)
            total_rent = sum(c.total_rent for c in displayed_contracts)
            stamp_duties = [c.initial_total_rent * config.business.stamp_duty_rate for c in displayed_contracts]
            total_stamp_duty = sum(stamp_duties)
            avg_stamp_duty = total_stamp_duty / total_contracts if total_contracts > 0 else 0
            max_stamp_duty = max(stamp_duties) if stamp_duties else 0
            min_stamp_duty = min(stamp_duties) if stamp_duties else 0
            
            # 更新显示
            self.total_contracts_var.set(str(total_contracts))
            self.total_rent_var.set(f"{total_rent:.2f}元")
            self.total_stamp_duty_var.set(f"{total_stamp_duty:.2f}元")
            self.avg_stamp_duty_var.set(f"{avg_stamp_duty:.2f}元")
            self.max_stamp_duty_var.set(f"{max_stamp_duty:.2f}元")
            self.min_stamp_duty_var.set(f"{min_stamp_duty:.2f}元")
            
        except Exception as e:
            logger.error(f"更新印花税统计失败: {str(e)}")
    
    def _on_double_click(self, event):
        """双击事件处理"""
        selection = self.stamp_tree.selection()
        if not selection:
            return
        
        # 获取选中的合同ID
        item = selection[0]
        contract_id = self.stamp_tree.item(item, "values")[0]
        
        # 查找合同对象
        contract = next((c for c in self.contracts if c.contract_id == contract_id), None)
        if contract:
            self._show_contract_detail(contract)
    
    def _show_contract_detail(self, contract: LeaseContract):
        """显示合同详细信息"""
        # 计算印花税详细信息
        stamp_duty = contract.initial_total_rent * config.business.stamp_duty_rate
        
        detail_text = f"""
合同详细信息

合同ID: {contract.contract_id}
客户姓名: {contract.customer_name}
房间号: {contract.room_number}
租赁面积: {contract.area:.2f} m²

财务信息:
合同总租金: {contract.total_rent:.2f} 元
初始总租金: {contract.initial_total_rent:.2f} 元
印花税税率: {config.business.stamp_duty_rate * 1000:.1f}‰
应缴印花税: {stamp_duty:.2f} 元

合同状态: {'已生效' if contract.is_effective else '未生效'}
生效日期: {contract.effective_date.strftime('%Y-%m-%d') if contract.effective_date else '未设置'}
创建时间: {contract.create_time.strftime('%Y-%m-%d %H:%M')}
创建人: {contract.created_by}
        """
        
        messagebox.showinfo("合同详细信息", detail_text.strip())
    
    def _export_details(self):
        """导出印花税明细"""
        # TODO: 实现导出功能
        messagebox.showinfo("提示", "印花税明细导出功能待实现\n将导出当前显示的所有印花税明细数据")
    
    def refresh(self):
        """刷新数据"""
        try:
            self.contracts = self.contract_service.get_all_contracts()
            self._populate_contract_list()
            self._update_statistics()
        except Exception as e:
            logger.error(f"刷新印花税数据失败: {str(e)}")
            messagebox.showerror("错误", f"刷新数据失败: {str(e)}")
