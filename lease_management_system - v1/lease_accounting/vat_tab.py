"""
增值税管理标签页 - UI模块
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import calendar
import pandas as pd

from tkcalendar import DateEntry
from models.entities import InvoiceRecord
from .core import LeaseAccounting
from utils.logging import get_logger

logger = get_logger("VATTab")


def add_vat_tab(app):
    """给主应用添加增值税管理标签页"""
    try:
        if not hasattr(app, 'notebook'):
            raise ValueError("传入的app实例缺少notebook属性，无法添加标签页")
        
        # 1. 创建标签页容器
        vat_tab = ttk.Frame(app.notebook)
        app.notebook.add(vat_tab, text="增值税管理")
        app.vat_tab = vat_tab

        # 2. 顶部功能区（开票登记按钮+查询条件）
        top_frame = ttk.Frame(vat_tab)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # 开票登记按钮
        ttk.Button(
            top_frame, text="登记开票",
            command=lambda: open_invoice_dialog(app)
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # 查询条件（年份+月份）
        ttk.Label(top_frame, text="查询月份：").pack(side=tk.LEFT, padx=5, pady=5)
        current_year = datetime.date.today().year
        app.vat_year_var = tk.StringVar(value=str(current_year))
        vat_year_combobox = ttk.Combobox(
            top_frame, textvariable=app.vat_year_var,
            values=[str(y) for y in range(current_year - 2, current_year + 2)],
            state="readonly", width=8
        )
        vat_year_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        app.vat_month_var = tk.StringVar(value=str(datetime.date.today().month))
        vat_month_combobox = ttk.Combobox(
            top_frame, textvariable=app.vat_month_var,
            values=[str(m) for m in range(1, 13)],
            state="readonly", width=5
        )
        vat_month_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        # 查询/导出按钮
        ttk.Button(
            top_frame, text="查询增值税",
            command=lambda: query_vat_records(app)
        ).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(
            top_frame, text="导出增值税表",
            command=lambda: export_vat_table(app)
        ).pack(side=tk.RIGHT, padx=5, pady=5)

        # 3. 增值税明细表格（含特殊情形标记）
        columns = (
            "vat_id", "contract_id", "customer_name", "relate_type",
            "relate_date", "total_amount", "vat_amount", "tax_date",
            "status", "special_case"
        )
        app.vat_tree = ttk.Treeview(vat_tab, columns=columns, show="headings", selectmode="extended")

        # 设置表头
        app.vat_tree.heading("vat_id", text="增值税ID")
        app.vat_tree.heading("contract_id", text="合同ID")
        app.vat_tree.heading("customer_name", text="客户姓名")
        app.vat_tree.heading("relate_type", text="触发类型")
        app.vat_tree.heading("relate_date", text="触发日期")
        app.vat_tree.heading("total_amount", text="含税金额(元)")
        app.vat_tree.heading("vat_amount", text="增值税额(元)")
        app.vat_tree.heading("tax_date", text="纳税义务日期")
        app.vat_tree.heading("status", text="纳税状态")
        app.vat_tree.heading("special_case", text="特殊情形")

        # 设置列宽和对齐
        app.vat_tree.column("vat_id", width=80)
        app.vat_tree.column("contract_id", width=100)
        app.vat_tree.column("customer_name", width=120)
        app.vat_tree.column("relate_type", width=100, anchor=tk.CENTER)
        app.vat_tree.column("relate_date", width=120)
        app.vat_tree.column("total_amount", width=120, anchor=tk.E)
        app.vat_tree.column("vat_amount", width=120, anchor=tk.E)
        app.vat_tree.column("tax_date", width=120)
        app.vat_tree.column("status", width=100, anchor=tk.CENTER)
        app.vat_tree.column("special_case", width=200)

        # 滚动条
        scrollbar_y = ttk.Scrollbar(vat_tab, orient="vertical", command=app.vat_tree.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x = ttk.Scrollbar(vat_tab, orient="horizontal", command=app.vat_tree.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        app.vat_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 4. 批量操作按钮（更新纳税状态）
        batch_frame = ttk.Frame(vat_tab)
        batch_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(
            batch_frame, text="标记选中为已缴税",
            command=lambda: mark_vat_paid(app)
        ).pack(side=tk.LEFT, padx=5)

        # 5. 显示表格
        app.vat_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        logger.info("增值税管理标签页加载成功")
    except Exception as e:
        logger.error(f"加载增值税管理标签页失败：{str(e)}")
        messagebox.showerror("错误", f"增值税管理标签页加载失败：{str(e)}")


def open_invoice_dialog(app):
    """打开开票登记对话框"""
    dialog = tk.Toplevel(app)
    dialog.title("登记开票记录")
    dialog.geometry("550x350")
    dialog.transient(app)
    dialog.grab_set()

    # 表单变量
    app.invoice_contract_var = tk.StringVar()
    app.invoice_amount_var = tk.StringVar()
    app.invoice_number_var = tk.StringVar()
    app.relate_payment_var = tk.StringVar()

    # 3. 表单布局
    frame = ttk.Frame(dialog, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    row = 0
    # 合同选择
    ttk.Label(frame, text="合同ID *：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    contract_combobox = ttk.Combobox(
        frame, textvariable=app.invoice_contract_var,
        values=[c.contract_id for c in app.contracts.values()],
        state="readonly", width=20
    )
    contract_combobox.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
    row += 1

    # 客户姓名显示（联动合同选择）
    ttk.Label(frame, text="客户姓名：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    app.invoice_customer_var = tk.StringVar()
    ttk.Entry(frame, textvariable=app.invoice_customer_var, state="readonly", width=20).grid(
        row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5
    )
    
    # 绑定合同选择事件，自动填充客户姓名
    def fill_customer_name(event):
        contract_id = app.invoice_contract_var.get()
        if contract_id in app.contracts:
            app.invoice_customer_var.set(app.contracts[contract_id].customer_name)
        else:
            app.invoice_customer_var.set("")
    contract_combobox.bind("<<ComboboxSelected>>", fill_customer_name)
    row += 1

    # 开票日期
    ttk.Label(frame, text="开票日期 *：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    date_entry = DateEntry(
        frame, width=12, background="darkblue", foreground="white",
        borderwidth=2, date_pattern="yyyy-mm-dd"
    )
    date_entry.set_date(datetime.date.today())
    date_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
    row += 1

    # 含税金额
    ttk.Label(frame, text="含税金额(元) *：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Entry(frame, textvariable=app.invoice_amount_var, width=20).grid(
        row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5
    )
    row += 1

    # 发票号
    ttk.Label(frame, text="发票号 *：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Entry(frame, textvariable=app.invoice_number_var, width=20).grid(
        row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5
    )
    row += 1

    # 关联收款ID（可选）
    ttk.Label(frame, text="关联收款ID（可选）：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Entry(frame, textvariable=app.relate_payment_var, width=20).grid(
        row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5
    )
    row += 1

    # 关联收入年份选择
    ttk.Label(frame, text="关联收入年份 *：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    app.relate_income_year_var = tk.StringVar(value=str(datetime.date.today().year))
    income_year_combobox = ttk.Combobox(
        frame, textvariable=app.relate_income_year_var,
        values=[str(y) for y in range(datetime.date.today().year - 2, datetime.date.today().year + 2)],
        state="readonly", width=8
    )
    income_year_combobox.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
    row += 1

    # 关联收入月份选择
    ttk.Label(frame, text="关联收入月份 *：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    app.relate_income_month_var = tk.StringVar(value=str(datetime.date.today().month))
    income_month_combobox = ttk.Combobox(
        frame, textvariable=app.relate_income_month_var,
        values=[str(m) for m in range(1, 13)],
        state="readonly", width=5
    )
    income_month_combobox.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
    row += 1

    # 错误提示
    app.invoice_msg_var = tk.StringVar()
    ttk.Label(frame, textvariable=app.invoice_msg_var, foreground="red").grid(
        row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5
    )
    row += 1

    # 保存按钮逻辑
    def save_invoice():
        try:
            # 验证必填项
            contract_id = app.invoice_contract_var.get().strip()
            invoice_date = date_entry.get_date()
            invoice_amount_str = app.invoice_amount_var.get().strip()
            invoice_number = app.invoice_number_var.get().strip()

            if not contract_id:
                raise ValueError("请选择合同ID")
            if not invoice_amount_str:
                raise ValueError("请输入含税金额")
            try:
                invoice_amount = float(invoice_amount_str)
                if invoice_amount <= 0:
                    raise ValueError("含税金额必须大于0")
            except ValueError:
                raise ValueError("含税金额必须为有效数字")
            if not invoice_number:
                raise ValueError("请输入发票号")
            if contract_id not in app.contracts:
                raise ValueError(f"合同ID {contract_id} 不存在")

            # 验证发票号唯一性
            existing_invoice = app.db.query(
                "SELECT id FROM invoice_details WHERE invoice_number=?",
                (invoice_number,)
            )
            if existing_invoice:
                raise ValueError(f"发票号{invoice_number}已存在，请重新输入")

            # 计算增值税+获取合同
            contract = app.contracts[contract_id]
            tax_rate = contract.tax_rate
            vat_amount = round(invoice_amount / (1 + tax_rate) * tax_rate, 2)

            # 关联收款ID（可选，处理空值）
            relate_payment_id = app.relate_payment_var.get().strip()
            relate_payment_id = int(relate_payment_id) if (relate_payment_id.isdigit() and relate_payment_id) else None
            
            # 获取用户选择的关联收入年月
            relate_income_year = int(app.relate_income_year_var.get())
            relate_income_month = int(app.relate_income_month_var.get())

            # 创建InvoiceRecord
            invoice = InvoiceRecord(
                date=invoice_date,
                amount=invoice_amount,
                tax_amount=vat_amount,
                invoice_number=invoice_number,
                contract_id=contract_id
            )

            # 保存到数据库
            contract.add_invoice(invoice, app.db, app.current_user['username'])
            app.db.execute('''
            INSERT INTO invoice_details (
                invoice_number, contract_id, invoice_date, total_amount, vat_amount,
                relate_payment_id, relate_income_year, relate_income_month, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'valid')
            ''', (invoice_number, contract_id, invoice_date.strftime("%Y-%m-%d"),
                  invoice_amount, vat_amount, relate_payment_id,
                  relate_income_year, relate_income_month))

            # 提示成功+刷新界面
            messagebox.showinfo("成功", f"开票记录已添加：\n"
                                       f"发票号：{invoice_number}\n"
                                       f"含税金额：{invoice_amount:.2f}元\n"
                                       f"增值税：{vat_amount:.2f}元")
            dialog.destroy()
            query_vat_records(app)

        except Exception as e:
            app.invoice_msg_var.set(f"错误：{str(e)}")
            logger.error(f"保存开票记录失败：{str(e)}")

    # 按钮布局
    button_frame = ttk.Frame(frame)
    button_frame.grid(row=row, column=0, columnspan=3, pady=10)
    ttk.Button(button_frame, text="保存", command=save_invoice).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    # 居中显示
    dialog.update_idletasks()
    x = (app.winfo_width() // 2) - (dialog.winfo_width() // 2) + app.winfo_x()
    y = (app.winfo_height() // 2) - (dialog.winfo_height() // 2) + app.winfo_y()
    dialog.geometry(f"+{x}+{y}")


def query_vat_records(app):
    """查询增值税记录"""
    try:
        year = int(app.vat_year_var.get())
        month = int(app.vat_month_var.get())
        tax_start_date = f"{year}-{month:02d}-01"
        tax_end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
        
        # 清空表格
        for item in app.vat_tree.get_children():
            app.vat_tree.delete(item)
        
        # 查询增值税记录
        vat_records = app.db.query('''
        SELECT DISTINCT
            vr.id AS vat_id, 
            vr.contract_id, 
            c.customer_name, 
            vr.relate_type,
            vr.tax_obligation_date AS tax_date, 
            vr.vat_amount, 
            vr.status,
            pr.date AS payment_relate_date,       
            pr.amount AS payment_total_amount,   
            id.invoice_date AS invoice_relate_date,  
            id.total_amount AS invoice_total_amount,
            mi.tax_income * (1 + c.tax_rate) AS receivable_total_amount
        FROM vat_records vr
        LEFT JOIN contracts c ON vr.contract_id = c.contract_id
        LEFT JOIN payment_records pr 
            ON vr.relate_type = 'payment' 
            AND vr.relate_id = CAST(pr.id AS TEXT)
        LEFT JOIN invoice_details id 
            ON vr.relate_type = 'invoice' 
            AND vr.relate_id = id.invoice_number
        LEFT JOIN monthly_income mi 
            ON vr.contract_id = mi.contract_id 
            AND mi.year = strftime('%Y', vr.tax_obligation_date)
            AND mi.month = strftime('%m', vr.tax_obligation_date)
        WHERE vr.tax_obligation_date BETWEEN ? AND ?
        ''', (tax_start_date, tax_end_date))

        # 处理特殊情形
        def get_special_case(relate_type, relate_date, tax_date, contract_id):
            """判断特殊情形：如"先收款后确认收入""先开票后收款" """
            if not relate_date or not tax_date or relate_date == "无":
                return ""
            try:
                relate_date_obj = datetime.datetime.strptime(relate_date, "%Y-%m-%d").date()
                tax_date_obj = datetime.datetime.strptime(tax_date, "%Y-%m-%d").date()
            except ValueError:
                return ""

            # 先收款/先开票：触发日期早于纳税义务日期
            if relate_type in ["payment", "invoice"] and relate_date_obj < tax_date_obj:
                income_exist = app.db.query('''
                SELECT id FROM monthly_income 
                WHERE contract_id=? AND year=? AND month=? AND tax_income>0
                ''', (contract_id, tax_date_obj.year, tax_date_obj.month))
                if income_exist:
                    return f"先{relate_type}后确认收入"
                else:
                    return f"先{relate_type}未确认收入"
            # 先确认收入未收款/未开票
            elif relate_type == "receivable":
                has_payment = app.db.query('''
                SELECT id FROM payment_records 
                WHERE contract_id=? AND date > ? AND amount>0
                ''', (contract_id, tax_date))
                has_invoice = app.db.query('''
                SELECT id FROM invoice_details 
                WHERE contract_id=? AND invoice_date > ? AND total_amount>0
                ''', (contract_id, tax_date))
                if has_payment and has_invoice:
                    return "先确认收入后收款开票"
                elif has_payment:
                    return "先确认收入后收款"
                elif has_invoice:
                    return "先确认收入后开票"
                else:
                    return "先确认收入未收款未开票"
            return ""

        total_vat = 0.0
        pending_vat = 0.0
        paid_vat = 0.0
        
        for record in vat_records:
            if record["relate_type"] == "payment":
                relate_date = record["payment_relate_date"] if record["payment_relate_date"] else None
                total_amount = round(float(record["payment_total_amount"]) if record["payment_total_amount"] else 0.0, 2)
            elif record["relate_type"] == "invoice":
                relate_date = record["invoice_relate_date"] if (
                    record["invoice_relate_date"] and str(record["invoice_relate_date"]).strip() != "None"
                ) else record["tax_date"]
                try:
                    invoice_total = float(record["invoice_total_amount"]) if (
                        record["invoice_total_amount"] and str(record["invoice_total_amount"]).strip() != "None"
                    ) else 0.0
                except (ValueError, TypeError):
                    invoice_total = 0.0
                total_amount = round(invoice_total, 2)
            elif record["relate_type"] == "receivable":
                relate_date = record["tax_date"] if record["tax_date"] else "未确定"
                try:
                    receivable_total = float(record["receivable_total_amount"]) if (
                        record["receivable_total_amount"] and str(record["receivable_total_amount"]).strip() != "None"
                    ) else 0.0
                except (ValueError, TypeError):
                    receivable_total = 0.0
                total_amount = round(receivable_total, 2)
                
            # 处理特殊情形
            special_case = get_special_case(
                record["relate_type"], relate_date, record["tax_date"], record["contract_id"]
            )
            
            # 累加合计
            vat_amount = round(float(record["vat_amount"]), 2)
            total_vat += vat_amount
            if record["status"] == "pending":
                pending_vat += vat_amount
            else:
                paid_vat += vat_amount
            
            # 插入表格
            app.vat_tree.insert("", tk.END, values=(
                record["vat_id"],
                record["contract_id"],
                record["customer_name"] or "未知客户",
                record["relate_type"],
                relate_date,
                f"{total_amount:.2f}",
                f"{vat_amount:.2f}",
                record["tax_date"],
                record["status"],
                special_case
            ))
        
        # 添加合计行
        app.vat_tree.insert("", tk.END, values=(
            "合计", "", "", "", "",
            f"--",
            f"{total_vat:.2f}",
            "",
            f"待缴:{pending_vat:.2f} | 已缴:{paid_vat:.2f}",
            ""
        ), tags=("vat_total",))
        app.vat_tree.tag_configure("vat_total", background="#f0f0f0", font=("Arial", 10, "bold"))
        
        logger.info(f"查询{year}年{month}月增值税记录完成，共{len(app.vat_tree.get_children())-1}条")
    except Exception as e:
        logger.error(f"查询增值税记录失败：{str(e)}")
        messagebox.showerror("错误", f"查询增值税记录失败：{str(e)}")


def mark_vat_paid(app):
    """标记选中的增值税记录为"已缴税" """
    try:
        # 获取选中的记录
        selected_items = app.vat_tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选中要标记的增值税记录")
            return

        # 确认操作
        if not messagebox.askyesno("确认", f"确定要将选中的{len(selected_items)}条记录标记为已缴税吗？"):
            return

        # 遍历选中记录，更新状态
        success_count = 0
        for item in selected_items:
            values = app.vat_tree.item(item, "values")
            vat_id = values[0]
            if vat_id == "合计":
                continue  # 跳过合计行

            # 更新数据库状态
            today = datetime.date.today().strftime("%Y-%m-%d")
            success = app.db.execute('''
            UPDATE vat_records 
            SET status = 'paid', payment_date = ? 
            WHERE id = ? AND status = 'pending'
            ''', (today, vat_id))

            if success:
                success_count += 1
                # 更新表格显示
                app.vat_tree.set(item, column="status", value="已缴")
                app.vat_tree.set(item, column="special_case", value=f"已缴：{today}")

        # 提示结果
        messagebox.showinfo("成功", f"共标记{success_count}条记录为已缴税")
        logger.info(f"用户{app.current_user['username']}标记{success_count}条增值税记录为已缴税")
        # 刷新合计行
        query_vat_records(app)
    except Exception as e:
        logger.error(f"标记增值税已缴失败：{str(e)}")
        messagebox.showerror("错误", f"标记增值税已缴失败：{str(e)}")


def export_vat_table(app):
    """导出增值税记录到Excel"""
    try:
        # 获取查询条件
        year = app.vat_year_var.get()
        month = app.vat_month_var.get()
        default_filename = f"{year}年{month}月增值税明细.xlsx"

        # 选择保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=default_filename,
            title="选择增值税明细导出路径"
        )
        if not file_path:
            return

        # 提取表格数据（排除合计行）
        data = []
        for item in app.vat_tree.get_children():
            values = app.vat_tree.item(item, "values")
            if values[0] == "合计":
                continue
            data.append({
                "增值税ID": values[0],
                "合同ID": values[1],
                "客户姓名": values[2],
                "触发类型": values[3],
                "触发日期": values[4],
                "含税金额(元)": float(values[5]),
                "增值税额(元)": float(values[6]),
                "纳税义务日期": values[7],
                "纳税状态": values[8],
                "特殊情形": values[9]
            })

        # 导出到Excel
        df = pd.DataFrame(data)
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=f"{year}年{month}月增值税明细", index=False)

        messagebox.showinfo("成功", f"增值税明细已导出至：\n{file_path}")
        logger.info(f"导出{year}年{month}月增值税明细到Excel：{file_path}")
    except Exception as e:
        logger.error(f"导出增值税明细失败：{str(e)}")
        messagebox.showerror("错误", f"导出增值税明细失败：{str(e)}")
