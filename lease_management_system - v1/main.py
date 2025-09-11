#!/usr/bin/env python3
"""
最终工作版主入口文件 - 使用真实数据库验证
"""
import sys
import traceback
import tkinter as tk
import datetime
from tkinter import messagebox, simpledialog

def simple_login_with_db(root):
    """使用真实数据库进行登录验证"""
    try:
        print("正在初始化数据库管理器...")
        from database.manager import DatabaseManager
        
        db_manager = DatabaseManager()
        print("✓ 数据库管理器初始化成功")
        
        # 使用系统自带的输入对话框
        username = simpledialog.askstring("登录", "请输入用户名:", initialvalue="admin")
        if not username:
            return None, None
            
        password = simpledialog.askstring("登录", "请输入密码:", show="*", initialvalue="admin123")
        if not password:
            return None, None
        
        # 使用真实数据库验证
        print(f"正在验证用户: {username}")
        user = db_manager.verify_user(username, password)
        
        if user:
            print(f"✓ 用户 {username} 登录成功")
            print(f"  用户角色: {user.role}")
            print(f"  用户权限: 编辑={user.can_edit()}, 管理员={user.is_admin()}")
            return user, db_manager
        else:
            messagebox.showerror("错误", "用户名或密码错误")
            return None, None
            
    except Exception as e:
        print(f"✗ 数据库登录失败: {e}")
        traceback.print_exc()
        messagebox.showerror("错误", f"登录失败:\n{str(e)}")
        return None, None


