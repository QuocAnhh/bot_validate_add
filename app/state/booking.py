from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class BookingState:
    """lưu trữ trạng thái của quá trình đặt vé"""
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_time: Optional[str] = None
    
    # lưu trữ danh sách các chuyến xe tìm được
    available_trips: List[Dict[str, Any]] = field(default_factory=list)
    
    # lưu trữ id của chuyến xe được chọn
    selected_trip_id: Optional[str] = None
    
    # trạng thái của quá trình đặt vé
    status: str = "pending"

    def is_ready_for_search(self) -> bool:
        """kiểm tra xem có đủ thông tin để tìm chuyến xe"""
        return self.origin is not None and self.destination is not None and self.departure_time is not None 