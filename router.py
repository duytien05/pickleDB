from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Cấu hình danh sách các Shard trong hệ thống
SHARDS = {
    0: "http://127.0.0.1:6001",
    1: "http://127.0.0.1:6002"
}

def get_shard_url(key):
    """
    Thuật toán phân tán: Băm key để xác định Shard tương ứng.
    Sử dụng hàm hash() có sẵn của Python và ép kiểu dương để tránh số âm
    """
    shard_index = abs(hash(key)) % len(SHARDS)
    return SHARDS[shard_index], shard_index


@app.route('/router/set', methods=['POST'])
def route_set():
    """Nhận lệnh SET từ Client và điều hướng tới đúng Shard"""
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')

    if not key or value is None:
        return jsonify({"status": "error", "message": "Missing key or value"}), 400

    # Tính toán xem key này thuộc Shard nào
    target_url, shard_id = get_shard_url(key)
    print(f"[Router] Key '{key}' belongs to Shard {shard_id} ({target_url})")

    try:
        # Chuyển tiếp (Forward) request nguyên vẹn sang Shard đó
        # Vì các Shard chạy độc lập nên gửi như một lệnh POST thông thường
        response = requests.post(f"{target_url}/set", json={"key": key, "value": value})
        return (response.content, response.status_code, response.headers.items())
    except requests.exceptions.RequestException:
        return jsonify({"status": "error", "message": f"Shard {shard_id} is offline"}), 500


@app.route('/router/get', methods=['GET'])
def route_get():
    """Nhận lệnh GET từ Client, băm key để biết cần lấy từ Shard nào"""
    key = request.args.get('key')
    if not key:
        return jsonify({"status": "error", "message": "Missing key"}), 400

    # Tìm xem key này ngày xưa được lưu ở Shard nào
    target_url, shard_id = get_shard_url(key)
    print(f"[Router] Looking for Key '{key}' in Shard {shard_id} ({target_url})")

    try:
        # Đến đúng Shard đó để lấy dữ liệu về cho Client
        response = requests.get(f"{target_url}/get", params={"key": key})
        return (response.content, response.status_code, response.headers.items())
    except requests.exceptions.RequestException:
        return jsonify({"status": "error", "message": f"Shard {shard_id} is offline"}), 500


if __name__ == '__main__':
    PORT = 6000
    print(f"[*] Starting Router Node on port {PORT}...")
    app.run(host='127.0.0.1', port=PORT, debug=False)
