from flask import Flask, render_template, request
import calendar
from datetime import datetime

app = Flask(__name__)

# 自定義日曆類別，用來幫「今天」加上特殊的 HTML class
class HighlightCalendar(calendar.HTMLCalendar):
    def __init__(self, today_day):
        super().__init__()
        self.today_day = today_day

    def formatday(self, day, weekday):
        if day == self.today_day:
            return f'<td class="today">{day}</td>'
        if day == 0:
            return '<td class="noday">&nbsp;</td>'
        return f'<td class="day">{day}</td>'

@app.route("/")
def home():
    # 1. 取得真正的「今天」
    real_today = datetime.now()
    
    # 2. 從網址取得使用者想看的年份和月份 (如果沒給，就用今天)
    view_year = request.args.get('y', default=real_today.year, type=int)
    view_month = request.args.get('m', default=real_today.month, type=int)

    # 3. 計算「上個月」與「下個月」的數值 (用於按鈕連結)
    prev_m = view_month - 1 if view_month > 1 else 12
    prev_y = view_year if view_month > 1 else view_year - 1
    next_m = view_month + 1 if view_month < 12 else 1
    next_y = view_year if view_month < 12 else view_year + 1

    # 4. 如果看的正是「本月」，就標記今天；否則不標記
    highlight_day = real_today.day if (view_year == real_today.year and view_month == real_today.month) else -1
    
    # 5. 產生 HTML 格式的日曆
    cal = HighlightCalendar(highlight_day)
    cal_html = cal.formatmonth(view_year, view_month)

    message = f"現在是 {real_today.year} 年 {real_today.month} 月 {real_today.day} 日"
    view_title = f"{view_year} 年 {view_month} 月"

    return render_template("index.html", 
                           msg=message, 
                           view_title=view_title,
                           calendar_html=cal_html,
                           prev_y=prev_y, prev_m=prev_m,
                           next_y=next_y, next_m=next_m)

if __name__ == "__main__":
    app.run(debug=True)