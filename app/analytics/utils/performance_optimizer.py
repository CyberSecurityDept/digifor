#!/usr/bin/env python3
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from pathlib import Path
import logging, asyncio, gzip, json, warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def compress_response(self, data: Dict[str, Any]) -> bytes:
        try:
            json_str = json.dumps(data, default=str)
            compressed = gzip.compress(json_str.encode('utf-8'))
            logger.info(f"Response compressed: {len(json_str)} -> {len(compressed)} bytes ({len(compressed)/len(json_str)*100:.1f}% reduction)")
            return compressed
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return json.dumps(data, default=str).encode('utf-8')
    
    def paginate_data(self, data: List[Dict], page_size: int = 1000) -> List[List[Dict]]:
        pages = []
        for i in range(0, len(data), page_size):
            pages.append(data[i:i + page_size])
        return pages
    
    def optimize_excel_reading(self, file_path: Path, chunk_size: int = 10000) -> List[pd.DataFrame]:
        try:
            chunks = []
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                chunk_iter = pd.read_excel(file_path, sheet_name=sheet_name, chunksize=chunk_size, engine='openpyxl')
                for chunk in chunk_iter:
                    chunks.append(chunk)
            
            logger.info(f"Excel file read in {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Chunked Excel reading failed: {e}")
            return [pd.read_excel(file_path, engine='openpyxl')]
    
    async def process_chunks_async(self, chunks: List[pd.DataFrame], processor_func) -> List[Any]:
        try:
            loop = asyncio.get_event_loop()
            tasks = []
            
            for chunk in chunks:
                task = loop.run_in_executor(self.executor, processor_func, chunk)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            logger.info(f"Processed {len(chunks)} chunks asynchronously")
            return results
        except Exception as e:
            logger.error(f"Async chunk processing failed: {e}")
            return []
    
    def batch_database_operations(self, data: List[Dict], batch_size: int = 1000) -> List[List[Dict]]:
        batches = []
        for i in range(0, len(data), batch_size):
            batches.append(data[i:i + batch_size])
        return batches
    
    def create_summary_response(self, total_records: int, file_size: int, processing_time: float) -> Dict[str, Any]:
        return {
            "status": 200,
            "message": "File uploaded and processed successfully",
            "summary": {
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "total_records": total_records,
                "processing_time_seconds": round(processing_time, 2),
                "records_per_second": round(total_records / processing_time, 2),
                "data_available": True
            },
            "data": {
                "file_id": None,
                "device_id": None,
                "parsing_complete": True
            }
        }
    
    def optimize_memory_usage(self, data: List[Dict]) -> List[Dict]:
        optimized = []
        for item in data:
            optimized_item = {
                "display_name": item.get("display_name"),
                "phone_number": item.get("phone_number"),
                "type": item.get("type"),
                "last_time_contacted": item.get("last_time_contacted")
            }
            optimized.append(optimized_item)
        return optimized
    
    def __del__(self):
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

performance_optimizer = PerformanceOptimizer()
