"""
印花税季度提醒模块
"""
import datetime
import calendar
from tkinter import messagebox

from .core import LeaseAccounting
from utils.logging import get_logger

logger = get_logger("StampDuty")


def check_quarterly_stamp_duty(app):
    """
    季度末提示缴纳印花税（3/6/9/12月最后5天触发）
    :param app: 主应用实例
    """
    try:
        today = datetime.date.today()
        # 季度末月份（3/6/9/12）且在最后5天
        quarter_end_months = [3, 6, 9, 12]
        if today.month not in quarter_end_months:
            return

        # 当月最后一天
        month_last_day = calendar.monthrange(today.year, today.month)[1]
        if (month_last_day - today.day) > 5:
            return  # 不在最后5天，不提示

        # 计算本季度新增合同的印花税总和
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        quarter_start_date = datetime.date(today.year, quarter_start_month, 1)
        quarter_end_date = today

        total_stamp_duty = 0.0
        quarterly_contracts = []
        
        for contract in app.contracts.values():
            # 合同创建时间（转换为date对象）
            create_time = contract.create_time
            if isinstance(create_time, datetime.datetime):
                create_date = create_time.date()
            else:
                create_date = create_time

            # 本季度新增的合同
            if quarter_start_date <= create_date <= quarter_end_date:
                # 计算印花税
                accounting_obj = LeaseAccounting(contract, app.db)
                stamp_duty = accounting_obj.calculate_stamp_duty()
                total_stamp_duty += stamp_duty
                quarterly_contracts.append({
                    "contract_id": contract.contract_id,
                    "customer_name": contract.customer_name,
                    "stamp_duty": stamp_duty
                })

        # 有印花税时提示
        if total_stamp_duty > 0:
            quarter_num = (today.month - 1) // 3 + 1
            msg = f"季度末印花税提醒\n\n" \
                  f"当前为{today.year}年第{quarter_num}季度末，需缴纳本季度新增合同印花税：\n" \
                  f"合计金额：{total_stamp_duty:.2f}元\n\n" \
                  f"涉及合同（共{len(quarterly_contracts)}个）：\n"
            
            for c in quarterly_contracts[:10]:  # 最多显示10个合同
                msg += f"- {c['contract_id']}（{c['customer_name']}）：{c['stamp_duty']:.2f}元\n"
            if len(quarterly_contracts) > 10:
                msg += f"- ...（还有{len(quarterly_contracts)-10}个合同）\n"
            
            msg += f"\n请及时完成缴纳！"

            messagebox.showwarning("印花税提示", msg)
            logger.info(f"向用户{app.current_user['username']}发送季度印花税提示：{total_stamp_duty:.2f}元")
            
    except Exception as e:
        logger.error(f"季度印花税提示失败：{str(e)}")
