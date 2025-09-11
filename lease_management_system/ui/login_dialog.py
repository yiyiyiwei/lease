"""
登录对话框UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from database.manager import DatabaseManager
from models.entities import User
from utils.logging import get_logger

logger = get_logger("LoginDialog")


class LoginDialog(tk.Toplevel):
    """登录对话框"""
    
    def __init__(self, parent: tk.Tk, db_manager: DatabaseManager):
        super().__init__(parent)
        
        self.parent = parent
        self.db_manager = db_manager
        self.result: Optional[User] = None
        
        # 配置对话框
        self.title("用户登录")
        self.geometry("350x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # 创建界面
        self._create_widgets()
        self._center_window()
        
        # 绑定回车键
        self.bind('<Return>', lambda e: self._login())
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="租赁合同管理系统",
            font=("SimHei", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 用户名输入
        ttk.Label(main_frame, text="用户名:").pack(anchor=tk.W, pady=(0, 5))
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=25)
        self.username_entry.pack(fill=tk.X, pady=(0, 10))
        self.username_entry.focus()  # 设置焦点
        
        # 密码输入
        ttk.Label(main_frame, text="密码:").pack(anchor=tk.W, pady=(0, 5))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            main_frame,
            textvariable=self.password_var,
            show="*",
            width=25
        )
        self.password_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 错误消息标签
        self.message_var = tk.StringVar()
        self.message_label = ttk.Label(
            main_frame,
            textvariable=self.message_var,
            foreground="red",
            font=("SimHei", 9)
        )
        self.message_label.pack(pady=(0, 10))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 登录按钮
        login_button = ttk.Button(
            button_frame,
            text="登录",
            command=self._login,
            width=12
        )
        login_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_button = ttk.Button(
            button_frame,
            text="取消",
            command=self._cancel,
            width=12
        )
        cancel_button.pack(side=tk.LEFT)
        
        # 默认管理员提示
        hint_label = ttk.Label(
            main_frame,
            text="默认管理员: admin / admin123",
            font=("SimHei", 8),
            foreground="gray"
        )
        hint_label.pack(pady=(15, 0))
    
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
    
    def _login(self):
        """执行登录验证"""
        try:
            username = self.username_var.get().strip()
            password = self.password_var.get().strip()
            
            # 验证输入
            if not username:
                self.message_var.set("请输入用户名")
                self.username_entry.focus()
                return
            
            if not password:
                self.message_var.set("请输入密码")
                self.password_entry.focus()
                return
            
            # 清除之前的错误消息
            self.message_var.set("")
            
            # 验证用户
            user = self.db_manager.verify_user(username, password)
            if user:
                self.result = user
                logger.info(f"用户 {username} 登录成功")
                self.destroy()
            else:
                self.message_var.set("用户名或密码错误")
                self.password_var.set("")  # 清空密码
                self.password_entry.focus()
                logger.warning(f"用户 {username} 登录失败")
                
        except Exception as e:
            error_msg = f"登录失败: {str(e)}"
            self.message_var.set(error_msg)
            logger.error(f"登录异常: {str(e)}")
    
    def _cancel(self):
        """取消登录"""
        self.result = None
        self.destroy()
