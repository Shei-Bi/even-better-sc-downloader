from .item_chain import ItemChain, Item
from threading import Thread
import os
import posixpath
import requests
from hashlib import sha1
from sc_compression import decompress as decompress_data

class DownloaderWorker(Thread):
    def __init__(
        self,
        content_hash: str,
        assets_urls: list[str],
        assets_path: str,
        assets_basepath: str,
        folder: ItemChain,
    ) -> None:
        Thread.__init__(self)
        self.is_working = True
        self.assets_basepath = assets_basepath
        self.assets_path = assets_path
        self.folder = folder
        self.content_hash = content_hash
        self.assets_urls = assets_urls
    
    @staticmethod
    def download_file(urls: list[str], conent_hash: str, filepath: str) -> bytes or int:
        request: requests.Response = None
        for url in urls:
            request = requests.get(
                f"{url}/{conent_hash}/{filepath}"
            )
            if request.status_code == 200: break

        if request.status_code == 200:
            return request.content
        else:
            return request.status_code
    
    def run(self):
        for item in self.folder.items:
            if not self.is_working: return
            if isinstance(item, ItemChain): continue

            base_filepath = posixpath.join(self.assets_basepath, item.name)
            full_path = os.path.join(self.assets_path, base_filepath)

            server_response = DownloaderWorker.download_file(
                self.assets_urls, self.content_hash, base_filepath
            )
            
            if isinstance(server_response, bytes):
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "wb") as file:
                    file.write(server_response)

                if full_path.endswith((".toml", ".csv")):
                    try:
                        processed_data, *extra_data = decompress_data(server_response)
                        with open(full_path, "wb") as file:
                            file.write(processed_data)
                        self.message(f"Decompressed {base_filepath}")
                    except Exception as e:
                        self.message(f"Decompression failed for {base_filepath}: {e}")

                self.message(f"Downloaded {base_filepath}")
            else:
                self.message(f"Failed to download \"{base_filepath}\" with code {server_response}")

        self.message("Done")
        self.is_working = False

    def message(self, text: str):
        print(f"[{self.name}] {text}")

def DownloaderDecorator(function):
    def decorator(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except KeyboardInterrupt:
            args[0].stop_all_workers()
            exit(0)
    return decorator

class Downloader:            
    def __init__(self,
                 content_urls: list[str],
                 content_hash: str,
                 output_folder: str,
                 max_workers=8,
                 worker_max_items=50,
                 strict_level=0) -> None:
        self.workers: list[DownloaderWorker] = []
        self.max_workers = max_workers
        self.worker_max_items = worker_max_items
        self.output_folder = output_folder
        self.content_urls = content_urls
        self.content_hash = content_hash
        self.strict_level = strict_level
    
    @staticmethod
    def add_unlisted_items(folder: ItemChain):
        folder.items.append(Item("fingerprint.json", ""))
        folder.items.append(Item("version.number", ""))

    def check_workers_status(self) -> bool:
        i = 0
        while len(self.workers) > i:
            worker = self.workers[i]
            if not worker.is_working:
                del self.workers[i]
            else:
                i += 1
        if len(self.workers) == 0:
            return True
        return False

    def wait_for_workers(self) -> None:
        while True:
            if self.check_workers_status():
                break

    def add_worker(self, basepath: str, chain: ItemChain) -> bool:
        if len(self.workers) >= self.max_workers:
            return False
        worker = DownloaderWorker(
            self.content_hash,
            self.content_urls,
            self.output_folder,
            basepath,
            chain
        )
        print(f"[Main] {chain.name or 'Assets'} folder added to download queue")
        worker.start()
        self.workers.append(worker)
        return True
    
    def stop_all_workers(self):
        for worker in self.workers:
            worker.is_working = False
        self.wait_for_workers()

    @DownloaderDecorator
    def download(self, folder: ItemChain, basepath: str = "") -> None:
        current_dir = os.path.join(self.output_folder, basepath)
        os.makedirs(current_dir, exist_ok=True)
        
        worker_chunks: list[ItemChain] = []
        i = 0
        temp_chunk = ItemChain(folder.name)
        
        for item in folder.items:
            if isinstance(item, ItemChain): continue
            asset_path = os.path.join(current_dir, item.name)
            valid_file = False
            if self.strict_level >= 1:
                valid_file = os.path.exists(asset_path) and len(item.hash) != 0 
            if self.strict_level >= 2:
                if valid_file:
                    with open(asset_path, "rb") as file:
                        digest = sha1(file.read())
                        valid_file = digest.hexdigest() == item.hash
            if valid_file: continue
            if i >= self.worker_max_items:
                i = 0
                worker_chunks.append(temp_chunk)
                temp_chunk = ItemChain(folder.name)
            temp_chunk.items.append(item)
            i += 1
        
        if len(temp_chunk.items) != 0:
            worker_chunks.append(temp_chunk)
                
        for worker_chunk in worker_chunks:
            while True:
                self.check_workers_status()
                if self.add_worker(basepath, worker_chunk):
                    break

        for item in folder.items:
            if isinstance(item, Item): continue
            self.download(item, posixpath.join(basepath, item.name))
            
    @DownloaderDecorator
    def download_folder(self, folder: ItemChain) -> None:
        print("Downloading...")
        self.download(folder)
        self.wait_for_workers()
        print("Downloading is finished")
    
    @DownloaderDecorator
    def download_fingerprint(self, fingerprint: dict) -> None:
        root = ItemChain.from_fingerprint(fingerprint)
        Downloader.add_unlisted_items(root)
        self.download_folder(root)
