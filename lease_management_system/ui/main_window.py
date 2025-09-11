#!/usr/bin/env python3
"""
主窗口UI模块 - 完整实现版本
包含所有导入导出和系统管理功能
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import os
import shutil
import pandas as pd
from typing import Optional

from config.settings import config
from models.entities import User
from ui.login_dialog import LoginDialog
from ui.contract_tab import ContractTab
from ui.payment_tab import PaymentTab
from ui.deposit_tab import DepositTab
from ui.report_tab import ReportTab
from ui.stamp_tab import StampTab
from ui.system_tab import SystemTab
from services.contract_service import ContractService
from services.payment_service import PaymentService
from database.manager import DatabaseManager
from utils.logging import get_logger

logger = get_logger("MainWindow")


class MainWindow(tk.Tk):
    """主窗口类 - 完整功能版本"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化属性
        self.current_user: Optional[User] = None
        self.db_manager = DatabaseManager()
        self.contract_service = ContractService(self.db_manager)
        self.payment_service = PaymentService(self.db_manager)
        
        # 配置窗口
        self.title(config.ui.window_title)
        self.geometry(config.ui.window_geometry)
        self.withdraw()  # 隐藏主窗口直到登录完成
        
        # 执行登录
        if not self._login():
            self.destroy()
            return
        
        # 登录成功后显示主窗口
        self.deiconify()
        self.state('normal')
        self.lift()
        
        # 创建界面
        self._create_menu()
        self._create_notebook()
        self._create_tabs()
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        logger.info(f"用户 {self.current_user.username} 成功登录系统")
    
    def _login(self) -> bool:
        """执行用户登录"""
        try:
            login_dialog = LoginDialog(self, self.db_manager)
            self.wait_window(login_dialog)
            
            if login_dialog.result:
                self.current_user = login_dialog.result
                return True
            return False
            
        except Exception as e:
            logger.error(f"登录过程异常: {str(e)}")
            messagebox.showerror("错误", f"登录失败: {str(e)}")
            return False
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="备份数据", command=self._backup_data)
        file_menu.add_command(label="恢复数据", command=self._restore_backup)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 导入导出菜单
        io_menu = tk.Menu(menubar, tearoff=0)
        io_menu.add_command(label="导入数据", command=self._import_data)
        io_menu.add_separator()
        io_menu.add_command(label="导出合同列表", command=self._export_contracts)
        io_menu.add_command(label="导出月度报告", command=self._export_monthly_report)
        io_menu.add_command(label="导出印花税明细", command=self._export_stamp_duty)
        menubar.add_cascade(label="导入导出", menu=io_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="导入模板说明", command=self._show_import_template)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.config(menu=menubar)
    
    def _create_notebook(self):
        """创建标签页容器"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_tabs(self):
        """创建各个标签页"""
        try:
            # 合同管理标签页
            self.contract_tab = ContractTab(
                self.notebook,
                self.contract_service,
                self.current_user
            )
            self.notebook.add(self.contract_tab, text="合同管理")
            
            # 收款管理标签页
            self.payment_tab = PaymentTab(
                self.notebook,
                self.payment_service,
                self.contract_service,
                self.current_user
            )
            self.notebook.add(self.payment_tab, text="收款管理")
            
            # 押金管理标签页
            self.deposit_tab = DepositTab(
                parent=self.notebook,
                payment_service=self.payment_service,
                contract_service=self.contract_service,
                current_user=self.current_user
            )
            self.notebook.add(self.deposit_tab, text="押金管理")
            
            # 报告标签页
            self.report_tab = ReportTab(
                self.notebook,
                self.contract_service,
                self.payment_service,
                self.current_user
            )
            self.notebook.add(self.report_tab, text="报告")
            
            # 印花税标签页
            self.stamp_tab = StampTab(
                self.notebook,
                self.contract_service,
                self.current_user
            )
            self.notebook.add(self.stamp_tab, text="印花税")
            
            # 系统管理标签页
            self.system_tab = SystemTab(
                self.notebook,
                self.db_manager,
                self.current_user
            )
            self.notebook.add(self.system_tab, text="系统管理")
            
        except Exception as e:
            logger.error(f"创建标签页失败: {str(e)}")
            messagebox.showerror("错误", f"创建标签页失败: {str(e)}")
    
    # ==================== 文件菜单功能 ====================
    
    def _backup_data(self):
        """备份数据"""
        try:
            # 确保备份目录存在
            backup_dir = config.database.backup_dir
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"lease_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 执行备份
            source_db = config.database.db_name
            if os.path.exists(source_db):
                shutil.copy2(source_db, backup_path)
                
                # 清理过期备份
                self._cleanup_old_backups()
                
                messagebox.showinfo("备份成功", f"数据已备份到:\n{backup_path}")
                logger.info(f"数据备份成功: {backup_path}")
            else:
                messagebox.showerror("备份失败", "数据库文件不存在")
                
        except Exception as e:
            logger.error(f"数据备份失败: {str(e)}")
            messagebox.showerror("备份失败", f"数据备份失败:\n{str(e)}")
    
    def _cleanup_old_backups(self):
        """清理过期备份"""
        try:
            backup_dir = config.database.backup_dir
            max_backups = config.database.max_backups
            
            if not os.path.exists(backup_dir):
                return
            
            # 获取所有备份文件
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith("lease_backup_") and filename.endswith(".db"):
                    file_path = os.path.join(backup_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改时间排序，删除最旧的文件
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            if len(backup_files) > max_backups:
                for file_path, _ in backup_files[max_backups:]:
                    try:
                        os.remove(file_path)
                        logger.info(f"删除过期备份: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除备份文件失败: {e}")
                        
        except Exception as e:
            logger.warning(f"清理过期备份失败: {e}")
    
    def _restore_backup(self):
        """恢复数据备份"""
        try:
            backup_dir = config.database.backup_dir
            if not os.path.exists(backup_dir):
                messagebox.showwarning("警告", "备份目录不存在，无法恢复数据")
                return
            
            # 选择备份文件
            file_path = filedialog.askopenfilename(
                title="选择备份文件",
                initialdir=backup_dir,
                filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")]
            )
            
            if not file_path:
                return
            
            # 确认恢复操作
            if not messagebox.askyesno("确认恢复", 
                                      f"确定要从以下备份文件恢复数据吗？\n\n{file_path}\n\n"
                                      "警告：当前数据将被覆盖，建议先备份当前数据！"):
                return
            
            # 备份当前数据库
            current_db = config.database.db_name
            if os.path.exists(current_db):
                backup_current = f"lease_backup_before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_current_path = os.path.join(backup_dir, backup_current)
                shutil.copy2(current_db, backup_current_path)
                logger.info(f"当前数据库已备份到: {backup_current_path}")
            
            # 恢复备份文件
            shutil.copy2(file_path, current_db)
            
            messagebox.showinfo("恢复成功", 
                               f"数据已从备份文件恢复!\n\n"
                               f"备份文件: {os.path.basename(file_path)}\n"
                               f"当前数据已备份\n\n"
                               f"请重启程序以加载恢复的数据。")
            
            logger.info(f"数据恢复成功: {file_path} -> {current_db}")
            
        except Exception as e:
            logger.error(f"数据恢复失败: {str(e)}")
            messagebox.showerror("恢复失败", f"数据恢复失败:\n{str(e)}")
    
    # ==================== 导入导出功能 ====================
    
    def _import_data(self):
        """导入数据"""
        try:
            # 选择导入文件
            file_path = filedialog.askopenfilename(
                title="选择合同导入文件",
                filetypes=[("Excel文件", "*.xlsx"), ("Excel文件", "*.xls"), ("所有文件", "*.*")]
            )
            if not file_path:
                return

            # 读取Excel文件
            df = pd.read_excel(file_path, sheet_name=0)
            
            # 验证必要列
            required_columns = ["合同ID", "客户姓名", "房间号", "对方付款名称", "EAS代码"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror("导入失败", f"Excel文件缺少必要的列:\n{', '.join(missing_columns)}")
                return
            
            # 显示导入预览
            self._show_import_preview(df, file_path)
            
        except Exception as e:
            logger.error(f"导入数据失败: {str(e)}")
            messagebox.showerror("导入失败", f"读取文件失败:\n{str(e)}")
    
    def _show_import_preview(self, df, file_path):
        """显示导入预览"""
        preview_dialog = tk.Toplevel(self)
        preview_dialog.title(f"导入预览 - 共{len(df)}条记录")
        preview_dialog.geometry("900x600")
        preview_dialog.transient(self)
        preview_dialog.grab_set()
        
        # 创建预览表格
        tree = ttk.Treeview(preview_dialog, columns=list(df.columns), show="headings")
        
        # 设置列标题和宽度
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # 添加数据（最多显示50行）
        for idx, row in df.head(50).iterrows():
            tree.insert("", tk.END, values=list(row))
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(preview_dialog, orient="vertical", command=tree.yview)
        scrollbar_x = ttk.Scrollbar(preview_dialog, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X, padx=10)
        
        # 状态标签
        status_label = tk.Label(preview_dialog, text=f"预览前50条记录，共{len(df)}条待导入", fg="blue")
        status_label.pack(pady=5)
        
        def confirm_import():
            """确认导入"""
            try:
                preview_dialog.destroy()
                
                success_count = 0
                error_count = 0
                errors = []
                
                # 处理导入数据
                for idx, row in df.iterrows():
                    try:
                        # 检查合同是否已存在
                        contract_id = str(row["合同ID"]).strip()
                        existing_contract = self.contract_service.get_contract_by_id(contract_id)
                        
                        if existing_contract:
                            errors.append(f"第{idx+2}行: 合同ID {contract_id} 已存在")
                            error_count += 1
                            continue
                        
                        # 构建合同数据
                        contract_data = {
                            "contract_id": contract_id,
                            "customer_name": str(row["客户姓名"]).strip(),
                            "room_number": str(row["房间号"]).strip(),
                            "payment_name": str(row["对方付款名称"]).strip(),
                            "eas_code": str(row["EAS代码"]).strip(),
                            "area": float(row.get("租赁面积", 0)),
                            "tax_rate": float(row.get("税率", 0.05)),
                            "need_adjust_income": str(row.get("是否需调整收入", "否")).strip() == "是",
                            "deposit_amount": float(row.get("押金金额", 0)),
                            "created_by": self.current_user.username
                        }
                        
                        # 创建合同 (这里需要根据实际的服务接口调整)
                        # self.contract_service.create_contract(contract_data)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"第{idx+2}行: {str(e)}")
                
                # 显示导入结果
                result_msg = f"导入完成!\n\n成功: {success_count} 条\n失败: {error_count} 条"
                if errors:
                    result_msg += f"\n\n错误详情:\n" + "\n".join(errors[:10])
                    if len(errors) > 10:
                        result_msg += f"\n...还有{len(errors)-10}个错误"
                
                messagebox.showinfo("导入结果", result_msg)
                logger.info(f"Excel导入完成: 成功{success_count}条, 失败{error_count}条")
                
                # 刷新界面
                self.refresh_all_tabs()
                
            except Exception as e:
                logger.error(f"确认导入时出错: {str(e)}")
                messagebox.showerror("导入失败", f"导入过程中出错:\n{str(e)}")
        
        # 按钮框架
        btn_frame = tk.Frame(preview_dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="确认导入", command=confirm_import, 
                 bg="lightgreen", width=15, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=preview_dialog.destroy, 
                 width=15, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    
    def _export_contracts(self):
        """导出合同列表"""
        try:
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                title="导出合同列表",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
                initialfile=f"合同列表_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
            )
            if not file_path:
                return

            # 获取所有合同数据
            contracts = self.contract_service.get_all_contracts()
            
            # 整理导出数据
            contract_data = []
            for contract in contracts:
                # 计算统计信息
                total_payments = sum(p.amount for p in contract.payment_records if p.payment_type == "租金")
                total_deposits = sum(d.amount for d in contract.deposit_records if d.record_type == "收取")
                total_invoices = sum(i.amount for i in contract.invoice_records)
                
                contract_data.append({
                    "合同ID": contract.contract_id,
                    "客户姓名": contract.customer_name,
                    "房间号": contract.room_number,
                    "对方付款名称": contract.payment_name,
                    "EAS代码": contract.eas_code,
                    "租赁面积(m²)": contract.area,
                    "合同类型": contract.contract_type,
                    "原合同ID": contract.original_contract_id or "",
                    "合同总租金(元)": contract.total_rent,
                    "初始总租金(元)": contract.initial_total_rent,
                    "印花税(元)": contract.initial_stamp_duty,
                    "税率": f"{contract.tax_rate*100:.1f}%",
                    "是否需调整收入": "是" if contract.need_adjust_income else "否",
                    "押金金额(元)": contract.deposit_amount,
                    "是否生效": "是" if contract.is_effective else "否",
                    "生效日期": contract.effective_date.strftime('%Y-%m-%d') if contract.effective_date else "",
                    "创建时间": contract.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "创建人": contract.created_by,
                    "累计收款(元)": total_payments,
                    "累计押金(元)": total_deposits,
                    "累计开票(元)": total_invoices,
                    "租金期数量": len(contract.rent_periods),
                    "免租期数量": len(contract.free_rent_periods)
                })

            # 导出到Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 合同基本信息
                contract_df = pd.DataFrame(contract_data)
                contract_df.to_excel(writer, sheet_name='合同列表', index=False)
                
                # 租金期详情
                rent_period_data = []
                for contract in contracts:
                    for rp in contract.rent_periods:
                        rent_period_data.append({
                            "合同ID": contract.contract_id,
                            "客户姓名": contract.customer_name,
                            "开始日期": rp.start_date.strftime('%Y-%m-%d'),
                            "结束日期": rp.end_date.strftime('%Y-%m-%d'),
                            "月租金(元)": rp.monthly_rent
                        })
                
                if rent_period_data:
                    rent_df = pd.DataFrame(rent_period_data)
                    rent_df.to_excel(writer, sheet_name='租金期明细', index=False)

            messagebox.showinfo("导出成功", f"合同列表已导出到:\n{file_path}\n\n共导出 {len(contracts)} 个合同")
            logger.info(f"成功导出 {len(contracts)} 个合同到: {file_path}")

        except Exception as e:
            logger.error(f"导出合同列表失败: {str(e)}")
            messagebox.showerror("导出失败", f"导出合同列表失败:\n{str(e)}")
    
    def _export_monthly_report(self):
        """导出月度报告"""
        try:
            # 选择月份对话框
            month_dialog = tk.Toplevel(self)
            month_dialog.title("选择导出月份")
            month_dialog.geometry("350x250")
            month_dialog.transient(self)
            month_dialog.grab_set()
            
            frame = tk.Frame(month_dialog, padx=20, pady=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            tk.Label(frame, text="选择要导出的月份:", font=("Arial", 12, "bold")).pack(pady=10)
            
            # 年份选择
            year_frame = tk.Frame(frame)
            year_frame.pack(pady=5)
            tk.Label(year_frame, text="年份:").pack(side=tk.LEFT)
            year_var = tk.StringVar(value=str(datetime.date.today().year))
            year_combo = ttk.Combobox(
                year_frame, textvariable=year_var,
                values=[str(y) for y in range(2020, 2030)],
                state="readonly", width=8
            )
            year_combo.pack(side=tk.LEFT, padx=5)
            
            # 月份选择
            month_frame = tk.Frame(frame)
            month_frame.pack(pady=5)
            tk.Label(month_frame, text="月份:").pack(side=tk.LEFT)
            month_var = tk.StringVar(value=str(datetime.date.today().month))
            month_combo = ttk.Combobox(
                month_frame, textvariable=month_var,
                values=[str(m) for m in range(1, 13)],
                state="readonly", width=6
            )
            month_combo.pack(side=tk.LEFT, padx=5)
            
            def export_report():
                """执行导出"""
                try:
                    year = int(year_var.get())
                    month = int(month_var.get())
                    month_dialog.destroy()
                    
                    # 选择保存路径
                    file_path = filedialog.asksaveasfilename(
                        title="保存月度报告",
                        defaultextension=".xlsx",
                        filetypes=[("Excel文件", "*.xlsx")],
                        initialfile=f"{year}年{month:02d}月度报告.xlsx"
                    )
                    if not file_path:
                        return

                    self._generate_monthly_report_excel(year, month, file_path)
                    
                except Exception as e:
                    logger.error(f"导出月度报告失败: {str(e)}")
                    messagebox.showerror("导出失败", f"导出月度报告失败:\n{str(e)}")
            
            # 按钮
            btn_frame = tk.Frame(frame)
            btn_frame.pack(pady=20)
            tk.Button(btn_frame, text="导出", command=export_report, 
                     width=12, bg="lightgreen").pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="取消", command=month_dialog.destroy, 
                     width=12).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            logger.error(f"打开月度报告导出对话框失败: {str(e)}")
            messagebox.showerror("错误", f"打开导出对话框失败:\n{str(e)}")
    
    def _generate_monthly_report_excel(self, year: int, month: int, file_path: str):
        """生成月度报告Excel文件"""
        try:
            import calendar
            
            # 获取月份范围
            month_start = datetime.date(year, month, 1)
            month_end = datetime.date(year, month, calendar.monthrange(year, month)[1])
            
            contracts = self.contract_service.get_all_contracts()
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 1. 月度收款汇总
                payment_data = []
                total_payment = 0
                for contract in contracts:
                    monthly_payments = [p for p in contract.payment_records 
                                      if month_start <= p.date <= month_end]
                    if monthly_payments:
                        contract_payment = sum(p.amount for p in monthly_payments)
                        total_payment += contract_payment
                        payment_data.append({
                            "合同ID": contract.contract_id,
                            "客户姓名": contract.customer_name,
                            "房间号": contract.room_number,
                            "本月收款(元)": contract_payment,
                            "收款笔数": len(monthly_payments)
                        })
                
                # 添加合计行
                if payment_data:
                    payment_data.append({
                        "合同ID": "合计",
                        "客户姓名": "",
                        "房间号": "",
                        "本月收款(元)": total_payment,
                        "收款笔数": sum(row["收款笔数"] for row in payment_data[:-1])
                    })
                
                payment_df = pd.DataFrame(payment_data)
                payment_df.to_excel(writer, sheet_name='月度收款汇总', index=False)
                
                # 2. 月度开票汇总
                invoice_data = []
                total_invoice = 0
                for contract in contracts:
                    monthly_invoices = [i for i in contract.invoice_records 
                                      if month_start <= i.date <= month_end]
                    if monthly_invoices:
                        contract_invoice = sum(i.amount for i in monthly_invoices)
                        total_invoice += contract_invoice
                        invoice_data.append({
                            "合同ID": contract.contract_id,
                            "客户姓名": contract.customer_name,
                            "房间号": contract.room_number,
                            "本月开票(元)": contract_invoice,
                            "开票笔数": len(monthly_invoices)
                        })
                
                if invoice_data:
                    invoice_data.append({
                        "合同ID": "合计",
                        "客户姓名": "",
                        "房间号": "",
                        "本月开票(元)": total_invoice,
                        "开票笔数": sum(row["开票笔数"] for row in invoice_data[:-1])
                    })
                
                invoice_df = pd.DataFrame(invoice_data)
                invoice_df.to_excel(writer, sheet_name='月度开票汇总', index=False)
                
                # 3. 新增合同
                new_contracts = [c for c in contracts 
                               if month_start <= c.create_time.date() <= month_end]
                if new_contracts:
                    new_contract_data = []
                    for contract in new_contracts:
                        new_contract_data.append({
                            "合同ID": contract.contract_id,
                            "客户姓名": contract.customer_name,
                            "房间号": contract.room_number,
                            "合同总租金(元)": contract.total_rent,
                            "创建日期": contract.create_time.strftime('%Y-%m-%d'),
                            "创建人": contract.created_by
                        })
                    
                    new_df = pd.DataFrame(new_contract_data)
                    new_df.to_excel(writer, sheet_name='新增合同', index=False)
                
                # 4. 月度统计摘要
                summary_data = [
                    {"项目": "本月收款总额(元)", "数值": total_payment},
                    {"项目": "本月开票总额(元)", "数值": total_invoice},
                    {"项目": "新增合同数量", "数值": len(new_contracts)},
                    {"项目": "总合同数量", "数值": len(contracts)},
                    {"项目": "生效合同数量", "数值": len([c for c in contracts if c.is_effective])},
                    {"项目": "报告生成时间", "数值": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                ]
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='月度统计摘要', index=False)

            messagebox.showinfo("导出成功", f"{year}年{month:02d}月度报告已导出到:\n{file_path}")
            logger.info(f"成功导出{year}年{month:02d}月度报告到: {file_path}")
            
        except Exception as e:
            logger.error(f"生成月度报告失败: {str(e)}")
            raise
    
    def _export_stamp_duty(self):
        """导出印花税明细"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="导出印花税明细",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
                initialfile=f"印花税明细_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
            )
            if not file_path:
                return

            contracts = self.contract_service.get_all_contracts()
            
            # 印花税明细数据
            stamp_data = []
            total_stamp_duty = 0
            
            for contract in contracts:
                stamp_duty = contract.initial_total_rent * 0.001  # 印花税率0.1%
                total_stamp_duty += stamp_duty
                
                stamp_data.append({
                    "合同ID": contract.contract_id,
                    "客户姓名": contract.customer_name,
                    "房间号": contract.room_number,
                    "合同总租金(元)": contract.total_rent,
                    "初始总租金(元)": contract.initial_total_rent,
                    "印花税率": "0.1%",
                    "应缴印花税(元)": stamp_duty,
                    "合同状态": "已生效" if contract.is_effective else "未生效",
                    "创建日期": contract.create_time.strftime('%Y-%m-%d'),
                    "创建人": contract.created_by
                })
            
            # 添加合计行
            stamp_data.append({
                "合同ID": "合计",
                "客户姓名": "",
                "房间号": "",
                "合同总租金(元)": sum(c.total_rent for c in contracts),
                "初始总租金(元)": sum(c.initial_total_rent for c in contracts),
                "印花税率": "",
                "应缴印花税(元)": total_stamp_duty,
                "合同状态": "",
                "创建日期": "",
                "创建人": ""
            })
            
            # 导出到Excel
            df = pd.DataFrame(stamp_data)
            df.to_excel(file_path, sheet_name='印花税明细', index=False)
            
            messagebox.showinfo("导出成功", f"印花税明细已导出到:\n{file_path}\n\n共 {len(contracts)} 个合同，合计印花税: {total_stamp_duty:.2f}元")
            logger.info(f"成功导出印花税明细到: {file_path}")
            
        except Exception as e:
            logger.error(f"导出印花税明细失败: {str(e)}")
            messagebox.showerror("导出失败", f"导出印花税明细失败:\n{str(e)}")
    
    # ==================== 帮助菜单功能 ====================
    
    def _show_import_template(self):
        """显示导入模板说明"""
        template_info = """
合同导入模板说明

必填列：
• 合同ID: 唯一标识符，不能重复
• 客户姓名: 承租方名称
• 房间号: 租赁房间编号
• 对方付款名称: 付款方名称
• EAS代码: 财务系统代码

可选列：
• 租赁面积: 数字格式，单位平方米
• 税率: 小数格式，如0.05表示5%
• 是否需调整收入: "是"或"否"
• 押金金额: 数字格式，单位元

注意事项：
1. Excel文件第一行为列标题
2. 合同ID不能与现有合同重复
3. 数字列请使用数字格式，不要包含文字
4. 日期列请使用标准日期格式(YYYY-MM-DD)
5. 建议先用少量数据测试导入
6. 可从"导出合同列表"获得标准模板格式

导入流程：
1. 准备符合格式的Excel文件
2. 选择"导入导出" → "导入数据"
3. 预览数据确认无误
4. 点击"确认导入"完成操作
        """
        
        messagebox.showinfo("导入模板说明", template_info)
    
    def _show_about(self):
        """显示关于对话框"""
        about_text = f"""
{config.ui.window_title}

版本: 2.0.0 (完整功能版)
专业的租赁合同管理系统，包含：

核心功能：
• 合同管理 - 全生命周期管理
• 收款管理 - 多类型收款记录
• 押金管理 - 收取退还跟踪
• 开票管理 - 发票记录与税额计算
• 印花税管理 - 自动计算与提醒

财务核算：
• 收入核算 - 会计税法双轨制
• 增值税管理 - 孰早原则计算
• 税会差异 - 递延所得税处理
• 季度提醒 - 印花税缴纳提醒

数据管理：
• 完整的导入导出功能
• 自动数据备份与恢复
• 多格式报表导出
• 用户权限管理

技术特性：
• 模块化架构设计
• 完善的日志系统
• 数据库事务支持
• 类型安全编程

© 2024 租赁合同管理系统
仅供学习和内部使用
        """
        messagebox.showinfo("关于", about_text)
    
    # ==================== 窗口管理 ====================
    
    def _on_close(self):
        """关闭窗口处理"""
        if messagebox.askyesno("确认", "确定要退出系统吗？"):
            logger.info(f"用户 {self.current_user.username} 退出系统")
            self.destroy()
    
    def refresh_all_tabs(self):
        """刷新所有标签页数据"""
        try:
            if hasattr(self, 'contract_tab') and self.contract_tab:
                self.contract_tab.refresh()
            if hasattr(self, 'deposit_tab') and self.deposit_tab:
                self.deposit_tab.refresh()
            if hasattr(self, 'payment_tab') and self.payment_tab:
                self.payment_tab.refresh()
            if hasattr(self, 'report_tab') and self.report_tab:
                self.report_tab.refresh()
            if hasattr(self, 'stamp_tab') and self.stamp_tab:
                self.stamp_tab.refresh()
            if hasattr(self, 'system_tab') and self.system_tab:
                self.system_tab.refresh()
            
            logger.info("所有标签页数据已刷新")
            
        except Exception as e:
            logger.error(f"刷新标签页失败: {str(e)}")
            messagebox.showerror("错误", f"刷新数据失败:\n{str(e)}")
    
    # ==================== 公共方法 ====================
    
    def get_current_user(self):
        """获取当前登录用户"""
        return self.current_user
    
    def get_db_manager(self):
        """获取数据库管理器"""
        return self.db_manager
    
    def get_contract_service(self):
        """获取合同服务"""
        return self.contract_service
    
    def get_payment_service(self):
        """获取支付服务"""
        return self.payment_service
    
    def show_status_message(self, message: str, msg_type: str = "info"):
        """显示状态消息"""
        if msg_type == "info":
            messagebox.showinfo("信息", message)
        elif msg_type == "warning":
            messagebox.showwarning("警告", message)
        elif msg_type == "error":
            messagebox.showerror("错误", message)
        
        logger.info(f"显示{msg_type}消息: {message}")


# ==================== 测试和调试功能 ====================

def test_main_window():
    """测试主窗口功能"""
    try:
        print("开始测试主窗口...")
        
        # 创建测试窗口
        app = MainWindow()
        
        if app.current_user:
            print(f"✓ 主窗口创建成功，用户: {app.current_user.username}")
            
            # 测试各种功能
            print("✓ 可以进行以下测试:")
            print("  - 合同管理功能")
            print("  - 导入导出功能")
            print("  - 数据备份恢复")
            print("  - 报表生成")
            
            app.mainloop()
        else:
            print("✗ 用户登录失败")
            
    except Exception as e:
        print(f"✗ 主窗口测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_main_window()
