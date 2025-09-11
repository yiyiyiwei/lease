"""
免租期对话框UI模块
"""
import tkinter as tk
from tkinter import ttk
import datetime
from typing import Optional, Tuple

from utils.logging import get_logger

logger = get_logger("FreePeriodDialog")


class FreePeriodDialog(tk.Toplevel):
    """免租期对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.result: Optional[Tuple[datetime.date, datetime.date]] = None
        
        # 配置对话框
        self.title("添加免租期")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # 创建界面
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
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="添加免租期",
            font=("SimHei", 12, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 表单框架
        form_frame = ttk.LabelFrame(main_frame, text="免租期信息", padding="15")
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 开始日期
        ttk.Label(form_frame, text="开始日期:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        self.start_date_frame = ttk.Frame(form_frame)
        self.start_date_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=10)
        
        self.start_year_var = tk.StringVar()
        self.start_month_var = tk.StringVar()
        self.start_day_var = tk.StringVar()
        
        # 年份
        ttk.Label(self.start_date_frame, text="年:").pack(side=tk.LEFT)
        start_year_combo = ttk.Combobox(
            self.start_date_frame,
            textvariable=self.start_year_var,
            values=[str(year) for year in range(2020, 2030)],
            width=6,
            state="readonly"
        )
        start_year_combo.pack(side=tk.LEFT, padx=2)
        
        # 月份
        ttk.Label(self.start_date_frame, text="月:").pack(side=tk.LEFT, padx=(10, 0))
        start_month_combo = ttk.Combobox(
            self.start_date_frame,
            textvariable=self.start_month_var,
            values=[f"{month:02d}" for month in range(1, 13)],
            width=4,
            state="readonly"
        )
        start_month_combo.pack(side=tk.LEFT, padx=2)
        
        # 日期
        ttk.Label(self.start_date_frame, text="日:").pack(side=tk.LEFT, padx=(10, 0))
        start_day_combo = ttk.Combobox(
            self.start_date_frame,
            textvariable=self.start_day_var,
            values=[f"{day:02d}" for day in range(1, 32)],
            width=4,
            state="readonly"
        )
        start_day_combo.pack(side=tk.LEFT, padx=2)
        
        # 结束日期
        ttk.Label(form_frame, text="结束日期:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        self.end_date_frame = ttk.Frame(form_frame)
        self.end_date_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)
        
        self.end_year_var = tk.StringVar()
        self.end_month_var = tk.StringVar()
        self.end_day_var = tk.StringVar()
        
        # 年份
        ttk.Label(self.end_date_frame, text="年:").pack(side=tk.LEFT)
        end_year_combo = ttk.Combobox(
            self.end_date_frame,
            textvariable=self.end_year_var,
            values=[str(year) for year in range(2020, 2030)],
            width=6,
            state="readonly"
        )
        end_year_combo.pack(side=tk.LEFT, padx=2)
        
        # 月份
        ttk.Label(self.end_date_frame, text="月:").pack(side=tk.LEFT, padx=(10, 0))
        end_month_combo = ttk.Combobox(
            self.end_date_frame,
            textvariable=self.end_month_var,
            values=[f"{month:02d}" for month in range(1, 13)],
            width=4,
            state="readonly"
        )
        end_month_combo.pack(side=tk.LEFT, padx=2)
        
        # 日期
        ttk.Label(self.end_date_frame, text="日:").pack(side=tk.LEFT, padx=(10, 0))
        end_day_combo = ttk.Combobox(
            self.end_date_frame,
            textvariable=self.end_day_var,
            values=[f"{day:02d}" for day in range(1, 32)],
            width=4,
            state="readonly"
        )
        end_day_combo.pack(side=tk.LEFT, padx=2)
        
        # 错误消息标签
        self.message_var = tk.StringVar()
        message_label = ttk.Label(
            form_frame,
            textvariable=self.message_var,
            foreground="red",
            font=("SimHei", 9)
        )
        message_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 保存按钮
        ttk.Button(button_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.LEFT)
        
        # 设置默认值为当前日期
        today = datetime.date.today()
        self.start_year_var.set(str(today.year))
        self.start_month_var.set(f"{today.month:02d}")
        self.start_day_var.set(f"{today.day:02d}")
        
        self.end_year_var.set(str(today.year))
        self.end_month_var.set(f"{today.month:02d}")
        self.end_day_var.set(f"{today.day:02d}")
    
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
            # 清除之前的错误消息
            self.message_var.set("")
            
            # 验证开始日期
            try:
                start_year = int(self.start_year_var.get())
                start_month = int(self.start_month_var.get())
                start_day = int(self.start_day_var.get())
                start_date = datetime.date(start_year, start_month, start_day)
            except ValueError:
                self.message_var.set("开始日期格式错误")
                return False
            
            # 验证结束日期
            try:
                end_year = int(self.end_year_var.get())
                end_month = int(self.end_month_var.get())
                end_day = int(self.end_day_var.get())
                end_date = datetime.date(end_year, end_month, end_day)
            except ValueError:
                self.message_var.set("结束日期格式错误")
                return False
            
            # 验证日期逻辑
            if start_date > end_date:
                self.message_var.set("开始日期不能晚于结束日期")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"输入验证失败: {str(e)}")
            self.message_var.set(f"验证失败: {str(e)}")
            return False
    
    def _save(self):
        """保存数据"""
        if not self._validate_input():
            return
        
        try:
            # 构建结果数据
            start_year = int(self.start_year_var.get())
            start_month = int(self.start_month_var.get())
            start_day = int(self.start_day_var.get())
            start_date = datetime.date(start_year, start_month, start_day)
            
            end_year = int(self.end_year_var.get())
            end_month = int(self.end_month_var.get())
            end_day = int(self.end_day_var.get())
            end_date = datetime.date(end_year, end_month, end_day)
            
            self.result = (start_date, end_date)
            
            logger.info(f"免租期数据保存: {self.result}")
            self.destroy()
            
        except Exception as e:
            logger.error(f"保存免租期数据失败: {str(e)}")
            self.message_var.set(f"保存失败: {str(e)}")
    
    def _cancel(self):
        """取消编辑"""
        self.result = None
        self.destroy()