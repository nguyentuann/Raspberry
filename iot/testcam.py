import cv2

def open_camera():
    # Mở camera (0 là chỉ số của camera mặc định, có thể thay đổi nếu sử dụng camera khác)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Không thể mở camera")
        return

    while True:
        # Đọc từng frame từ camera
        ret, frame = cap.read()
        
        if not ret:
            print("Không thể nhận frame từ camera")
            break

        # Hiển thị video trong cửa sổ
        cv2.imshow("Camera", frame)

        # Nếu người dùng nhấn phím 'q', thoát khỏi vòng lặp
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Giải phóng tài nguyên khi kết thúc
    cap.release()
    cv2.destroyAllWindows()

# Gọi hàm để mở camera
open_camera()
