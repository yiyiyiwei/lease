"""
系统管理标签页UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import datetime
from typing import List, Dict, Any

from models.entities import User
from database.manager import DatabaseManager
from config.settings import config
from utils.logging import get_logger

logger = get_logger("SystemTab")


class SystemTab(ttk.Frame):
    """系统管理标签页"""
    
    def __init__(self, parent, db_manager: DatabaseManager, current_user: User):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.current_user = current_user
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建笔记本组件用于多个管理页面
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 数据管理标签页
        self._create_data_management_tab()
        
        # 用户管理标签页
        self._create_user_management_tab()
        
        # 系统信息标签页
        self._create_system_info_tab()
        
        # 操作日志标签页
        self._create_operation_log_tab()
    
    def _create_data_management_tab(self):
        """创建数据管理标签页"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="数据管理")
        
        # 标题
        ttk.Label(data_frame, text="数据备份与恢复", font=("SimHei", 12, "bold")).pack(pady=(10, 20))
        
        # 备份还原框架
        backup_frame = ttk.LabelFrame(data_frame, text="数据备份", padding="20")
        backup_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # 备份说明
        backup_info = """
数据备份说明：
• 系统将创建完整的数据库备份文件
• 备份文件包含所有合同、收款、押金等业务数据
• 建议定期备份以确保数据安全
• 备份文件存储在 backups 目录下
        """
        ttk.Label(backup_frame, text=backup_info.strip(), justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 15))
        
        # 备份操作按钮
        backup_button_frame = ttk.Frame(backup_frame)
        backup_button_frame.pack(fill=tk.X)
        
        ttk.Button(backup_button_frame, text="立即备份", command=self._backup_database).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(backup_button_frame, text="查看备份文件", command=self._view_backups).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(backup_button_frame, text="清理旧备份", command=self._cleanup_backups).pack(side=tk.LEFT)
        
        # 恢复框架
        restore_frame = ttk.LabelFrame(data_frame, text="数据恢复", padding="20")
        restore_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # 恢复说明
        restore_info = """
数据恢复说明：
• 选择备份文件进行数据恢复
• 恢复操作将覆盖当前所有数据，请谨慎操作
• 建议在恢复前先进行当前数据的备份
• 恢复完成后需要重启系统
        """
        ttk.Label(restore_frame, text=restore_info.strip(), justify=tk.LEFT, foreground="red").pack(anchor=tk.W, pady=(0, 15))
        
        # 恢复操作按钮
        ttk.Button(restore_frame, text="选择文件恢复", command=self._restore_database).pack(anchor=tk.W)
        
        # 数据清理框架
        cleanup_frame = ttk.LabelFrame(data_frame, text="数据清理", padding="20")
        cleanup_frame.pack(fill=tk.X, padx=20)
        
        cleanup_info = """
数据清理功能：
• 清理过期的操作日志记录
• 清理无效的临时数据
• 优化数据库性能
        """
        ttk.Label(cleanup_frame, text=cleanup_info.strip(), justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 15))
        
        cleanup_button_frame = ttk.Frame(cleanup_frame)
        cleanup_button_frame.pack(fill=tk.X)
        
        ttk.Button(cleanup_button_frame, text="清理操作日志", command=self._cleanup_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(cleanup_button_frame, text="优化数据库", command=self._optimize_database).pack(side=tk.LEFT)
    
    def _create_user_management_tab(self):
        """创建用户管理标签页"""
        user_frame = ttk.Frame(self.notebook)
        self.notebook.add(user_frame, text="用户管理")
        
        # 标题和操作按钮
        header_frame = ttk.Frame(user_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="用户管理", font=("SimHei", 12, "bold")).pack(side=tk.LEFT)
        
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="添加用户", command=self._add_user).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="修改密码", command=self._change_password).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="删除用户", command=self._delete_user).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="刷新", command=self._refresh_users).pack(side=tk.LEFT)
        
        # 用户列表
        user_columns = ("username", "role", "created_at", "status")
        self.user_tree = ttk.Treeview(user_frame, columns=user_columns, show="headings", selectmode="browse")
        
        # 设置列标题和宽度
        self.user_tree.heading("username", text="用户名")
        self.user_tree.heading("role", text="角色")
        self.user_tree.heading("created_at", text="创建时间")
        self.user_tree.heading("status", text="状态")
        
        self.user_tree.column("username", width=120)
        self.user_tree.column("role", width=100)
        self.user_tree.column("created_at", width=150)
        self.user_tree.column("status", width=100)
        
        # 滚动条
        user_scrollbar = ttk.Scrollbar(user_frame, orient="vertical", command=self.user_tree.yview)
        user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_tree.configure(yscrollcommand=user_scrollbar.set)
        self.user_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    def _create_system_info_tab(self):
        """创建系统信息标签页"""
        info_frame = ttk.Frame(self.notebook)
        self.notebook.add(info_frame, text="系统信息")
        
        # 创建滚动文本框显示系统信息
        canvas = tk.Canvas(info_frame)
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 系统信息内容
        info_content = ttk.Frame(scrollable_frame, padding="20")
        info_content.pack(fill=tk.BOTH, expand=True)
        
        # 基本信息
        basic_frame = ttk.LabelFrame(info_content, text="基本信息", padding="15")
        basic_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(basic_frame, text="系统名称:", font=("SimHei", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(basic_frame, text=config.ui.window_title).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(basic_frame, text="版本信息:", font=("SimHei", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(basic_frame, text="v1.0.0 (重构版)").grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(basic_frame, text="数据库路径:", font=("SimHei", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(basic_frame, text=config.database.db_path).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(basic_frame, text="日志目录:", font=("SimHei", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Label(basic_frame, text=config.logging.log_dir).grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(info_content, text="数据统计", padding="15")
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 统计变量
        self.stats_vars = {
            'total_contracts': tk.StringVar(),
            'effective_contracts': tk.StringVar(),
            'total_payments': tk.StringVar(),
            'total_deposits': tk.StringVar(),
            'total_invoices': tk.StringVar(),
            'total_users': tk.StringVar()
        }
        
        row = 0
        stats_labels = [
            ("合同总数:", 'total_contracts'),
            ("有效合同:", 'effective_contracts'),
            ("收款记录:", 'total_payments'),
            ("押金记录:", 'total_deposits'),
            ("开票记录:", 'total_invoices'),
            ("用户总数:", 'total_users')
        ]
        
        for i, (label_text, var_key) in enumerate(stats_labels):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_frame, text=label_text, font=("SimHei", 10, "bold")).grid(row=row, column=col, sticky=tk.W, pady=5, padx=(0 if col == 0 else 20, 0))
            ttk.Label(stats_frame, textvariable=self.stats_vars[var_key], foreground="blue").grid(row=row, column=col+1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 配置信息
        config_frame = ttk.LabelFrame(info_content, text="配置信息", padding="15")
        config_frame.pack(fill=tk.X)
        
        ttk.Label(config_frame, text="默认税率:", font=("SimHei", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(config_frame, text=f"{config.business.default_tax_rate*100:.1f}%").grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(config_frame, text="印花税率:", font=("SimHei", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(config_frame, text=f"{config.business.stamp_duty_rate*1000:.1f}‰").grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(config_frame, text="最大备份数:", font=("SimHei", 10, "bold")).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        ttk.Label(config_frame, text=str(config.database.max_backups)).grid(row=0, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(config_frame, text="日志大小限制:", font=("SimHei", 10, "bold")).grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        ttk.Label(config_frame, text=f"{config.logging.max_bytes // 1024 // 1024}MB").grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_operation_log_tab(self):
        """创建操作日志标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="操作日志")
        
        # 标题和操作按钮
        header_frame = ttk.Frame(log_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="操作日志", font=("SimHei", 12, "bold")).pack(side=tk.LEFT)
        
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="刷新日志", command=self._refresh_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导出日志", command=self._export_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="清空日志", command=self._clear_logs).pack(side=tk.LEFT)
        
        # 操作日志列表
        log_columns = ("operation_time", "user", "operation_type", "target_type", "target_id", "details")
        self.log_tree = ttk.Treeview(log_frame, columns=log_columns, show="headings", selectmode="browse")
        
        # 设置列标题和宽度
        self.log_tree.heading("operation_time", text="操作时间")
        self.log_tree.heading("user", text="用户")
        self.log_tree.heading("operation_type", text="操作类型")
        self.log_tree.heading("target_type", text="目标类型")
        self.log_tree.heading("target_id", text="目标ID")
        self.log_tree.heading("details", text="详细信息")
        
        self.log_tree.column("operation_time", width=150)
        self.log_tree.column("user", width=80)
        self.log_tree.column("operation_type", width=80)
        self.log_tree.column("target_type", width=80)
        self.log_tree.column("target_id", width=100)
        self.log_tree.column("details", width=200)
        
        # 滚动条
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_tree.configure(yscrollcommand=log_scrollbar.set)
        self.log_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    def _backup_database(self):
        """备份数据库"""
        try:
            # 创建备份目录
            os.makedirs(config.database.backup_dir, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"lease_backup_{timestamp}.db"
            backup_path = os.path.join(config.database.backup_dir, backup_filename)
            
            # 复制数据库文件
            shutil.copy2(config.database.db_path, backup_path)
            
            messagebox.showinfo("成功", f"数据库备份成功\n备份文件：{backup_filename}")
            logger.info(f"数据库备份成功: {backup_path}")
            
        except Exception as e:
            error_msg = f"数据库备份失败: {str(e)}"
            messagebox.showerror("错误", error_msg)
            logger.error(error_msg)
    
    def _view_backups(self):
        """查看备份文件"""
        try:
            backup_dir = config.database.backup_dir
            if os.path.exists(backup_dir):
                # 获取备份文件列表
                backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
                backup_files.sort(reverse=True)  # 按时间倒序
                
                if backup_files:
                    file_list = "\n".join(backup_files[:10])  # 显示最新的10个备份
                    messagebox.showinfo("备份文件列表", f"最新的备份文件：\n\n{file_list}")
                else:
                    messagebox.showinfo("提示", "暂无备份文件")
            else:
                messagebox.showinfo("提示", "备份目录不存在")
                
        except Exception as e:
            messagebox.showerror("错误", f"查看备份文件失败: {str(e)}")
    
    def _cleanup_backups(self):
        """清理旧备份"""
        try:
            backup_dir = config.database.backup_dir
            if not os.path.exists(backup_dir):
                messagebox.showinfo("提示", "备份目录不存在")
                return
            
            # 获取备份文件列表
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
            backup_files.sort()  # 按时间排序
            
            if len(backup_files) <= config.database.max_backups:
                messagebox.showinfo("提示", "备份文件数量未超过限制，无需清理")
                return
            
            # 删除多余的备份文件
            files_to_delete = backup_files[:-config.database.max_backups]
            deleted_count = 0
            
            for filename in files_to_delete:
                file_path = os.path.join(backup_dir, filename)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"删除备份文件失败: {file_path}, 错误: {str(e)}")
            
            messagebox.showinfo("成功", f"清理完成，删除了 {deleted_count} 个旧备份文件")
            
        except Exception as e:
            messagebox.showerror("错误", f"清理备份文件失败: {str(e)}")
    
    def _restore_database(self):
        """恢复数据库"""
        # 警告提示
        if not messagebox.askyesno("警告", 
                                   "数据恢复操作将覆盖当前所有数据！\n"
                                   "请确保已经备份了当前数据。\n\n"
                                   "是否继续？"):
            return
        
        try:
            # 选择备份文件
            file_path = filedialog.askopenfilename(
                title="选择备份文件",
                filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")],
                initialdir=config.database.backup_dir
            )
            
            if not file_path:
                return
            
            # 验证文件
            if not os.path.exists(file_path):
                messagebox.showerror("错误", "选择的文件不存在")
                return
            
            # 最后确认
            if not messagebox.askyesno("最后确认", 
                                       f"确定要从以下文件恢复数据吗？\n\n"
                                       f"{os.path.basename(file_path)}\n\n"
                                       f"此操作不可撤销！"):
                return
            
            # 执行恢复
            shutil.copy2(file_path, config.database.db_path)
            
            messagebox.showinfo("成功", "数据恢复成功！\n请重启系统以生效。")
            logger.info(f"数据库恢复成功: 从 {file_path}")
            
        except Exception as e:
            error_msg = f"数据库恢复失败: {str(e)}"
            messagebox.showerror("错误", error_msg)
            logger.error(error_msg)
    
    def _cleanup_logs(self):
        """清理操作日志"""
        if not messagebox.askyesno("确认", "确定要清理30天前的操作日志吗？"):
            return
        
        try:
            # 删除30天前的日志
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=30)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
            
            sql = "DELETE FROM operation_logs WHERE operation_time < ?"
            if self.db_manager.execute_command(sql, (cutoff_str,)):
                messagebox.showinfo("成功", "操作日志清理完成")
                self._refresh_logs()
            else:
                messagebox.showerror("错误", "清理操作日志失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"清理操作日志失败: {str(e)}")
    
    def _optimize_database(self):
        """优化数据库"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                conn.commit()
            
            messagebox.showinfo("成功", "数据库优化完成")
            logger.info("数据库优化完成")
            
        except Exception as e:
            error_msg = f"数据库优化失败: {str(e)}"
            messagebox.showerror("错误", error_msg)
            logger.error(error_msg)
    
    def _add_user(self):
        """添加用户"""
        # TODO: 实现用户添加对话框
        messagebox.showinfo("提示", "用户添加功能待实现")
    
    def _change_password(self):
        """修改密码"""
        # TODO: 实现密码修改对话框
        messagebox.showinfo("提示", "密码修改功能待实现")
    
    def _delete_user(self):
        """删除用户"""
        # TODO: 实现用户删除功能
        messagebox.showinfo("提示", "用户删除功能待实现")
    
    def _refresh_users(self):
        """刷新用户列表"""
        try:
            # 清空现有数据
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
            
            # 获取用户列表
            users = self.db_manager.execute_query("SELECT username, role, created_at FROM users ORDER BY created_at DESC")
            
            # 填充用户数据
            for user_data in users:
                status = "正常" if user_data['username'] != 'admin' else "系统管理员"
                created_at = user_data['created_at'] or "未知"
                
                self.user_tree.insert("", tk.END, values=(
                    user_data['username'],
                    user_data['role'],
                    created_at,
                    status
                ))
                
        except Exception as e:
            logger.error(f"刷新用户列表失败: {str(e)}")
            messagebox.showerror("错误", f"刷新用户列表失败: {str(e)}")
    
    def _refresh_logs(self):
        """刷新操作日志"""
        try:
            # 清空现有数据
            for item in self.log_tree.get_children():
                self.log_tree.delete(item)
            
            # 获取最近的操作日志
            logs = self.db_manager.execute_query("""
                SELECT operation_time, user, operation_type, target_type, target_id, details
                FROM operation_logs 
                ORDER BY operation_time DESC 
                LIMIT 1000
            """)
            
            # 填充日志数据
            for log_data in logs:
                self.log_tree.insert("", tk.END, values=(
                    log_data['operation_time'],
                    log_data['user'],
                    log_data['operation_type'],
                    log_data['target_type'],
                    log_data['target_id'],
                    log_data['details'] or ""
                ))
                
        except Exception as e:
            logger.error(f"刷新操作日志失败: {str(e)}")
            messagebox.showerror("错误", f"刷新操作日志失败: {str(e)}")
    
    def _export_logs(self):
        """导出操作日志"""
        # TODO: 实现日志导出功能
        messagebox.showinfo("提示", "日志导出功能待实现")
    
    def _clear_logs(self):
        """清空操作日志"""
        if not messagebox.askyesno("警告", "确定要清空所有操作日志吗？\n此操作不可撤销！"):
            return
        
        try:
            if self.db_manager.execute_command("DELETE FROM operation_logs"):
                messagebox.showinfo("成功", "操作日志已清空")
                self._refresh_logs()
            else:
                messagebox.showerror("错误", "清空操作日志失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"清空操作日志失败: {str(e)}")
    
    def _update_stats(self):
        """更新统计信息"""
        try:
            # 查询各种数据的统计
            stats_queries = {
                'total_contracts': "SELECT COUNT(*) as count FROM contracts",
                'effective_contracts': "SELECT COUNT(*) as count FROM contracts WHERE is_effective = 1",
                'total_payments': "SELECT COUNT(*) as count FROM payment_records",
                'total_deposits': "SELECT COUNT(*) as count FROM deposit_records",
                'total_invoices': "SELECT COUNT(*) as count FROM invoice_records",
                'total_users': "SELECT COUNT(*) as count FROM users"
            }
            
            for key, query in stats_queries.items():
                result = self.db_manager.execute_query(query)
                count = result[0]['count'] if result else 0
                self.stats_vars[key].set(str(count))
                
        except Exception as e:
            logger.error(f"更新统计信息失败: {str(e)}")
            # 设置默认值
            for var in self.stats_vars.values():
                var.set("0")
    
    def refresh(self):
        """刷新数据"""
        try:
            self._refresh_users()
            self._refresh_logs()
            self._update_stats()
        except Exception as e:
            logger.error(f"刷新系统管理数据失败: {str(e)}")
            messagebox.showerror("错误", f"刷新数据失败: {str(e)}")
