from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import json
import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Import security modules
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.security.dependencies import verify_api_key_header
from app.utils.validation import validate_url, sanitize_input
from app.config import settings

# Đường dẫn đến thư mục mycrawler
BASE_DIR = Path(__file__).parent
MYCRAWLER_DIR = BASE_DIR / "mycrawler"

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Scheduler instance
scheduler = None

# Mapping từ spider name sang source type
SPIDER_TO_SOURCE = {
    "openai-com-listing": "openai.com",
    "techcrunch-listing": "techcrunch.com",
    "anthropic-listing": "anthropic.com",
    "adobe-com-listing": "adobe.com"
}

# Danh sách tất cả listing spiders
ALL_LISTING_SPIDERS = list(SPIDER_TO_SOURCE.keys())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler cho startup và shutdown"""
    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title="Crawler API",
    description="API để crawl và lấy dữ liệu từ các nguồn (OpenAI, TechCrunch, Anthropic, Adobe)",
    lifespan=lifespan
)

# Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Thêm Security Headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Thêm Rate Limiting middleware
app.add_middleware(RateLimitMiddleware)


class CrawlDetailRequest(BaseModel):
    type: str
    url: str


def get_listing_log_path() -> Path:
    """Trả về đường dẫn đến log file"""
    return BASE_DIR / "mycrawler" / "data" / "listing_scheduler_log.json"


def load_listing_log() -> dict:
    """Đọc log file, khởi tạo nếu chưa có"""
    log_path = get_listing_log_path()
    
    # Tạo thư mục nếu chưa có
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Nếu file chưa tồn tại, khởi tạo với thời gian hiện tại
    if not log_path.exists():
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_log = {spider: current_time for spider in ALL_LISTING_SPIDERS}
        save_listing_log(initial_log)
        logger.info(f"Khởi tạo log file mới với thời gian: {current_time}")
        return initial_log
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        # Kiểm tra xem có đủ tất cả spiders không
        missing_spiders = set(ALL_LISTING_SPIDERS) - set(log_data.keys())
        if missing_spiders:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for spider in missing_spiders:
                log_data[spider] = current_time
            save_listing_log(log_data)
            logger.info(f"Thêm các spiders còn thiếu vào log: {missing_spiders}")
        
        return log_data
    except json.JSONDecodeError as e:
        logger.error(f"Log file bị corrupt, khởi tạo lại: {e}")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_log = {spider: current_time for spider in ALL_LISTING_SPIDERS}
        save_listing_log(initial_log)
        return initial_log
    except Exception as e:
        logger.error(f"Lỗi đọc log file: {e}")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_log = {spider: current_time for spider in ALL_LISTING_SPIDERS}
        save_listing_log(initial_log)
        return initial_log


def save_listing_log(log_data: dict) -> None:
    """Lưu log file"""
    log_path = get_listing_log_path()
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Đã lưu log file: {log_path}")
    except Exception as e:
        logger.error(f"Lỗi lưu log file: {e}")
        raise


def get_source_config(source_type: str) -> dict:
    """Lấy cấu hình cho source type"""
    configs = {
        "openai.com": {
            "data_dir": "OpenAI",
            "listing_file": "openai-com-listing.json",
            "detail_file": "openai-com-detail.json",
            "listing_spider": "openai-com-listing",
            "detail_spider": "openai-com-detail"
        },
        "techcrunch.com": {
            "data_dir": "TechCrunch",
            "listing_file": "techcrunch-listing.json",
            "detail_file": "techcrunch-detail.json",
            "listing_spider": "techcrunch-listing",
            "detail_spider": "techcrunch-detail"
        },
        "anthropic.com": {
            "data_dir": "Anthropic",
            "listing_file": "anthropic-listing.json",
            "detail_file": "anthropic-detail.json",
            "listing_spider": "anthropic-listing",
            "detail_spider": "anthropic-detail"
        },
        "adobe.com": {
            "data_dir": "Adobe",
            "listing_file": "adobe-com-listing.json",
            "detail_file": "adobe-com-detail.json",
            "listing_spider": "adobe-com-listing",
            "detail_spider": "adobe-com-detail"
        }
    }
    return configs.get(source_type)


def get_next_listing_to_run() -> Optional[str]:
    """Tìm listing có thời gian chạy cũ nhất từ log file"""
    try:
        log_data = load_listing_log()
        
        if not log_data:
            logger.warning("Log file trống, không có listing nào để chạy")
            return None
        
        # Tìm listing có timestamp cũ nhất
        oldest_spider = None
        oldest_time = None
        
        for spider, time_str in log_data.items():
            if spider not in ALL_LISTING_SPIDERS:
                continue
            
            try:
                time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                if oldest_time is None or time_obj < oldest_time:
                    oldest_time = time_obj
                    oldest_spider = spider
            except ValueError as e:
                logger.warning(f"Không thể parse timestamp cho {spider}: {time_str}, {e}")
                # Nếu không parse được, coi như listing này cần chạy ngay
                if oldest_spider is None:
                    oldest_spider = spider
        
        if oldest_spider:
            logger.info(f"Listing được chọn để chạy: {oldest_spider} (thời gian chạy cuối: {log_data.get(oldest_spider, 'N/A')})")
            return oldest_spider
        
        return None
    except Exception as e:
        logger.error(f"Lỗi khi tìm listing cũ nhất: {e}")
        return None


def find_json_file(filename: str, source_type: str = None) -> Optional[Path]:
    """Tìm file JSON trong các thư mục có thể có"""
    # Nếu có source_type, tìm trong thư mục cụ thể của source
    if source_type:
        config = get_source_config(source_type)
        if config:
            data_dir = config["data_dir"]
            possible_paths = [
                BASE_DIR / "mycrawler" / "data" / data_dir / filename,
                BASE_DIR / "mycrawler" / "mycrawler" / "data" / data_dir / filename,
                BASE_DIR / "mycrawler" / "mycrawler" / "mycrawler" / "data" / data_dir / filename,
            ]
            
            for path in possible_paths:
                if path.exists():
                    return path
    
    # Tìm đệ quy trong thư mục mycrawler nếu không tìm thấy ở các đường dẫn trên
    mycrawler_path = BASE_DIR / "mycrawler"
    if mycrawler_path.exists():
        for root, dirs, files in os.walk(mycrawler_path):
            if filename in files:
                found_path = Path(root) / filename
                if found_path.exists():
                    return found_path
    
    return None


async def run_listing_spider(spider_name: str) -> dict:
    """
    Chạy listing spider với timeout 15 phút, force kill nếu quá timeout
    
    Args:
        spider_name: Tên spider (ví dụ: 'openai-com-listing')
    
    Returns:
        dict: Kết quả chạy spider {'success': bool, 'message': str}
    """
    # Lấy source_type từ spider_name
    source_type = SPIDER_TO_SOURCE.get(spider_name)
    if not source_type:
        error_msg = f"Không tìm thấy source_type cho spider: {spider_name}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}
    
    config = get_source_config(source_type)
    if not config:
        error_msg = f"Không tìm thấy config cho source_type: {source_type}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}
    
    listing_spider = config["listing_spider"]
    
    logger.info(f"Bắt đầu chạy listing spider: {listing_spider} (source: {source_type})")
    
    try:
        # Chạy scrapy command bằng subprocess
        cmd = [
            sys.executable,
            "-m",
            "scrapy",
            "crawl",
            listing_spider
        ]
        
        # Chạy trong thư mục mycrawler
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(MYCRAWLER_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Đợi spider hoàn thành với timeout 15 phút (900 giây)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=900)
        except asyncio.TimeoutError:
            logger.warning(f"Spider {listing_spider} chạy quá 15 phút, force kill")
            process.kill()
            # Đợi process bị kill xong
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                logger.error(f"Không thể kill process {listing_spider}")
            
            error_msg = f"Timeout: Spider {listing_spider} chạy quá 15 phút, đã force kill"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
            logger.error(f"Spider {listing_spider} chạy thất bại (returncode: {process.returncode}): {error_msg}")
            return {"success": False, "message": f"Spider chạy thất bại: {error_msg}"}
        
        # Đợi một chút để đảm bảo file được ghi
        await asyncio.sleep(2)
        
        logger.info(f"Spider {listing_spider} chạy thành công")
        return {"success": True, "message": f"Spider {listing_spider} chạy thành công"}
        
    except Exception as e:
        error_msg = f"Lỗi khi chạy spider {listing_spider}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "message": error_msg}


def run_async_in_sync(coro):
    """
    Chạy async function từ sync context một cách an toàn
    BackgroundScheduler chạy trong thread riêng nên không có event loop
    """
    try:
        # Thử lấy event loop đang chạy
        loop = asyncio.get_running_loop()
        # Nếu có loop đang chạy, tạo event loop mới trong thread riêng
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # Không có event loop đang chạy, tạo mới (trường hợp phổ biến trong scheduler)
        return asyncio.run(coro)


def check_and_run_listing():
    """
    Check log file, tìm listing cũ nhất, chạy spider và cập nhật log
    Hàm này được gọi bởi scheduler mỗi 1 giờ
    """
    logger.info("=== Bắt đầu check listing scheduler ===")
    
    try:
        # Tìm listing cũ nhất
        spider_name = get_next_listing_to_run()
        
        if not spider_name:
            logger.warning("Không tìm thấy listing nào để chạy")
            return
        
        # Chạy spider (sử dụng helper function để chạy async function từ sync context)
        result = run_async_in_sync(run_listing_spider(spider_name))
        
        if result["success"]:
            # Cập nhật log file với thời gian hiện tại
            log_data = load_listing_log()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_data[spider_name] = current_time
            save_listing_log(log_data)
            logger.info(f"Đã cập nhật log cho {spider_name}: {current_time}")
        else:
            # Không cập nhật log nếu spider fail, lần check sau sẽ chọn lại nếu vẫn cũ nhất
            logger.warning(f"Spider {spider_name} chạy thất bại, không cập nhật log: {result['message']}")
        
        logger.info("=== Kết thúc check listing scheduler ===")
        
    except Exception as e:
        logger.error(f"Lỗi trong check_and_run_listing: {e}", exc_info=True)


@app.get("/api/listings")
async def get_listings(type: str = Query(..., description="Loại source (ví dụ: openai.com, techcrunch.com, anthropic.com)")):
    """
    Lấy danh sách listings từ file JSON
    Query params:
    - type: Loại source (ví dụ: 'openai.com', 'techcrunch.com', 'anthropic.com', 'adobe.com')
    """
    config = get_source_config(type)
    if not config:
        supported_types = ", ".join(["'openai.com'", "'techcrunch.com'", "'anthropic.com'", "'adobe.com'"])
        raise HTTPException(status_code=400, detail=f"Type '{type}' không được hỗ trợ. Chỉ hỗ trợ: {supported_types}")
    
    json_file = find_json_file(config["listing_file"], type)
    
    if not json_file:
        raise HTTPException(status_code=404, detail="File listing không tồn tại. Vui lòng chạy listing spider trước.")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return JSONResponse(content={
            "success": True,
            "type": type,
            "count": len(data),
            "data": data
        })
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Lỗi đọc file JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@app.post("/api/crawl-detail")
async def crawl_detail(
    request: CrawlDetailRequest,
    api_key_verified: bool = Depends(verify_api_key_header)
):
    """
    Chạy spider để crawl detail page và trả về kết quả
    Body:
    - type: Loại source (ví dụ: 'openai.com', 'techcrunch.com', 'anthropic.com', 'adobe.com')
    - url: URL của detail page cần crawl
    
    Yêu cầu: API key trong header X-API-Key
    """
    # Sanitize input
    request.type = sanitize_input(request.type, max_length=50)
    request.url = sanitize_input(request.url, max_length=2048)
    
    config = get_source_config(request.type)
    if not config:
        supported_types = ", ".join(["'openai.com'", "'techcrunch.com'", "'anthropic.com'", "'adobe.com'"])
        raise HTTPException(status_code=400, detail=f"Type '{request.type}' không được hỗ trợ. Chỉ hỗ trợ: {supported_types}")
    
    # Validate URL với validation function mới
    is_valid, error_msg = validate_url(request.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"URL không hợp lệ: {error_msg}")
    
    try:
        # Chạy scrapy command bằng subprocess
        cmd = [
            sys.executable,
            "-m",
            "scrapy",
            "crawl",
            config["detail_spider"],
            "-a",
            f"start_url={request.url}"
        ]
        
        # Chạy trong thư mục mycrawler
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(MYCRAWLER_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Đợi spider hoàn thành (timeout 120 giây)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
        except asyncio.TimeoutError:
            process.kill()
            raise HTTPException(status_code=408, detail="Timeout: Spider chạy quá lâu (quá 120 giây)")
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
            raise HTTPException(status_code=500, detail=f"Lỗi crawl: {error_msg}")
        
        # Đợi một chút để đảm bảo file được ghi
        await asyncio.sleep(2)
        
        # Đọc kết quả từ file JSON
        json_file = find_json_file(config["detail_file"], request.type)
        
        if not json_file:
            raise HTTPException(status_code=500, detail="Không tìm thấy file output sau khi crawl")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return JSONResponse(content={
            "success": True,
            "type": request.type,
            "url": request.url,
            "count": len(data) if data else 0,
            "data": data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi crawl: {str(e)}")


@app.get("/api/test-scheduler")
async def test_scheduler(api_key_verified: bool = Depends(verify_api_key_header)):
    """
    Test scheduler thủ công - chạy check_and_run_listing ngay lập tức
    Endpoint này dùng để test scheduler mà không cần đợi đến giờ
    
    Yêu cầu: API key trong header X-API-Key
    """
    try:
        logger.info("=== Test scheduler thủ công ===")
        check_and_run_listing()
        return JSONResponse(content={
            "success": True,
            "message": "Scheduler test đã chạy thành công"
        })
    except Exception as e:
        logger.error(f"Lỗi khi test scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi test scheduler: {str(e)}")


@app.get("/api/scheduler-status")
async def get_scheduler_status(api_key_verified: bool = Depends(verify_api_key_header)):
    """
    Lấy trạng thái scheduler và log file
    
    Yêu cầu: API key trong header X-API-Key
    """
    try:
        log_data = load_listing_log()
        scheduler_status = {
            "running": scheduler is not None and scheduler.running if scheduler else False,
            "jobs": []
        }
        
        if scheduler and scheduler.running:
            for job in scheduler.get_jobs():
                scheduler_status["jobs"].append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None
                })
        
        return JSONResponse(content={
            "success": True,
            "scheduler": scheduler_status,
            "log_data": log_data,
            "next_listing": get_next_listing_to_run()
        })
    except Exception as e:
        logger.error(f"Lỗi khi lấy scheduler status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@app.get("/")
async def root():
    return {
        "message": "Crawler API",
        "endpoints": {
            "GET /api/listings?type={source}": "Lấy danh sách listings (source: openai.com, techcrunch.com, anthropic.com, adobe.com)",
            "POST /api/crawl-detail": "Crawl detail page (body: {type: 'openai.com'|'techcrunch.com'|'anthropic.com'|'adobe.com', url: '...'})",
            "GET /api/test-scheduler": "Test scheduler thủ công (chạy check_and_run_listing ngay)",
            "GET /api/scheduler-status": "Lấy trạng thái scheduler và log file"
        },
        "supported_sources": ["openai.com", "techcrunch.com", "anthropic.com", "adobe.com"]
    }


def start_scheduler():
    """Khởi tạo và cấu hình scheduler với cron job mỗi 1 giờ"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.warning("Scheduler đã đang chạy")
        return
    
    scheduler = BackgroundScheduler()
    
    # Cấu hình cron job chạy mỗi 1 giờ (phút 0 của mỗi giờ)
    scheduler.add_job(
        check_and_run_listing,
        trigger=CronTrigger(minute=0),  # Chạy vào phút 0 của mỗi giờ
        id='check_listing_job',
        name='Check và chạy listing spider',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler đã được khởi động - sẽ chạy mỗi 1 giờ (phút 0)")


def shutdown_scheduler():
    """Cleanup scheduler khi app shutdown"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.info("Đang dừng scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler đã được dừng")


if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Kiểm tra port 8000 có đang được sử dụng không
    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return False
            except OSError:
                return True
    
    # Nếu port 8000 đang được sử dụng, thử port 8001
    port = 8000
    if is_port_in_use(port):
        logger.warning(f"Port {port} đang được sử dụng, thử port {port + 1}")
        port = 8001
    
    uvicorn.run(app, host="0.0.0.0", port=port)

