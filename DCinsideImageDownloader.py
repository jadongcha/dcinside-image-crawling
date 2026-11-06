import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
import time
import requests
import os
from bs4 import BeautifulSoup
import mimetypes

# 여기에 기존 DCInsideCrawler와 ImageHandler 코드 그대로 넣기
# (생략하지 말고 유지)
# DCInside Crawler 클래스
class DCInsideCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.sent_titles = set()

    def image_check(self, element):
        """이미지 포함 여부 체크"""
        return "icon_pic" in str(element)

    def get_latest_post(self):
        """최신 게시글 정보 가져오기"""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(self.base_url, headers=headers)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')

            posts = soup.select("tr.ub-content")

            if not posts:
                return None

            for post in posts[15:]:
                try:
                    title_element = post.select_one("td.gall_tit > a:first-child")
                    if not title_element:
                        continue

                    link = "https://gall.dcinside.com" + title_element.get("href", "")
                    title = title_element.text.strip()
                    image_insert = self.image_check(post)

                    print(f"{title} {link} {image_insert}")

                    if title not in self.sent_titles:
                        return {
                            'link': link,
                            'title': title,
                            'has_image': image_insert
                        }

                except Exception as e:
                    continue

            return None

        except Exception as e:
            print(f"Error: {e}")
            return None

# 이미지 다운로드 처리 클래스
class ImageHandler:
    def __init__(self):
        if not os.path.exists("Image"):
            os.makedirs("Image")

    def download_image(self, url):
        """이미지 다운로드"""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            headers['Referer'] = url
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')

            # 이미지 링크 찾기
            image_download_contents = soup.select("div.appending_file_box ul li")
            for li in image_download_contents:
                img_tag = li.find('a', href=True)
                img_url = img_tag['href']

                # MIME 타입을 확인하여 확장자 추출
                ext = mimetypes.guess_extension(res.headers['Content-Type'])
                if ext is None:
                    ext = ".jpg"  # 기본 jpg로 설정

                filename = img_url.split("no=")[2] + ext
                path = f"Image/{filename}"

                # 파일 존재 여부 체크 후 저장
                if not os.path.exists(path):
                    img_res = requests.get(img_url, headers=headers)
                    img_res.raise_for_status()
                    with open(path, "wb") as f:
                        f.write(img_res.content)
                    print(f"저장됨: {path}")
                else:
                    print(f"이미지 {filename}이 이미 존재합니다.")
                
                return path

        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

def download_dcinside_images(page_url):
    """페이지에서 이미지를 다운로드하는 함수"""
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(page_url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 첨부 이미지 탐색
    file_list = soup.select("ul.appending_file a")
    if not file_list:
        print("첨부 이미지가 없습니다.")
        return

    os.makedirs("./img_dc", exist_ok=True)

    count = 1
    for a in file_list:
        href = a.get("href")
        if not href:
            continue

        # 절대 URL 보정
        if href.startswith("//"):
            img_url = "https:" + href
        elif href.startswith("/"):
            img_url = "https://gall.dcinside.com/" + href
        else:
            img_url = href

        print("다운로드:", img_url)

        img_res = requests.get(img_url, headers=headers)
        img_res.raise_for_status()

        # Content-Type 확인 (예: image/jpeg, image/png ... )
        content_type = img_res.headers.get("Content-Type", "")

        # MIME → 확장자 자동 변환
        ext = mimetypes.guess_extension(content_type)

        # 일부 사이트는 jpeg을 ".jpe" 로 줄 때가 있으니 보완 처리
        if ext in [".jpe", ".jfif"]:
            ext = ".jpeg"

        # 혹시 못 맞추면 기본 jpg
        if ext is None:
            ext = ".jpg"

        filename = f"image{count}{ext}"
        save_path = os.path.join("./img_dc", filename)

        # 저장
        with open(save_path, "wb") as f:
            f.write(img_res.content)

        print(f"저장됨: {save_path}")
        count += 1

    print("모든 이미지 다운로드 완료!")

crawler = DCInsideCrawler("https://gall.dcinside.com/mgallery/board/lists/?id=projectmx")
latest_post = crawler.get_latest_post()
if latest_post:
    print(f"새로운 게시글: {latest_post['title']} - {latest_post['link']}")
    if latest_post['has_image']:
        image_handler = ImageHandler()
        image_handler.download_image(latest_post['link'])
else:
    print("최신 게시글을 찾을 수 없습니다.")



# GUI 클래스
class DCCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DCInside 이미지 크롤러")
        self.root.geometry("600x400")

        # URL 입력
        tk.Label(root, text="갤러리 URL:").pack(anchor='w', padx=10, pady=5)
        self.url_entry = tk.Entry(root, width=80)
        self.url_entry.pack(padx=10)
        self.url_entry.insert(0, "https://gall.dcinside.com/mgallery/board/lists/?id=projectmx")

        # 시작/중지 버튼
        self.start_button = tk.Button(root, text="크롤링 시작", command=self.start_crawling)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="크롤링 중지", command=self.stop_crawling, state=tk.DISABLED)
        self.stop_button.pack()

        # 로그 출력
        self.log_area = scrolledtext.ScrolledText(root, width=70, height=15)
        self.log_area.pack(padx=10, pady=10)

        self.running = False
        self.crawler_thread = None

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_crawling(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("경고", "URL을 입력해주세요.")
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log("크롤링 시작...")

        # 스레드로 크롤링 실행
        self.crawler_thread = threading.Thread(target=self.crawl_loop, args=(url,), daemon=True)
        self.crawler_thread.start()

    def stop_crawling(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("크롤링 중지됨.")

    def crawl_loop(self, url):
        crawler = DCInsideCrawler(url)
        image_handler = ImageHandler()

        while self.running:
            latest_post = crawler.get_latest_post()
            if latest_post:
                self.log(f"새 게시글: {latest_post['title']} - {latest_post['link']}")
                if latest_post['has_image']:
                    self.log("이미지 다운로드 중...")
                    path = image_handler.download_image(latest_post['link'])
                    if path:
                        self.log(f"이미지 저장됨: {path}")
                    else:
                        self.log("이미지 다운로드 실패")
            else:
                self.log("새 게시글 없음")

            # 30초 간격 체크
            for _ in range(5):
                if not self.running:
                    break
                time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = DCCrawlerGUI(root)
    root.mainloop()
