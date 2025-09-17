"""
收入核算标签页 - UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import calendar
import pandas as pd

from .core import LeaseAccounting
from utils.logging import get_logger

logger = get_logger("IncomeTab")


def add_income_tab(app):
    """给主应用添加收入核算标签页"""
    try:
        if not hasattr(app, 'notebook'):
            raise ValueError("传入的app实例缺少notebook属性，无法添加标签页")
        
        # 1. 创建标签页，挂载到app的notebook
        income_tab = ttk.Frame(app.notebook)
        app.notebook.add(income_tab, text="收入核算")
        app.income_tab = income_tab

        # 2. 顶部查询条件（年份+月份+查询/导出按钮）
        top_frame = ttk.Frame(income_tab)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # 年份选择（支持近5年）
        ttk.Label(top_frame, text="年份：").pack(side=tk.LEFT, padx=5, pady=5)
        current_year = datetime.date.today().year
        app.income_year_var = tk.StringVar(value=str(current_year))
        # 关键修改：将下拉框实例保存到app对象
        app.income_year_combobox = ttk.Combobox(
            top_frame, textvariable=app.income_year_var,
            values=[str(y) for y in range(current_year - 4, current_year + 2)],
            state="readonly", width=8
        )
        app.income_year_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        # 月份选择
        ttk.Label(top_frame, text="月份：").pack(side=tk.LEFT, padx=5, pady=5)
        app.income_month_var = tk.StringVar(value=str(datetime.date.today().month))
        # 关键修改：将下拉框实例保存到app对象
        app.income_month_combobox = ttk.Combobox(
            top_frame, textvariable=app.income_month_var,
            values=[str(m) for m in range(1, 13)],
            state="readonly", width=5
        )
        app.income_month_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        # 查询/导出按钮
        ttk.Button(
            top_frame, text="查询收入", 
            command=lambda: query_monthly_income(app)
        ).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(
            top_frame, text="导出Excel", 
            command=lambda: export_income_table(app)
        ).pack(side=tk.RIGHT, padx=5, pady=5)

        # 3. 收入明细表格（会计/税法/税会差异）
        columns = (
            "contract_id", "customer_name", "room_number", "is_adjust",
            "accounting_income", "tax_income", "diff_amount", "deferred_tax",
            "to_be_settled_vat", "adjust_vat"
        )
        app.income_tree = ttk.Treeview(income_tab, columns=columns, show="headings", selectmode="extended")

        # 设置表头
        app.income_tree.heading("contract_id", text="合同ID")
        app.income_tree.heading("customer_name", text="客户姓名")
        app.income_tree.heading("room_number", text="房间号")
        app.income_tree.heading("is_adjust", text="是否调整收入")
        app.income_tree.heading("accounting_income", text="会计收入(元)")
        app.income_tree.heading("tax_income", text="税法收入(元)")
        app.income_tree.heading("diff_amount", text="税会差异(元)")
        app.income_tree.heading("deferred_tax", text="递延所得税(元)")
        app.income_tree.heading("to_be_settled_vat", text="待转销项税额(元)")
        app.income_tree.heading("adjust_vat", text="冲减待转销项(元)")

        # 设置列宽和对齐（金额列右对齐）
        app.income_tree.column("contract_id", width=100)
        app.income_tree.column("customer_name", width=120)
        app.income_tree.column("room_number", width=80)
        app.income_tree.column("is_adjust", width=100, anchor=tk.CENTER)
        app.income_tree.column("accounting_income", width=120, anchor=tk.E)
        app.income_tree.column("tax_income", width=120, anchor=tk.E)
        app.income_tree.column("diff_amount", width=120, anchor=tk.E)
        app.income_tree.column("deferred_tax", width=120, anchor=tk.E)
        app.income_tree.column("to_be_settled_vat", width=140, anchor=tk.E)
        app.income_tree.column("adjust_vat", width=140, anchor=tk.E)

        # 滚动条（支持垂直+水平）
        scrollbar_y = ttk.Scrollbar(income_tab, orient="vertical", command=app.income_tree.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x = ttk.Scrollbar(income_tab, orient="horizontal", command=app.income_tree.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        app.income_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 4. 显示表格
        app.income_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        logger.info("收入核算标签页加载成功")
    except Exception as e:
        logger.error(f"加载收入核算标签页失败：{str(e)}")
        messagebox.showerror("错误", f"收入核算标签页加载失败：{str(e)}")


def query_monthly_income(app):
    """查询指定月份的收入明细"""
    try:
        # 关键修复：强制将下拉框当前值同步到变量
        app.income_year_var.set(app.income_year_combobox.get())
        app.income_month_var.set(app.income_month_combobox.get())
        
        # 调试打印（验证同步结果）
        print("同步后变量值:", app.income_year_var.get(), app.income_month_var.get())
        print("下拉框实际值:", app.income_year_combobox.get(), app.income_month_combobox.get())
        
        # 现在获取的就是同步后的最新值
        year = int(app.income_year_var.get())
        month = int(app.income_month_var.get())
        query_month_last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])

        # 清空表格现有数据
        for item in app.income_tree.get_children():
            app.income_tree.delete(item)

        # 遍历所有合同，仅计算"已到租期"的合同
        total_accounting = 0.0
        total_tax = 0.0
        total_diff = 0.0
        total_deferred = 0.0
        total_to_be_settled = 0.0
        total_adjust = 0.0

        for contract in app.contracts.values():
            # 过滤未到租期的合同
            if not contract.rent_periods:
                logger.warning(f"合同 {contract.contract_id} 没有租金期数据，已跳过")
                continue
                
            contract_start = min(rp.start_date for rp in contract.rent_periods)

            # 若合同起始日 > 查询月份最后一天 → 跳过，不计算收入
            if contract_start > query_month_last_day:
                continue  # 未到租期，跳过该合同

            # 对已到租期的合同，正常计算收入和税差
            accounting_obj = LeaseAccounting(contract, app.db)
            tax_diff_data = accounting_obj.calculate_tax_diff(year, month)

            # 跳过无收入的合同
            if tax_diff_data["accounting_income"] == 0 and tax_diff_data["tax_income"] == 0:
                continue

            # 累加合计值
            total_accounting += tax_diff_data["accounting_income"]
            total_tax += tax_diff_data["tax_income"]
            total_diff += tax_diff_data["diff_amount"]
            total_deferred += tax_diff_data["deferred_tax"]
            total_to_be_settled += tax_diff_data["to_be_settled_vat"]
            total_adjust += tax_diff_data["adjust_vat"]

            # 添加数据到表格
            app.income_tree.insert("", tk.END, values=(
                tax_diff_data["contract_id"],
                tax_diff_data["customer_name"],
                tax_diff_data["room_number"],
                "是" if tax_diff_data["is_adjust"] else "否",
                f"{tax_diff_data['accounting_income']:.2f}",
                f"{tax_diff_data['tax_income']:.2f}",
                f"{tax_diff_data['diff_amount']:.2f}",
                f"{tax_diff_data['deferred_tax']:.2f}",
                f"{tax_diff_data['to_be_settled_vat']:.2f}",
                f"{tax_diff_data['adjust_vat']:.2f}"
            ))

        # 添加合计行
        app.income_tree.insert("", tk.END, values=(
            "合计", "", "", "",
            f"{total_accounting:.2f}",
            f"{total_tax:.2f}",
            f"{total_diff:.2f}",
            f"{total_deferred:.2f}",
            f"{total_to_be_settled:.2f}",
            f"{total_adjust:.2f}"
        ), tags=("total_row",))
        app.income_tree.tag_configure("total_row", background="#f0f0f0", font=("Arial", 10, "bold"))

        logger.info(f"查询{year}年{month}月收入明细完成，共{len(app.income_tree.get_children())-1}个已到租期合同")
    except ValueError as e:
        logger.error(f"查询收入失败：日期格式错误 - {str(e)}")
        messagebox.showerror("错误", f"日期格式错误：{str(e)}")
    except Exception as e:
        logger.error(f"查询收入失败：{str(e)}")
        messagebox.showerror("错误", f"查询收入失败：{str(e)}")


def export_income_table(app):
    """导出收入明细到Excel"""
    try:
        # 1. 获取当前查询的年份和月份
        year = app.income_year_var.get()
        month = app.income_month_var.get()
        default_filename = f"{year}年{month}月收入核算明细.xlsx"

        # 2. 选择保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=default_filename,
            title="选择收入明细导出路径"
        )
        if not file_path:
            return  # 用户取消导出

        # 3. 提取表格数据（排除合计行）
        data = []
        for item in app.income_tree.get_children():
            values = app.income_tree.item(item, "values")
            if values[0] == "合计":
                continue  # 跳过合计行
            # 整理数据为字典（与表格列对应）
            data.append({
                "合同ID": values[0],
                "客户姓名": values[1],
                "房间号": values[2],
                "是否调整收入": values[3],
                "会计不含税收入(元)": float(values[4]),
                "税法不含税收入(元)": float(values[5]),
                "税会差异(元)": float(values[6]),
                "递延所得税(元)": float(values[7]),
                "待转销项税额(元)": float(values[8]),
                "冲减待转销项税额(元)": float(values[9])
            })

        # 4. 添加合计行数据
        total_values = app.income_tree.item(app.income_tree.get_children()[-1], "values")
        data.append({
            "合同ID": "合计",
            "客户姓名": "",
            "房间号": "",
            "是否调整收入": "",
            "会计不含税收入(元)": float(total_values[4]),
            "税法不含税收入(元)": float(total_values[5]),
            "税会差异(元)": float(total_values[6]),
            "递延所得税(元)": float(total_values[7]),
            "待转销项税额(元)": float(total_values[8]),
            "冲减待转销项税额(元)": float(total_values[9])
        })

        # 5. 导出到Excel
        df = pd.DataFrame(data)
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=f"{year}年{month}月收入明细", index=False)

        # 6. 提示成功
        messagebox.showinfo("成功", f"收入明细已导出至：\n{file_path}")
        logger.info(f"导出{year}年{month}月收入明细到Excel：{file_path}")
    except Exception as e:
        logger.error(f"导出收入明细失败：{str(e)}")
        messagebox.showerror("错误", f"导出收入明细失败：{str(e)}")
