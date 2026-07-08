# crawler_carvertical.py - کرالر اختصاصی برای سایت carvertical.com
import chromadb
from sentence_transformers import SentenceTransformer
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import hashlib
import os
import shutil

# ========== تنظیمات ==========
LOCAL_MODEL_PATH = r"C:\Users\arezo\OneDrive\Desktop\website_crawling\models\all-MiniLM-L6-v2"
DB_PATH = "./data/carvertical_database"

# ========== کلاس کرالر ==========
class CarVerticalCrawler:
    def __init__(self, db_path):
        self.db_path = db_path
        self.visited_urls = set()
        self.page_count = 0
        self.total_chunks = 0
        self.crawled_pages = []
        
        print("=" * 70)
        print("🕷️ کرالر اختصاصی carvertical.com")
        print("=" * 70)
        
        # بارگذاری مدل embedding
        print("📂 بارگذاری مدل embedding...")
        if os.path.exists(LOCAL_MODEL_PATH):
            self.embedding_model = SentenceTransformer(LOCAL_MODEL_PATH, device='cpu')
            print("✅ مدل embedding از مسیر محلی بارگذاری شد.")
        else:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ مدل embedding دانلود و بارگذاری شد.")
        
        # آماده‌سازی دیتابیس
        os.makedirs(db_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        # حذف collection قبلی
        try:
            self.chroma_client.delete_collection("carvertical_content")
            print("🔄 Collection قبلی حذف شد.")
        except:
            pass
        
        # ایجاد collection جدید
        self.collection = self.chroma_client.create_collection("carvertical_content")
        print("✅ دیتابیس جدید ایجاد شد.")
        print("-" * 70)
    
    def extract_text(self, html):
        """استخراج متن تمیز از HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # حذف تگ‌های غیرمحتوایی
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "meta"]):
            tag.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        
        # حذف فاصله‌های اضافی
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def extract_links(self, html, base_url):
        """استخراج لینک‌های داخلی"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        base_domain = urlparse(base_url).netloc
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # فقط لینک‌های همان دامنه
            if parsed.netloc == base_domain and parsed.scheme in ['http', 'https']:
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if clean_url and len(clean_url) > 10 and '#' not in clean_url:
                    links.add(clean_url)
        
        return links
    
    def split_text(self, text, chunk_size=600, overlap=150):
        """تقسیم متن به تکه‌های همپوشان"""
        words = text.split()
        
        if len(words) <= chunk_size:
            return [text]
        
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk) > 50:
                chunks.append(chunk)
        
        return chunks
    
    def save_chunks(self, text, source_url, title=""):
        """ذخیره تکه‌ها در دیتابیس (بدون ترجمه چون سایت انگلیسی است)"""
        chunks = self.split_text(text)
        saved_count = 0
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 100:
                continue
            
            # تولید شناسه یکتا
            chunk_id = hashlib.md5(f"{source_url}_{i}_{chunk[:50]}".encode()).hexdigest()
            
            # ذخیره مستقیم (بدون ترجمه)
            self.collection.upsert(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[{
                    "source": source_url,
                    "title": title[:100],
                    "chunk_index": i,
                    "length": len(chunk)
                }]
            )
            saved_count += 1
        
        return saved_count
    
    def crawl(self, start_url, max_pages=80, max_depth=4):
        """اجرای خزش کامل وب‌سایت"""
        to_visit = [(start_url, 0)]  # (url, depth)
        
        print(f"\n🚀 شروع خزش: {start_url}")
        print(f"📊 حداکثر صفحات: {max_pages}, عمق خزش: {max_depth}")
        print("-" * 70)
        
        while to_visit and self.page_count < max_pages:
            url, depth = to_visit.pop(0)
            
            if url in self.visited_urls or depth > max_depth:
                continue
            
            print(f"\n📥 [{self.page_count + 1}/{max_pages}] خزش عمق {depth}: {url[:80]}...")
            
            try:
                # دریافت صفحه
                response = requests.get(url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                # استخراج عنوان
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else "No Title"
                title = title[:80] if title else "No Title"
                
                # استخراج متن
                text = self.extract_text(response.text)
                
                if text and len(text) > 200:
                    chunks_count = self.save_chunks(text, url, title)
                    self.page_count += 1
                    self.total_chunks += chunks_count
                    self.crawled_pages.append({
                        "url": url,
                        "title": title,
                        "chunks": chunks_count,
                        "length": len(text),
                        "depth": depth
                    })
                    
                    print(f"   ✅ صفحه {self.page_count}: {title[:50]}...")
                    print(f"      📄 طول متن: {len(text)} کاراکتر → 🧩 {chunks_count} تکه")
                else:
                    print(f"   ⚠️ محتوای کافی ندارد (طول: {len(text) if text else 0})")
                
                # پیدا کردن لینک‌های جدید
                if depth < max_depth:
                    new_links = self.extract_links(response.text, url)
                    new_count = 0
                    for link in new_links:
                        if link not in self.visited_urls:
                            to_visit.append((link, depth + 1))
                            new_count += 1
                    if new_count > 0:
                        print(f"   🔗 {new_count} لینک جدید (از {len(new_links)} لینک کل) اضافه شد به صف")
                
                self.visited_urls.add(url)
                time.sleep(0.8)  # احترام به وب‌سایت
                
            except requests.exceptions.Timeout:
                print(f"   ❌ زمان دریافت تمام شد")
                self.visited_urls.add(url)
            except requests.exceptions.RequestException as e:
                print(f"   ❌ خطا در درخواست: {str(e)[:50]}")
                self.visited_urls.add(url)
            except Exception as e:
                print(f"   ❌ خطا: {str(e)[:50]}")
                self.visited_urls.add(url)
        
        # نمایش نتیجه نهایی
        print("\n" + "=" * 70)
        print("🎉 خزش کامل شد!")
        print("=" * 70)
        print(f"   📄 صفحات کرال شده: {self.page_count}")
        print(f"   🧩 تکه‌های ذخیره شده: {self.total_chunks}")
        print(f"   🔗 URLهای دیده شده: {len(self.visited_urls)}")
        print(f"   💾 دیتابیس در مسیر: {self.db_path}")
        print("=" * 70)
        
        # نمایش لیست صفحات
        if self.crawled_pages:
            print("\n📋 لیست صفحات کرال شده:")
            for i, page in enumerate(self.crawled_pages, 1):
                print(f"   {i}. [{page['depth']}] {page['title'][:60]}...")
        
        return self.page_count, self.total_chunks

# ========== اجرای کرالر ==========
if __name__ == "__main__":
    import time
    
    # تنظیمات خزش
    START_URL = "https://carvertical.com"
    MAX_PAGES = 80
    MAX_DEPTH = 4
    
    # حذف دیتابیس قبلی برای شروع تازه
    if os.path.exists(DB_PATH):
        print("🗑️ حذف دیتابیس قبلی...")
        shutil.rmtree(DB_PATH, ignore_errors=True)
        time.sleep(0.5)
    
    # اجرای کرالر
    crawler = CarVerticalCrawler(DB_PATH)
    page_count, total_chunks = crawler.crawl(START_URL, MAX_PAGES, MAX_DEPTH)
    
    print("\n" + "=" * 70)
    print("✅ کرال با موفقیت انجام شد!")
    print("=" * 70)
    print("\n💡 مرحله بعد:")
    print("   1. LM Studio را باز کنید و مدل Gemma را Load کنید")
    print("   2. سرور LM Studio را استارت کنید (پورت 1234)")
    print("   3. فایل app_chat_carvertical.py را اجرا کنید:")
    print("      streamlit run app_chat_carvertical.py")