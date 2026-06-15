import argparse
from flask import Flask, request, jsonify
import requests
import pickledb as pickledb_mod

# Đoạn này để kiểm tra xem nó đang load file nào
print(f"[DEBUG] pickledb đang được load từ: {pickledb_mod.__file__}")

app = Flask(__name__)

# Khởi tạo các biến cấu hình toàn cục
ROLE = "master"
PORT = 5001
SLAVE_URLS = [] # Danh sách lưu địa chỉ các Slave (chỉ Master mới dùng)
db = None

@app.route('/get', methods=['GET'])
def get_value():
    """Endpoint xử lý lệnh GET (Cả Master và Slave đều dùng được)"""
    key = request.args.get('key')
    if not key:
        return jsonify({"status": "error", "message": "Missing key"}), 400
    
    # pickleDB mới: db.get() trả về giá trị mặc định (None) nếu không tìm thấy key
    value = db.get(key)
    
    # Kiểm tra xem key có thực sự tồn tại trong bộ nhớ không (vì value có thể là None hợp lệ)
    # Bản mới lưu dữ liệu trong dictionary `db.db`
    if key not in db.db:
        return jsonify({"status": "error", "message": f"Key '{key}' not found"}), 404
        
    return jsonify({"status": "success", "key": key, "value": value})


@app.route('/set', methods=['POST'])
def set_value():
    """Endpoint xử lý lệnh SET (Ghi dữ liệu)"""
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')
    
    # Biến kiểm tra xem request này đến từ Client hay do Master đồng bộ sang
    is_sync = data.get('is_sync', False)

    if not key or value is None:
        return jsonify({"status": "error", "message": "Missing key or value"}), 400

    # KIỂM TRA QUYỀN: Nếu là Slave và đây là lệnh ghi trực tiếp từ Client -> Từ chối!
    if ROLE == "slave" and not is_sync:
        return jsonify({
            "status": "error", 
            "message": "Write operation denied. This is a Read-Only Slave Node!"
        }), 403

    # Thực hiện ghi vào pickleDB cục bộ của Node hiện tại
    db.set(key, value)
    db.save() # Bản mới dùng hàm .save() thay vì .dump() để ghi xuống file cứng

    # NẾU LÀ MASTER: Tiến hành đồng bộ (Replicate) sang cho các Slave
    if ROLE == "master":
        for slave_url in SLAVE_URLS:
            try:
                # Gửi request POST sang bên Slave, kèm cờ is_sync=True
                requests.post(
                    f"{slave_url}/set", 
                    json={"key": key, "value": value, "is_sync": True},
                    timeout=2 # Timeout 2 giây để tránh treo Master nếu Slave sập
                )
                print(f"[Master] Synced key '{key}' to slave at {slave_url}")
            except requests.exceptions.RequestException:
                # Cơ chế chịu lỗi: Nếu Slave sập, Master vẫn sống và bỏ qua để phục vụ tiếp
                print(f"[Master] Failed to sync to slave {slave_url} (Slave might be offline)")

    return jsonify({"status": "success", "message": f"Data saved on {ROLE} node"})


if __name__ == '__main__':
    # Sử dụng argparse để truyền tham số từ Terminal khi chạy file
    parser = argparse.ArgumentParser(description="Distributed pickleDB Node")
    parser.add_argument('--role', choices=['master', 'slave'], required=True, help="Role of the node")
    parser.add_argument('--port', type=int, required=True, help="Port to run the server on")
    parser.add_argument('--slaves', type=str, help="Comma-separated list of slave ports (Only for master)")
    
    args = parser.parse_args()
    ROLE = args.role
    PORT = args.port

    # Cấu hình danh sách Slave cho Master
    if ROLE == "master" and args.slaves:
        ports = args.slaves.split(',')
        SLAVE_URLS = [f"http://127.0.0.1:{p}" for p in ports]

    # KHẮC PHỤC LỖI KHỞI TẠO CỦA BẢN MỚI:
    db_filename = f"pickledb_{ROLE}_{PORT}.db"
    
    # 1. Khởi tạo Object từ Class PickleDB
    db = pickledb_mod.PickleDB(db_filename)
    # 2. Gọi hàm nạp dữ liệu từ file cứng vào RAM
    db.load()

    print(f"[*] Starting {ROLE} node on port {PORT}...")
    app.run(host='127.0.0.1', port=PORT, debug=False)
