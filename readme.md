<h1 align="center">🎮 GRABBING GAME™ – Game Cào Tay Đỉnh Cao, Căng Đét Từng Giây</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/controller-Arduino%20(optional)-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/status-READY%20TO%20FIGHT-green?style=for-the-badge" />
</p>

---

## 🚀 Giới thiệu ngắn gọn mà cháy

**GRABBING GAME™** là game tay đôi dành cho các thần đồng nhặt đồ.  
Điều khiển 2 nhân vật đẩy – xoay – chụp – thả item về rổ để lấy điểm.  
Bàn phím chiến ổn. Có Arduino càng chill. Có cả server gửi điểm nếu bạn thích kiểu esports 😎

> Game đơn giản, chơi 60s, nhưng gây nghiện 60 năm.

---

## 💾 Setup dễ như ăn snack

```bash
# 1. Clone repo
git clone https://github.com/Minhmice/grabbing-game.git
cd grabbing-game

# 2. Cài Python packages (nếu chưa có)
pip install pygame pyserial

# 3. Mở game
python main.py
````

> 💡 **Không có Arduino?** Không sao cả! Vẫn chơi bằng bàn phím mượt như sáp.

---

## 🕹️ Controls

### ✋ Người chơi 1 (BLUE):

| Hành động | Phím   |
| --------- | ------ |
| Tiến/lùi  | W / S  |
| Trái/phải | A / D  |
| Xoay      | Q / E  |
| Chụp item | F      |
| Sẵn sàng  | LSHIFT |

### 🔥 Người chơi 2 (RED):

| Hành động | Phím         |
| --------- | ------------ |
| Tiến/lùi  | ↑ / ↓        |
| Trái/phải | ← / →        |
| Xoay      | NumPad 4 / 6 |
| Chụp item | M            |
| Sẵn sàng  | RSHIFT       |

> 🎛️ **Có dùng Arduino** thì game auto đọc giá trị joystick và nút bấm.
> Dữ liệu truyền từ serial như: `x,y,rot,...` → được map tốc độ/movement xịn xò.

---

## 🧠 Gameplay cơ bản

1. Vào menu, mỗi người **ấn Ready** (phím hoặc nút Arduino)
2. Game **countdown 3 giây** → bắt đầu chơi
3. Nhặt item → chụp bằng gripper → thả vào basket bên mình
4. Sau 60 giây: **Game Over**, điểm tổng được gửi lên scoreboard server.

---

## 🧱 Tính năng chất chơi người dơi

* ✅ Chơi full màn hình, scale auto mọi kích thước
* 🎮 Điều khiển qua bàn phím hoặc Arduino (có code đọc serial luôn)
* 🧲 Gripper "hút đồ" cực bén – pick & drop không trượt phát nào
* 🧠 AI-free, code 100% tay người – dễ debug, dễ mod
* 🌐 Server TCP có sẵn để gửi điểm số sang scoreboard UI

---

## 🖼 Giao diện siêu yêu

* Có background pool cute
* Countdown khổng lồ trước khi bắt đầu
* Mỗi player có avatar, rổ riêng, điểm riêng
* Font nét căng, màu rõ ràng – nhìn phát hiểu luôn ai thắng

---

## 🧪 Arduino Setup (tuỳ chọn)

```py
ARDUINO_SERIAL_PORT = 'COM3'  # đổi nếu khác
ARDUINO_BAUD_RATE = 115200
```

Code đọc serial đã viết sẵn:

```py
def read_arduino_data():
    line = ser.readline().decode('utf-8').strip()
    ...
```

> ⚠️ Không tìm thấy cổng? Tool sẽ chạy không Arduino. Không vấn đề.

---

## 🔄 Flow Game

```
Main Menu → Ready → Countdown → 60s Gameplay → Game Over → Gửi điểm
```

---

## 🛠 Khó chịu? Gỡ liền tay

| Vấn đề                | Giải pháp                                  |
| --------------------- | ------------------------------------------ |
| Không kết nối Arduino | Kiểm tra COM port đúng chưa                |
| Không thấy item spawn | Chờ 2s hoặc kiểm tra `ITEM_SPAWN_INTERVAL` |
| Countdown lỗi         | Check `COUNTDOWN_TIME` và `get_time_ms()`  |
| Không gửi được điểm   | Kiểm tra server có chạy chưa, cổng 12345   |

---

## 🧼 Clean restart?

Nhấn ESC bất kỳ lúc nào để thoát game an toàn và đóng serial nếu đang mở.

---

## ❤️ Made với tất cả sự cay cú

> Viết ra game này vì mấy trò chơi bây giờ không có cảm giác nữa.
> Chơi Grabbing Game không cần nhiều não – chỉ cần trái tim và 2 ngón tay thần tốc.

<p align="center"><strong>💻 Coded by <span style='color:#f40;'>bạn dev buồn ngủ</span> – nhưng vẫn gõ đến dòng cuối cùng</strong></p>

<p align="center"><i>Chúc bạn thắng thật to, nhưng quan trọng hơn là... vui 😎</i></p>

