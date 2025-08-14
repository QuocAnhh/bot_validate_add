from google.generativeai.types import FunctionDeclaration, Tool

# đây là cấu trúc mà LLM sẽ "nhìn" vào để hiểu công cụ này làm gì và cần tham số nào'
# search địa chỉ
search_address_func = FunctionDeclaration(
    name="search_address_in_vietnam",
    description="Tìm kiếm một địa chỉ ở Việt Nam để lấy thông tin chi tiết và tọa độ. Chỉ sử dụng công cụ này khi bạn có một địa chỉ đủ cụ thể để tìm kiếm.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Địa chỉ đầy đủ cần tìm kiếm. Ví dụ: 'công viên hòa bình, hà nội' hoặc '550 phạm văn đồng, quận bình thạnh'",
            }
        },
        "required": ["query"],
    },
)

# tìm kiếm chuyến đi
find_trips_func = FunctionDeclaration(
    name="find_trips",
    description="Tìm kiếm các chuyến xe (khách, taxi, xe ghép) dựa trên điểm đi, điểm đến và thời gian khởi hành.",
    parameters={
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Địa chỉ điểm đi đã được xác thực. Ví dụ: 'Bến xe Mỹ Đình, Hà Nội'",
            },
            "destination": {
                "type": "string",
                "description": "Địa chỉ điểm đến đã được xác thực. Ví dụ: 'Bến xe Cát Bà, Hải Phòng'",
            },
            "departure_time": {
                "type": "string",
                "description": "Thời gian khởi hành mong muốn. Ví dụ: '9:00 AM 25/12/2023'",
            },
        },
        "required": ["origin", "destination", "departure_time"],
    },
)

# đăt vé
book_trip_func = FunctionDeclaration(
    name="book_trip",
    description="Đặt một chuyến đi cụ thể sau khi người dùng đã lựa chọn. Chỉ sử dụng khi đã có 'trip_id'.",
    parameters={
        "type": "object",
        "properties": {
            "trip_id": {
                "type": "string",
                "description": "Mã định danh của chuyến đi được chọn từ kết quả của 'find_trips'.",
            },
            "passenger_name": {
                "type": "string",
                "description": "Tên đầy đủ của hành khách.",
            },
            "passenger_phone": {
                "type": "string",
                "description": "Số điện thoại của hành khách.",
            },
        },
        "required": ["trip_id", "passenger_name", "passenger_phone"],
    },
)


booking_tools = Tool(
    function_declarations=[
        search_address_func,
        find_trips_func,
        book_trip_func,
    ]
)