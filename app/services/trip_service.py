import logging
import re
from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.database import get_session
from app.models.trip import Trip, Base
from app.services.database import init_db

logger = logging.getLogger(__name__)

try:
    init_db(Base)
except Exception as e:
    logger.warning(f"DB init skipped: {e}")

def extract_city_from_address(address: str) -> str:
    if not address:
        return ""
    
    city_patterns = {
        'hà nội': ['hà nội', 'hanoi', 'đống đa', 'ba đình', 'hoàn kiếm', 'cầu giấy', 'nam từ liêm', 'bắc từ liêm', 'hai bà trưng', 'thanh xuân', 'mỹ đình', 'mễ trì', 'long biên'],
        'hải phòng': ['hải phòng', 'haiphong', 'hồng bàng', 'ngô quyền', 'lê chân', 'cát bà', 'đồ sơn'],
        'hồ chí minh': ['hồ chí minh', 'sài gòn', 'tp hcm', 'quận 1', 'quận 2', 'quận 3', 'thủ đức', 'bình thạnh'],
        'đà nẵng': ['đà nẵng', 'danang', 'hải châu', 'thanh khê', 'sơn trà', 'ngũ hành sơn'],
        'cần thơ': ['cần thơ', 'cantho', 'ninh kiều', 'bình thủy', 'cái răng'],
        'thái nguyên': ['thái nguyên', 'thainguyen', 'sông công', 'phổ yên'],
    }
    
    address_lower = address.lower()
    
    for city, patterns in city_patterns.items():
        for pattern in patterns:
            if pattern in address_lower:
                return city
    
    return ""

def _check_route_exists(session: Session, origin_city: str, dest_city: str) -> bool:
    return session.query(
        session.query(Trip).filter(
            Trip.origin_city.ilike(f"%{origin_city}%"),
            Trip.destination_city.ilike(f"%{dest_city}%")
        ).exists()
    ).scalar()

def get_available_trips_info(session: Session) -> List[Dict[str, Any]]:
    """
    lấy thông tin các chuyến có sẵn trong database và trả về 
    """
    trips = session.query(Trip.origin_city, Trip.destination_city, Trip.departure_time).distinct().all()
    
    available_trips = {}
    for origin, destination, time in trips:
        route = f"{origin.title()} - {destination.title()}"
        if route not in available_trips:
            available_trips[route] = []
        
        # chỉ thêm thời gian nếu chưa tồn tại
        if time and time.strftime('%H:%M') not in available_trips[route]:
            available_trips[route].append(time.strftime('%H:%M'))

    # format lại cho đẹp
    result = []
    for route, times in available_trips.items():
        result.append(f"{route} lúc {', '.join(sorted(times))}")
        
    return [{
        "status": "NO_ROUTE_FOUND",
        "available_trips": result
    }]


def find_trips(origin: str, destination: str, departure_dt: datetime) -> List[Dict[str, Any]]:
    """
    kiểm tra nếu có đường đi từ origin đến destination không, nếu có trả về ROUTE_EXITST
    """
    SessionLocal = get_session()
    if SessionLocal is None:
        logger.warning("DB session not available.")
        return []

    origin_city = extract_city_from_address(origin)
    dest_city = extract_city_from_address(destination)

    if not origin_city or not dest_city:
        logger.warning(f"Could not extract city from origin='{origin}' or destination='{destination}'")
        return []

    try:
        with SessionLocal() as session:
            logger.debug(f"Checking route existence for: {origin_city} -> {dest_city}")
            if _check_route_exists(session, origin_city, dest_city):
                logger.info(f"Route found for {origin_city} -> {dest_city}")
                return [{
                    "status": "ROUTE_EXISTS",
                    "origin_city": origin_city.title(),
                    "destination_city": dest_city.title(),
                }]
            else:
                logger.info(f"No route found for {origin_city} -> {dest_city}")
                return get_available_trips_info(session)
    except SQLAlchemyError as e:
        logger.error(f"DB error in find_trips: {e}")
        return [] 