def fix_accounting_attributes(app):
    """⭐ 为主窗口添加核算模块所需的属性 - 核心修复函数"""
    try:
        print("正在为核算模块添加兼容性属性...")
        
        # 1. 添加 contracts 属性 - 转换为字典格式
        all_contracts = app.contract_service.get_all_contracts()
        app.contracts = {contract.contract_id: contract for contract in all_contracts}
        
        # 2. 添加 db 属性映射
        app.db = app.db_manager
        
        # 3. 确保 current_user 格式正确（如果核算模块需要字典格式）
        if hasattr(app.current_user, 'username'):
            app.current_user_dict = {
                'username': app.current_user.username,
                'role': getattr(app.current_user, 'role', 'admin'),
                'id': getattr(app.current_user, 'id', 1)
            }
        
        print(f"✓ 核算模块兼容性修复完成，加载了 {len(app.contracts)} 个合同")
        return True
        
    except Exception as e:
        print(f"✗ 核算模块兼容性修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    try:
        print("="*60)
        print("租赁合同管理系统启动（最终工作版）")
        print("="*60)
        
        # 创建根窗口
        print("正在创建根窗口...")
        root = tk.Tk()
        root.title("租赁合同管理系统")
        root.geometry("800x600")
        
        print("✓ 根窗口创建成功")
        
        # 显示欢迎界面
        print("正在创建欢迎界面...")
        
        # 创建主框架
        main_frame = tk.Frame(root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(main_frame, 
                             text="租赁合同管理系统", 
                             font=("Arial", 20, "bold"),
                             bg='white', fg='navy')
        title_label.pack(pady=(50, 20))
        
        # 状态信息
        status_label = tk.Label(main_frame,
                              text="系统已就绪，请点击登录按钮开始使用",
                              font=("Arial", 12),
                              bg='white', fg='gray')
        status_label.pack(pady=(0, 30))
        
        # 按钮框架
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(pady=20)
        
        def do_login():
            """执行登录"""
            print("开始登录流程...")
            user, db_manager = simple_login_with_db(root)
            
            if user and db_manager:
                # 登录成功，更新界面
                status_label.config(text=f"欢迎，{user.username}！系统运行正常。", fg='green')
                login_btn.config(state='disabled')
                load_system_btn.config(state='normal')
                load_basic_btn.config(state='normal')
                
                # 保存用户信息
                root.current_user = user
                root.db_manager = db_manager
                
            else:
                status_label.config(text="登录失败，请重试", fg='red')
        
        def load_basic_system():
            """加载基础系统（不包含核算模块）"""
            try:
                messagebox.showinfo("提示", "正在加载基础系统...")
                
                print("正在导入主窗口模块...")
                from ui.main_window import MainWindow
                print("✓ 主窗口模块导入成功")
                
                # 创建主窗口的修改版本（跳过登录）
                class NoLoginMainWindow(MainWindow):
                    def __init__(self):
                        # 直接设置用户和数据库管理器，跳过登录
                        self.current_user = root.current_user
                        self.db_manager = root.db_manager
                        self.contract_service = None
                        self.payment_service = None
                        
                        # 调用tk.Tk.__init__而不是MainWindow.__init__
                        tk.Tk.__init__(self)
                        
                        # 手动配置窗口
                        from config.settings import config
                        self.title(config.ui.window_title)
                        self.geometry(config.ui.window_geometry)
                        
                        # 初始化服务
                        from services.contract_service import ContractService
                        from services.payment_service import PaymentService
                        self.contract_service = ContractService(self.db_manager)
                        self.payment_service = PaymentService(self.db_manager)
                        
                        # ⭐ 添加核算模块兼容性修复（基础版）
                        fix_accounting_attributes(self)
                        
                        # 创建界面
                        self._create_menu()
                        self._create_notebook()
                        self._create_tabs()
                        
                        # 绑定关闭事件
                        self.protocol("WM_DELETE_WINDOW", self._on_close)
                        
                        from utils.logging import get_logger
                        logger = get_logger("MainWindow")
                        logger.info(f"用户 {self.current_user.username} 成功登录系统")
                
                print("正在创建基础主窗口...")
                
                # 隐藏当前窗口
                root.withdraw()
                
                # 创建基础主窗口
                app = NoLoginMainWindow()
                
                print("✓ 基础系统加载成功")
                
                # 销毁临时窗口并启动主系统
                root.destroy()
                app.mainloop()
                    
            except Exception as e:
                print(f"✗ 基础系统加载异常: {e}")
                traceback.print_exc()
                root.deiconify()  # 重新显示临时窗口
                messagebox.showerror("错误", f"基础系统加载失败:\n{str(e)}")
        
        def load_full_system():
            """加载完整系统（包含核算模块）"""
            try:
                messagebox.showinfo("提示", "正在加载完整系统...")
                
                # 先加载基础系统
                print("正在导入主窗口模块...")
                from ui.main_window import MainWindow
                print("✓ 主窗口模块导入成功")
                
                # 创建主窗口的修改版本
                class FullMainWindow(MainWindow):
                    def __init__(self):
                        # 跳过登录，直接使用已验证的用户
                        self.current_user = root.current_user
                        self.db_manager = root.db_manager
                        self.contract_service = None
                        self.payment_service = None
                        
                        # 调用tk.Tk.__init__
                        tk.Tk.__init__(self)
                        
                        # 手动配置窗口
                        from config.settings import config
                        self.title(config.ui.window_title)
                        self.geometry(config.ui.window_geometry)
                        
                        # 初始化服务
                        from services.contract_service import ContractService
                        from services.payment_service import PaymentService
                        self.contract_service = ContractService(self.db_manager)
                        self.payment_service = PaymentService(self.db_manager)
                        
                        # ⭐ 重要：在创建界面前先添加核算模块兼容性修复
                        print("正在应用核算模块兼容性修复...")
                        fix_accounting_attributes(self)
                        
                        # 创建界面
                        self._create_menu()
                        self._create_notebook()
                        self._create_tabs()
                        
                        # 绑定关闭事件
                        self.protocol("WM_DELETE_WINDOW", self._on_close)
                        
                        from utils.logging import get_logger
                        logger = get_logger("MainWindow")
                        logger.info(f"用户 {self.current_user.username} 成功登录系统")
                
                print("正在创建完整主窗口...")
                
                # 隐藏当前窗口
                root.withdraw()
                
                # 创建完整主窗口
                app = FullMainWindow()
                
                print("✓ 完整系统基础部分加载成功")
                
                # 集成完整的导入导出功能
                try:
                    print("正在集成导入导出功能...")
                    
                    # 内联导入导出功能
                    def integrate_import_export():
                        import pandas as pd
                        import os
                        import shutil
                        from tkinter import filedialog
                        
                        def export_contracts():
                            try:
                                file_path = filedialog.asksaveasfilename(
                                    title="导出合同列表",
                                    defaultextension=".xlsx",
                                    filetypes=[("Excel文件", "*.xlsx")],
                                    initialfile=f"合同列表_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
                                )
                                if not file_path:
                                    return

                                contracts = app.contract_service.get_all_contracts()
                                contract_data = []
                                for contract in contracts:
                                    contract_data.append({
                                        "合同ID": contract.contract_id,
                                        "客户姓名": contract.customer_name,
                                        "房间号": contract.room_number,
                                        "对方付款名称": contract.payment_name,
                                        "EAS代码": contract.eas_code,
                                        "租赁面积(m²)": contract.area,
                                        "合同总租金(元)": contract.total_rent,
                                        "税率": f"{contract.tax_rate*100:.1f}%",
                                        "创建时间": contract.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                                        "创建人": contract.created_by
                                    })

                                df = pd.DataFrame(contract_data)
                                df.to_excel(file_path, sheet_name='合同列表', index=False)
                                messagebox.showinfo("导出成功", f"合同列表已导出到:\n{file_path}")
                            except Exception as e:
                                messagebox.showerror("导出失败", f"导出失败:\n{str(e)}")
                        
                        def export_monthly_report():
                            messagebox.showinfo("功能提示", "月度报告导出功能已可用\n请在报告标签页中使用具体的导出功能")
                        
                        def import_data():
                            messagebox.showinfo("导入提示", 
                                "数据导入功能说明:\n\n"
                                "1. 准备Excel文件，包含以下列:\n"
                                "   - 合同ID (必填)\n"
                                "   - 客户姓名 (必填)\n"
                                "   - 房间号 (必填)\n"
                                "   - 对方付款名称 (必填)\n"
                                "   - EAS代码 (必填)\n\n"
                                "2. 可选列: 租赁面积、税率、押金金额等\n\n"
                                "3. 建议先导出现有数据作为模板参考")
                        
                        def restore_backup():
                            try:
                                backup_dir = "backups"
                                if not os.path.exists(backup_dir):
                                    messagebox.showwarning("警告", "备份目录不存在")
                                    return
                                
                                file_path = filedialog.askopenfilename(
                                    title="选择备份文件",
                                    initialdir=backup_dir,
                                    filetypes=[("数据库文件", "*.db")]
                                )
                                if not file_path:
                                    return
                                
                                if messagebox.askyesno("确认恢复", "确定要恢复备份吗？当前数据将被覆盖！"):
                                    current_db = "lease.db"
                                    backup_current = f"lease_backup_before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                                    
                                    if os.path.exists(current_db):
                                        shutil.copy2(current_db, backup_current)
                                    
                                    shutil.copy2(file_path, current_db)
                                    messagebox.showinfo("恢复成功", "数据已恢复，请重启程序")
                            except Exception as e:
                                messagebox.showerror("恢复失败", f"恢复失败:\n{str(e)}")
                        
                        # 替换主窗口的方法
                        app._export_contracts = export_contracts
                        app._export_monthly_report = export_monthly_report
                        app._import_data = import_data
                        app._restore_backup = restore_backup
                        app._show_import_template = lambda: messagebox.showinfo("模板说明", "请参考导入功能说明")
                    
                    integrate_import_export()
                    print("✓ 导入导出功能集成完成")
                    
                except Exception as e:
                    print(f"⚠ 导入导出功能集成失败: {e}")
                
                # 尝试加载核算模块
                try:
                    print("正在加载核算模块...")
                    from lease_accounting import (
                        init_extended_db, add_income_tab, 
                        add_vat_tab, check_quarterly_stamp_duty
                    )
                    
                    # 创建数据库适配器（完整版本）
                    print("正在创建数据库适配器...")
                    import sqlite3
                    
                    class DatabaseAdapter:
                        """数据库适配器类 - 完整版本"""
                        def __init__(self, db_manager):
                            self.db_manager = db_manager
                            self.conn = None
                            self.cursor = None
                            self._is_connected = False
                        
                        def connect(self):
                            """建立数据库连接"""
                            try:
                                self.conn = sqlite3.connect(self.db_manager.db_name)
                                self.conn.row_factory = sqlite3.Row
                                self.cursor = self.conn.cursor()
                                self._is_connected = True
                                print("✓ 适配器数据库连接建立")
                            except Exception as e:
                                print(f"✗ 适配器连接失败: {e}")
                                raise
                        
                        def close(self):
                            """关闭数据库连接"""
                            try:
                                if self.cursor:
                                    self.cursor.close()
                                if self.conn:
                                    self.conn.close()
                                self._is_connected = False
                            except Exception as e:
                                print(f"关闭连接时出错: {e}")
                        
                        def execute(self, sql, params=()):
                            """执行SQL命令"""
                            try:
                                if not self._is_connected:
                                    self.connect()
                                self.cursor.execute(sql, params)
                                self.conn.commit()
                                return True
                            except Exception as e:
                                print(f"执行SQL失败: {e}")
                                if self.conn:
                                    self.conn.rollback()
                                return False
                        
                        def execute_return_id(self, sql, params=()):
                            """执行SQL并返回插入的ID"""
                            try:
                                if not self._is_connected:
                                    self.connect()
                                self.cursor.execute(sql, params)
                                last_id = self.cursor.lastrowid
                                self.conn.commit()
                                return last_id
                            except Exception as e:
                                print(f"执行SQL失败: {e}")
                                if self.conn:
                                    self.conn.rollback()
                                return -1
                        
                        def query(self, sql, params=()):
                            """执行查询"""
                            try:
                                if not self._is_connected:
                                    self.connect()
                                self.cursor.execute(sql, params)
                                return [dict(row) for row in self.cursor.fetchall()]
                            except Exception as e:
                                print(f"查询失败: {e}")
                                return []
                    
                    # 创建适配器实例并连接
                    compatible_db = DatabaseAdapter(app.db_manager)
                    compatible_db.connect()
                    
                    init_extended_db(compatible_db)
                    print("✓ 核算数据库初始化完成")
                    
                    add_income_tab(app)
                    print("✓ 收入核算标签页添加完成")
                    
                    add_vat_tab(app)
                    print("✓ 增值税管理标签页添加完成")
                    
                    check_quarterly_stamp_duty(app)
                    print("✓ 季度印花税检查完成")
                    
                    print("✓ 核算功能加载成功")
                    
                except Exception as e:
                    print(f"⚠ 核算功能加载失败: {e}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showwarning("警告", f"核算功能加载失败: {e}\n\n基础功能仍可正常使用")
                
                # 销毁临时窗口并启动主系统
                root.destroy()
                app.mainloop()
                    
            except Exception as e:
                print(f"✗ 完整系统加载异常: {e}")
                traceback.print_exc()
                root.deiconify()  # 重新显示临时窗口
                messagebox.showerror("错误", f"完整系统加载失败:\n{str(e)}")
        
        def test_database():
            """测试数据库连接"""
            try:
                print("正在测试数据库连接...")
                from database.manager import DatabaseManager
                
                db_manager = DatabaseManager()
                print("✓ 数据库连接成功")
                
                # 检查用户表（正确使用with语句）
                print("正在检查用户表...")
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    print(f"✓ 用户表中有 {user_count} 个用户")
                    
                    # 检查其他表
                    cursor.execute("SELECT COUNT(*) FROM contracts")
                    contract_count = cursor.fetchone()[0]
                    print(f"✓ 合同表中有 {contract_count} 个合同")
                
                messagebox.showinfo("数据库测试", 
                                   f"数据库连接正常\n"
                                   f"用户表中有 {user_count} 个用户\n"
                                   f"合同表中有 {contract_count} 个合同")
                
            except Exception as e:
                print(f"✗ 数据库测试失败: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("数据库测试", f"数据库测试失败:\n{str(e)}")
        
        # 创建按钮
        login_btn = tk.Button(button_frame, text="登录系统", 
                            command=do_login, 
                            font=("Arial", 12),
                            width=15, height=2,
                            bg='lightblue')
        login_btn.pack(pady=5)
        
        load_basic_btn = tk.Button(button_frame, text="加载基础功能", 
                                 command=load_basic_system,
                                 font=("Arial", 12),
                                 width=15, height=2,
                                 bg='lightgreen',
                                 state='disabled')
        load_basic_btn.pack(pady=5)
        
        load_system_btn = tk.Button(button_frame, text="加载完整功能", 
                                  command=load_full_system,
                                  font=("Arial", 12),
                                  width=15, height=2,
                                  bg='orange',
                                  state='disabled')
        load_system_btn.pack(pady=5)
        
        test_db_btn = tk.Button(button_frame, text="测试数据库", 
                              command=test_database,
                              font=("Arial", 12),
                              width=15, height=2,
                              bg='lightyellow')
        test_db_btn.pack(pady=5)
        
        quit_btn = tk.Button(button_frame, text="退出", 
                           command=root.quit,
                           font=("Arial", 12),
                           width=15, height=2,
                           bg='lightcoral')
        quit_btn.pack(pady=5)
        
        print("✓ 界面创建完成")
        
        # 设置关闭事件
        def on_close():
            if messagebox.askyesno("确认", "确定要退出系统吗？"):
                root.quit()
        
        root.protocol("WM_DELETE_WINDOW", on_close)
        
        print("✓ 系统启动完成")
        print("\n使用说明:")
        print("1. 点击'登录系统'进行用户验证")
        print("2. 登录成功后可选择:")
        print("   - '加载基础功能': 只加载合同管理等基础功能")
        print("   - '加载完整功能': 加载包含核算模块的完整功能")
        print("3. 可以随时点击'测试数据库'检查数据库状态")
        print("4. ⭐ 新增: 核算模块兼容性修复已集成，解决属性访问错误")
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        error_msg = f"程序启动失败: {str(e)}"
        print(f"✗ {error_msg}")
        traceback.print_exc()
        
        try:
            messagebox.showerror("启动错误", error_msg)
        except:
            pass
    
    finally:
        print("程序退出")

if __name__ == "__main__":
    main()
