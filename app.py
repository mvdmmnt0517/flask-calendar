from flask import Flask, render_template, request, session, redirect, url_for
import calendar
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = "f8#2d_K9L!zPqX6vW5r_p0A1"

# --- 日曆邏輯 ---
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

# --- 2048 核心邏輯 ---
def merge_left(row):
    nums = [i for i in row if i != 0]
    new_row = []
    points = 0
    skip = False
    for i in range(len(nums)):
        if skip:
            skip = False
            continue
        if i + 1 < len(nums) and nums[i] == nums[i+1]:
            val = nums[i] * 2
            new_row.append(val)
            points += val
            skip = True
        else:
            new_row.append(nums[i])
    return new_row + [0] * (6 - len(new_row)), points

def add_tile_dynamic(board):
    flat_board = [cell for row in board for cell in row]
    max_val = max(flat_board) if any(flat_board) else 2
    
    options = [2, 4, 8, 16, 32, 64]
    weights = [64, 32, 16, 8, 4, 2]
    
    valid_options = []
    valid_weights = []
    for i in range(len(options)):
        if options[i] <= max_val:
            valid_options.append(options[i])
            valid_weights.append(weights[i])

    empty = [(r, c) for r in range(6) for c in range(6) if board[r][c] == 0]
    if empty:
        r, c = random.choice(empty)
        board[r][c] = random.choices(valid_options, weights=valid_weights, k=1)[0]
    return board

def check_game_over(board):
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0: return False
            if c < 5 and board[r][c] == board[r][c+1]: return False
            if r < 5 and board[r][c] == board[r+1][c]: return False
    return True

# --- 路由設定 ---

@app.route("/")
def home():
    real_today = datetime.now()
    view_year = request.args.get('y', default=real_today.year, type=int)
    view_month = request.args.get('m', default=real_today.month, type=int)
    prev_m = view_month - 1 if view_month > 1 else 12
    prev_y = view_year if view_month > 1 else view_year - 1
    next_m = view_month + 1 if view_month < 12 else 1
    next_y = view_year if view_month < 12 else view_year + 1
    cal = HighlightCalendar(real_today.day if (view_year == real_today.year and view_month == real_today.month) else -1)
    return render_template("index.html", view_title=f"{view_year} 年 {view_month} 月",
                           calendar_html=cal.formatmonth(view_year, view_month),
                           prev_y=prev_y, prev_m=prev_m, next_y=next_y, next_m=next_m)

@app.route("/2048")
def game_2048():
    if "board" not in session or len(session["board"]) != 6:
        # 修正：補上初始化邏輯
        session["board"] = add_tile_dynamic(add_tile_dynamic([[0]*6 for _ in range(6)]))
        session["score"] = 0
        session["game_over"] = False
    
    return render_template("2048.html", 
                           board=session["board"], 
                           score=session["score"], 
                           best=session.get("best_2048", 0),
                           game_over=session.get("game_over", False))

@app.route("/2048/move/<dir>")
def move_2048(dir):
    board = session.get("board")
    if not board: return redirect(url_for('game_2048'))
    
    total_points = 0
    temp_board = []

    # 修正：補齊位移邏輯
    if dir == "left":
        for row in board:
            res, pts = merge_left(row)
            temp_board.append(res); total_points += pts
    elif dir == "right":
        for row in board:
            res, pts = merge_left(row[::-1])
            temp_board.append(res[::-1]); total_points += pts
    elif dir == "up":
        transposed = [list(row) for row in zip(*board)]
        merged = []
        for col in transposed:
            res, pts = merge_left(col)
            merged.append(res); total_points += pts
        temp_board = [list(row) for row in zip(*merged)]
    elif dir == "down":
        transposed = [list(row) for row in zip(*board)]
        merged = []
        for col in transposed:
            res, pts = merge_left(col[::-1])
            merged.append(res[::-1]); total_points += pts
        temp_board = [list(row) for row in zip(*merged)]
    else:
        temp_board = board

    # 執行你的規則：產生新數字
    final_board = add_tile_dynamic(temp_board)

    # 更新 Session
    session["board"] = final_board
    session["score"] = session.get("score", 0) + total_points
    if session["score"] > session.get("best_2048", 0):
        session["best_2048"] = session["score"]
    
    # 檢查是否死亡
    session["game_over"] = check_game_over(final_board)
            
    return redirect(url_for('game_2048'))

@app.route("/2048/reset")
def reset_2048():
    session.pop("board", None)
    session.pop("score", None)
    session.pop("game_over", None)
    return redirect(url_for('game_2048'))

@app.route("/game", methods=["GET", "POST"])
def game():
    if "target" not in session:
        session["target"] = random.randint(1, 100)
        session["attempts"] = 0
        session["msg"] = "請輸入 1-100 的數字。"
    if request.method == "POST":
        try:
            guess = int(request.form.get("num"))
            session["attempts"] += 1
            if guess < session["target"]: session["msg"] = f"太小了！({session['attempts']}次)"
            elif guess > session["target"]: session["msg"] = f"太大了！({session['attempts']}次)"
            else:
                session["msg"] = f"中了！共猜了{session['attempts']}次。"
                session.pop("target") 
        except: session["msg"] = "無效數字！"
    return render_template("game.html", message=session["msg"])

if __name__ == "__main__":
    app.run(debug=True)