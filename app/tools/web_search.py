"""
Module: web_search.py
Vai trò: Công cụ tìm kiếm thông tin mở rộng trên Web (Web Search Tool).

Mô tả chi tiết:
- Tích hợp công cụ tìm kiếm Tavily Search API để thu thập dữ liệu ngoài luồng từ Internet.
- Phục vụ tra cứu thông tin nền tảng về đối tác, doanh nghiệp, thuật ngữ chuyên ngành hoặc kiểm chứng dữ kiện thực tế.
- Trả về kết quả có cấu trúc gồm tiêu đề (`title`), liên kết (`url`) và đoạn trích tóm tắt (`snippet`).
"""

from app.core.config import settings
from app.core.exceptions import ToolExecutionError

def web_search(query: str, max_results: int | None = None) -> dict:
    limit = max_results or settings.search_max_results
    try:
        from tavily import TavilyClient
        tavily_client = TavilyClient(api_key=settings.search_api_key)
        response = tavily_client.search(query=query, max_results=limit)
        results = [
            {
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "snippet": row.get("content", ""),
            }
            for row in response.get("results", [])
        ]
        return {
            "query": query,
            "results": results,
        }
    except Exception as exc:
        raise ToolExecutionError(f"Web search failed: {exc}") from exc

if __name__ == "__main__":
    import json
    search_result=web_search("ai là vị lãnh tụ vĩ đại của Việt Nam", max_results=3)
    print(json.dumps(search_result, indent=4, ensure_ascii=False))