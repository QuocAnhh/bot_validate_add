from google.generativeai.types import FunctionDeclaration, Tool

# đây là cấu trúc mà LLM sẽ "nhìn" vào để hiểu công cụ này làm gì và cần tham số nào
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


address_validation_tool = Tool(
    function_declarations=[search_address_func]
)