import customtkinter as ctk
import pyautogui
import schedule
import time
import threading
import webbrowser
import subprocess
from datetime import datetime, timedelta

# ---- SETUP GIAO DIỆN ----
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Auto Messenger Scheduler")
app.geometry("600x750")
app.resizable(False, False)

P_X = 36

scheduled_msgs = []
has_sent = set()
global_url = ""

def add_log(msg, color="#333"):
    log_box.configure(state="normal")
    now = datetime.now().strftime("%H:%M:%S")
    log_box.insert("end", f"[{now}] {msg}\n")
    log_box.tag_add(color, "end-2l", "end-1l")
    log_box.tag_config(color, foreground=color)
    log_box.see("end")
    log_box.configure(state="disabled")

def refresh_listbox():
    listbox_msgs.configure(state="normal")
    listbox_msgs.delete("1.0", "end")
    for i, line in enumerate(scheduled_msgs):
        listbox_msgs.insert("end", f"{i+1:02d}. {line}\n")
    listbox_msgs.configure(state="disabled")

def close_chrome():
    try:
        # Đóng chrome (trên Windows)
        subprocess.run("taskkill /IM chrome.exe /F", shell=True)
        add_log("Đã đóng Chrome.", "#e04b4a")
    except Exception as e:
        add_log(f"Lỗi đóng Chrome: {e}", "#e04b4a")

