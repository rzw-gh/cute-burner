import os
import re
import requests
from tqdm import tqdm
from core.utils import Utils
from urllib.parse import urlparse, urljoin, parse_qsl
import libtorrent as lt
import time
import sys


class Downloader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, download_link, download_path="assets/media"):
        self.utils = Utils()
        self.download_path = download_path
        self.utils.check_folder(download_path)
        self.download_link = download_link
        self.canceled = False

    def download(self):
        if self.download_link.startswith("magnet:"):
            return self.download_torrent()
        else:
            return self.download_url()

    @staticmethod
    def check_login_required(response):
        if response.status_code == 401 or response.status_code == 403:
            return True

        content_type = response.headers.get('Content-Type', '').lower()

        if 'html' in content_type or 'text' in content_type:
            content = response.content.decode('utf-8', errors='ignore')
            if 'login' in content.lower() or 'sign' in content.lower():
                return True

        return False

    def parse_link(self, link):
        parsed_url = urlparse(link)
        if parsed_url.scheme == 'mrl':
            self.download_link = f"{parsed_url.netloc}{parsed_url.path}"
            params = dict(parse_qsl(parsed_url.query))
            return True, params
        else:
            if not parsed_url.scheme:
                self.download_link = urljoin('https://', link)
            else:
                self.download_link = link
            return False, {}

    def download_url(self):
        is_mrl, params = self.parse_link(self.download_link)

        response = requests.get(self.download_link, stream=True, params=params)

        if self.check_login_required(response):
            raise ValueError("Login required to download the file.")

        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            filename = re.findall(r'filename=(.+)', content_disposition)
            if len(filename) > 0:
                filename = filename[0].strip('"')
            else:
                filename = "unknown"
        else:
            filename = urlparse(response.url).path.split('/')[-1]
        filename = self.utils.append_prefix(filename, self.download_path)
        self.utils.validate_file(filename, True)

        progress_bar = tqdm(
            total=int(response.headers.get('content-length', 0)),
            initial=0 if not os.path.exists(filename) else os.path.getsize(filename),
            unit='B', unit_scale=True, desc=f"Downloading {filename}",
            bar_format='{desc} {percentage:3.0f}% |{rate_fmt}{postfix}'
        )

        with open(filename, 'wb' if not os.path.exists(filename) else 'ab') as file, progress_bar as pbar:
            for data in response.iter_content(chunk_size=1024):
                if self.canceled:
                    pbar.close()
                    self.utils.validate_file(filename, True)
                    return
                file.write(data)
                pbar.update(len(data))
            return [filename]

    def download_torrent(self):
        ses = lt.session()
        ses.listen_on(6881, 6891)

        params = {
            'save_path': self.download_path,
        }
        handle = lt.add_magnet_uri(ses, self.download_link, params)

        while not handle.has_metadata():
            time.sleep(1)

        while handle.status().state != lt.torrent_status.seeding:
            if self.canceled:
                ses.pause()
                return
            s = handle.status()
            print(f"\r{int(s.progress * 100)}% complete | {s.download_rate / (1024 * 1024):.1f} kB/s", end='')
            sys.stdout.flush()
            time.sleep(1)

        return self.list_files_in_directory()

    def cancel(self):
        self.canceled = True

    def list_files_in_directory(self):
        file_list = []

        for file in os.listdir(self.download_path):
            path = os.path.join(self.download_path, file)
            file_list.append(os.path.basename(path))
        return file_list
