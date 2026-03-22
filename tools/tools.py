import getpass
import os
import platform
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from io import StringIO

import psutil
import pytz
import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.tools import tool

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows fallback
    winreg = None


def _get_proxies():
    proxies = {
        key: value
        for key, value in {
            "http": os.getenv("HTTP_PROXY", "").strip(),
            "https": os.getenv("HTTPS_PROXY", "").strip(),
        }.items()
        if value
    }
    return proxies or None


def get_desktop_path():
    if winreg is None:
        return os.path.join(os.path.expanduser("~"), "Desktop")

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    )
    desktop = winreg.QueryValueEx(key, "Desktop")[0]
    winreg.CloseKey(key)
    return desktop


@tool
def filesystem(operation: str, path: str, content: str = "") -> str:
    """File operations: read, write, or list files within the current workspace."""
    if not operation or not path:
        return "Error: Missing operation or path"

    if os.path.isabs(path):
        full_path = os.path.abspath(path)
    else:
        full_path = os.path.abspath(os.path.join(os.getcwd(), path))
        real_base = os.path.realpath(os.getcwd())
        real_path = os.path.realpath(full_path)
        if not real_path.startswith(real_base):
            return "Error: Path outside base directory"

    try:
        if operation == "read":
            if not os.path.isfile(full_path):
                return f"Error: File not found - {path}"
            if os.path.getsize(full_path) > 10 * 1024 * 1024:
                return "Error: File too large"
            with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                return file.read()

        if operation == "write":
            parent = os.path.dirname(full_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as file:
                file.write(content)
            return f"File written: {path}"

        if operation == "list":
            target = full_path if os.path.isdir(full_path) else os.path.dirname(full_path)
            if not os.path.isdir(target):
                return f"Error: Not a directory - {path}"
            return "\n".join(os.listdir(target))

        return f"Error: Unknown operation '{operation}'"
    except Exception as error:
        return f"Error: {type(error).__name__}: {error}"


@tool
def get_system_info(info: str) -> str:
    """Get system information such as desktop path, username, memory, and disk usage."""
    if info == "desktop_path":
        return get_desktop_path()
    if info == "username":
        return getpass.getuser()
    if info == "os_info":
        return f"{platform.system()} {platform.release()} ({platform.machine()})"
    if info == "cpu_count":
        return f"{psutil.cpu_count()} CPUs"
    if info == "memory_info":
        mem = psutil.virtual_memory()
        return f"Total: {mem.total // (1024**3)}GB, Available: {mem.available // (1024**3)}GB"
    if info == "disk_usage":
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        return f"Total: {disk.total // (1024**3)}GB, Used: {disk.used // (1024**3)}GB, Free: {disk.free // (1024**3)}GB"
    if info == "current_dir":
        return os.getcwd()
    return "Available: desktop_path, username, os_info, cpu_count, memory_info, disk_usage, current_dir"


@tool
def get_current_time(time_zone: str) -> str:
    """Get current date and time in the specified timezone."""
    try:
        tz = pytz.timezone(time_zone)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S")
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Error: Unknown timezone '{time_zone}'"


@tool
def search(query: str):
    """Search the web. The query must be in English."""
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        response = requests.get(url, headers=headers, proxies=_get_proxies(), timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for item in soup.select("div.result")[:20]:
            title_tag = item.select_one("a.result__a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            url_tag = item.select_one("a.result__url")
            link = url_tag.get("href", "") if url_tag else title_tag.get("href", "")
            if "/l/?uddg=" in link:
                from urllib.parse import unquote

                link = unquote(link.split("uddg=")[-1].split("&")[0])
            snippet_tag = item.select_one("div.result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            results.append({"title": title, "url": link, "snippet": snippet})
        if not results:
            return "No search results found."
        output = [
            f"{index}. {item['title']}\n   URL: {item['url']}\n   {item['snippet']}\n"
            for index, item in enumerate(results, 1)
        ]
        return "\n".join(output)
    except Exception as error:
        return f"Error: {error}"


@tool
def navigate_to_url(url: str) -> str:
    """Navigate to a URL and return page content (first 5000 characters)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, timeout=30, headers=headers, proxies=_get_proxies())
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        clean_text = "\n".join(line for line in lines if line)
        if len(clean_text) > 5000:
            clean_text = clean_text[:5000] + "\n...(content truncated)"
        return clean_text
    except Exception as error:
        return f"Error: {error}"


@tool
def download_file(url: str, filename: str = None, directory: str = None) -> str:
    """Download a file from a URL and ingest it into the documents vector store."""
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    if not filename:
        filename = url.split("/")[-1].split("?")[0] or "downloaded_file"

    save_dir = directory if directory else "./chroma_db/documents"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    try:
        with requests.get(url, stream=True, timeout=(10, 30), proxies=_get_proxies()) as response:
            response.raise_for_status()
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            size_mb = os.path.getsize(save_path) / 1024 / 1024
            from rag import ingest_downloaded_doc

            ingest_result = ingest_downloaded_doc(save_path)
            return (
                f"Download successful!\nSaved location: {save_path}\n"
                f"File size: {size_mb:.2f} MB\n{ingest_result}"
            )
        return "Error: File downloaded but size is 0, possibly empty content"

    except requests.exceptions.HTTPError as error:
        return f"Error: HTTP error - {error.response.status_code} {error.response.reason}"
    except requests.exceptions.ConnectionError:
        return "Error: Connection failed - please check network connection or URL"
    except requests.exceptions.Timeout:
        return "Error: Download timeout (no response after 30 seconds)"
    except requests.exceptions.RequestException as error:
        return f"Error: Network request failed - {error}"
    except OSError as error:
        return f"Error: File write failed (permission/path/disk problem) - {error}"
    except Exception as error:
        return f"Error: {type(error).__name__} - {error}"


@tool
def run_python_code(code: str) -> str:
    """Execute Python code with restricted builtins and return stdout or stderr."""
    import builtins
    import traceback

    stdout = StringIO()
    stderr = StringIO()

    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            safe_builtins = {
                name: getattr(builtins, name)
                for name in dir(builtins)
                if name
                not in {
                    "eval",
                    "exec",
                    "compile",
                    "__import__",
                    "open",
                    "input",
                    "getattr",
                    "setattr",
                    "delattr",
                    "globals",
                    "locals",
                }
            }

            exec(code, {"__builtins__": safe_builtins})
            output = stdout.getvalue().rstrip()
            error_output = stderr.getvalue().rstrip()

            if error_output:
                return f"stderr:\n{error_output}"
            if output:
                return output
            return "ok (no output)"
        except Exception:
            return "Error:\n" + traceback.format_exc().strip()


@tool
def load_pdf(pdf_path: str, page_range: str = None) -> str:
    """Load a PDF file and return its text content."""
    if not os.path.exists(pdf_path):
        return f"Error: PDF file not found - {pdf_path}"

    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    if page_range:
        start, end = map(int, page_range.split("-"))
        return "\n".join(page.page_content for page in pages[start - 1 : end])
    return "\n".join(page.page_content for page in pages)


@tool
def list_knowledge_base() -> str:
    """List all PDFs in the project knowledge base."""
    base_dir = "./chroma_db/documents"
    if not os.path.isdir(base_dir):
        return "Knowledge base directory does not exist."
    return "\n".join(
        file_name for file_name in os.listdir(base_dir) if file_name.endswith(".pdf")
    )


from tools.mail_tools import send_email

tools = [
    filesystem,
    get_system_info,
    get_current_time,
    search,
    navigate_to_url,
    download_file,
    run_python_code,
    load_pdf,
    send_email,
    list_knowledge_base,
]