def send_message(msg, key, open_tab=False, force_restart=False):
    global global_url
    if force_restart:
        close_chrome()
        time.sleep(2)  # Đợi Chrome đóng hoàn toàn
        webbrowser.open(global_url)
        add_log("Đã mở lại tab Messenger, chờ 5 giây để load...", "#0084FF")
        time.sleep(5)
    elif open_tab:
        webbrowser.open(global_url)
        add_log("Đã mở tab Messenger, chờ 5 giây để load...", "#0084FF")
        time.sleep(5)
    # Click vào giữa màn hình để Messenger tự động focus khung nhập
    width, height = pyautogui.size()
    pyautogui.click(width//2, height//2)
    time.sleep(0.3)
    if key in has_sent:
        return
    has_sent.add(key)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")
    add_log(f"Đã gửi: {msg}", "#1cae3e")

def set_clipboard_and_send(msg, key, open_tab=False, force_restart=False):
    app.clipboard_clear()
    app.clipboard_append(msg)
    app.update()
    add_log(f"Chuẩn bị gửi: {msg}", "#0078d7")
    send_message(msg, key, open_tab=open_tab, force_restart=force_restart)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def on_add():
    hour = combo_hour.get()
    minute = combo_minute.get()
    msg = entry_msg.get().strip()
    if not hour or not minute or not msg:
        add_log("Thiếu giờ, phút hoặc nội dung!", "#e04b4a")
        return
    line = f"{hour.zfill(2)}:{minute.zfill(2)} | {msg}"
    scheduled_msgs.append(line)
    refresh_listbox()
    entry_msg.delete(0, "end")
    add_log(f"Đã thêm: {line}", "#1cae3e")

def on_del():
    # Xóa dòng cuối cùng
    if scheduled_msgs:
        removed = scheduled_msgs.pop()
        refresh_listbox()
        add_log(f"Đã xóa: {removed}", "#e04b4a")
    else:
        add_log("Không còn dòng nào để xóa.", "#e04b4a")

def on_schedule():
    global has_sent, global_url
    has_sent.clear()
    chat_url = entry_url.get().strip()
    global_url = chat_url
    if not chat_url or not scheduled_msgs:
        add_log("Chưa nhập URL hoặc chưa có tin nhắn!", "#e04b4a")
        return
    ok_schedule = 0
    first = True
    for line in scheduled_msgs:
        if "|" not in line:
            continue
        time_part, msg = line.split("|", 1)
        time_part = time_part.strip()
        msg = msg.strip()
        try:
            now = datetime.now()
            send_time = datetime.strptime(time_part, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            if send_time < now:
                send_time += timedelta(days=1)
            send_time_only = send_time.time()
            # Lần đầu chỉ mở tab, lần sau thì force restart chrome
            schedule.every().day.at(send_time_only.strftime("%H:%M:%S")).do(
                set_clipboard_and_send, msg=msg, key=f"{time_part}|{msg}",
                open_tab=first, force_restart=(not first)
            )
            first = False
            add_log(f"Đã lên lịch: {line} (gửi lúc {send_time_only.strftime('%H:%M:%S')})", "#0078d7")
            ok_schedule += 1
        except Exception as e:
            add_log(f"Lỗi dòng: {line} - {e}", "#e04b4a")
    if ok_schedule == 0:
        add_log("Không có dòng hợp lệ!", "#e04b4a")
        return
    threading.Thread(target=run_schedule, daemon=True).start()
    add_log("Đã bắt đầu chạy tiến trình gửi tự động.", "#0084FF")

# ==== GIAO DIỆN ====
lbl = ctk.CTkLabel(app, text="Auto Messenger Scheduler", font=("Segoe UI", 26, "bold"))
lbl.pack(pady=(28, 20))

ctk.CTkLabel(app, text="🔗 Link đoạn chat Messenger:", font=("Segoe UI", 15)).pack(anchor="w", padx=P_X)
entry_url = ctk.CTkEntry(app, width=520, height=38, font=("Segoe UI", 14))
entry_url.pack(pady=(8,20), padx=P_X)

add_frame = ctk.CTkFrame(app, fg_color="#f3f3f3")
add_frame.pack(fill="x", padx=P_X, pady=(0,18))
add_frame.columnconfigure(5, weight=1)

ctk.CTkLabel(add_frame, text="⏰", font=("Segoe UI", 15)).grid(row=0, column=0, padx=(6,3), pady=10)
combo_hour = ctk.CTkComboBox(add_frame, width=65, font=("Segoe UI", 14), values=[str(i).zfill(2) for i in range(24)])
combo_hour.set("08")
combo_hour.grid(row=0, column=1, padx=(0,3), pady=10)
ctk.CTkLabel(add_frame, text=":", font=("Segoe UI", 15, "bold")).grid(row=0, column=2, padx=(0,2), pady=10)
combo_minute = ctk.CTkComboBox(add_frame, width=65, font=("Segoe UI", 14), values=[str(i).zfill(2) for i in range(60)])
combo_minute.set("00")
combo_minute.grid(row=0, column=3, padx=(0,15), pady=10)
ctk.CTkLabel(add_frame, text="Nội dung:", font=("Segoe UI", 14)).grid(row=0, column=4, padx=(0,7), pady=10)
entry_msg = ctk.CTkEntry(add_frame, width=200, height=38, font=("Segoe UI", 14))
entry_msg.grid(row=0, column=5, sticky="ew", padx=(0,10), pady=10)
btn_add = ctk.CTkButton(add_frame, text="Thêm", width=80, command=on_add)
btn_add.grid(row=0, column=6, padx=(6,8), pady=10)

ctk.CTkLabel(app, text="📋 Danh sách mốc giờ đã lên lịch:", font=("Segoe UI", 15)).pack(anchor="w", padx=P_X, pady=(4,2))
frame_list = ctk.CTkFrame(app, fg_color="#f3f3f3")
frame_list.pack(padx=P_X, pady=(0,12), fill="x")
listbox_msgs = ctk.CTkTextbox(frame_list, width=500, height=135, font=("Segoe UI", 13), wrap="none")
listbox_msgs.pack(side="left", padx=(10,0), pady=9, fill="both", expand=True)
listbox_msgs.configure(state="disabled")
btn_del = ctk.CTkButton(frame_list, text="Xóa dòng cuối", fg_color="#e04b4a", width=110, command=on_del)
btn_del.pack(side="right", padx=(8,12), pady=18)

btn_schedule = ctk.CTkButton(
    app, text="LÊN LỊCH GỬI TẤT CẢ", fg_color="#0084FF", hover_color="#0057B8",
    font=("Segoe UI", 18, "bold"), width=420, height=54, corner_radius=28, command=on_schedule
)
btn_schedule.pack(pady=24)

ctk.CTkLabel(app, text="📑 Nhật ký hoạt động:", font=("Segoe UI", 15)).pack(anchor="w", padx=P_X)
log_box = ctk.CTkTextbox(app, width=520, height=120, font=("Consolas", 11))
log_box.pack(padx=P_X, pady=(8,24), fill="x")
log_box.configure(state="disabled")

app.mainloop()
