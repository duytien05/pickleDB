[![Logo](https://patx.github.io/pickledb/logo.png)](https://patx.github.io/pickledb)

[pickleDB](https://patx.github.io/pickledb) is a fast, easy to use, in-memory Python 
key-value store with first class asynchronous support. It is built with the `orjson` 
module for extremely high performance. It is licensed under the BSD three-clause 
license. [Check out the website](https://patx.github.io/pickledb) for installation 
instructions, API docs, advanced examples, benchmarks, and more.

```python
from pickledb import PickleDB

db = PickleDB("example.json").load()
db.set("key", "value")

db.get("key")  # return "value"
```

Tính năng 1: 
  -Mở 3 tab terminal (đã vào folders lưu file code "cd ...")
  -terminal 1 : source .venv/bin/activate (kích hoạt môi trường ảo .venv)
                python server.py --role slave --port 5002 (lệnh khởi động Node Slave)
  -terminal 2 : source .venv/bin/activate
                python server.py --role master --port 5001 --slaves 5002 (bật Node Master ở Port 5001, đồng thời khai báo cho nó biết có một Slave ở Port 5002)
  -terminal 3(Terminal này đóng vai trò là Client để gõ lệnh gửi dữ liệu, thực hiện các demo test)
    + Kịch bản 1: Ghi dữ liệu vào Master và kiểm tra tự động đồng bộ (Replication) 
        Gửi lệnh SET một key bất kỳ (ví dụ: mssv giá trị B123456) tới Master (5001): curl -X POST http://127.0.0.1:5001/set -H "Content-Type: application/json" -d "{\"key\": \"mssv\", \"value\": \"23010468\"}"
        Quan sát terminal 2 (Master): Bạn sẽ thấy dòng log in ra: [Master] Synced key 'mssv' to slave at http://127.0.0.1:5002
        Quan sát thư mục dự án: Bạn sẽ thấy xuất hiện 2 file mới tự động sinh ra là pickledb_master_5001.db và pickledb_slave_5002.db.
    + Kịch bản 2: Đọc dữ liệu từ Slave để chứng minh dữ liệu đã được nhân bản
        Thực hiện lệnh GET key mssv nhưng gửi tới Slave (5002): curl -X GET "http://127.0.0.1:5002/get?key=mssv"
        Kết quả mong đợi: Trả về JSON: {"key": "mssv", "status": "success", "value": "23010468"}. Dù bạn chưa từng gọi lệnh ghi trực tiếp vào Slave nhưng Slave vẫn có dữ liệu
    + Kịch bản 3: Kiểm tra luật Read-Only của Slave
        Cố tình gửi lệnh SET trực tiếp vào Slave (5002) xem Slave có chặn lại không: curl -X POST http://127.0.0.1:5002/set -H "Content-Type: application/json" -d "{\"key\": \"hack_db\", \"value\": \"999\"}"
        Kết quả mong đợi: Trả về lỗi 403 Forbidden với message: "Write operation denied. This is a Read-Only Slave Node!". Đúng tính chất của kiến trúc Master-Slave
    + Kịch bản 4: Demo Khả năng Chịu lỗi (Fault-Tolerance)
        Quay lại Terminal 2 (Master) và nhấn Ctrl + C để TẮT HẲN NODE MASTER. (Lúc này cụm Master đã sập)
        Quay lại Terminal 3 (Client), tiếp tục gọi lệnh ĐỌC từ Slave xem dữ liệu có bị mất hay hệ thống có bị tê liệt không: curl -X GET "http://127.0.0.1:5002/get?key=mssv"
        Kết quả mong đợi: Slave vẫn trả về kết quả 23010468 bình thường. Hệ thống vẫn hoạt động (ở chế độ đọc) bất chấp Node chính bị sập
