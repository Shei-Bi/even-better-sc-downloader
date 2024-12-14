from .item_chain import ItemChain, Item
from threading import Thread
import os
import posixpath
import requests
from hashlib import sha1

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

        # Final writing to file
        if request.status_code == 200:
            return request.content
        else:
            return request.status_code
    
    def run(self):
        """
        The function downloads files from multiple URLs and saves them to a specified directory,
        providing status messages along the way.
        :return: The code is returning either None or stopping the execution of the function if the
        `self.is_working` flag is False.
        """

        for item in self.folder.items:
            if not self.is_working: return
            
            if isinstance(item, ItemChain):
                continue

            base_filepath = posixpath.join(self.assets_basepath, item.name)
            
            server_response = DownloaderWorker.download_file(self.assets_urls, self.content_hash, base_filepath)
            
            if (isinstance(server_response, bytes)):
                with open(os.path.join(self.assets_path, base_filepath), "wb") as file:
                    file.write(server_response)
                
                self.message(f"Downloaded {base_filepath}")
            else:
                self.message(f"Failed to download \"{base_filepath}\" with code {server_response}")

        self.message("Done")
        self.is_working = False

    def message(self, text: str):
        """
        The function "message" prints a formatted message with the name of the object and the provided
        text.
        
        :param text: The `text` parameter is a string that represents the message that you want to print
        :type text: str
        """
    
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
                 strict_level = 0) -> None:
        self.workers: list[DownloaderWorker] = []
        self.max_workers = max_workers
        self.worker_max_items = worker_max_items
        self.output_folder = output_folder
        self.content_urls = content_urls
        self.content_hash = content_hash
        self.strict_level = strict_level
    
    @staticmethod
    def add_unlisted_items(folder: ItemChain):
        """
        The function adds specific items to a given chain
        
        :param folder: The parameter "folder" is of type ItemChain
        :type folder: ItemChain
        """

        # Fingerprint itself
        folder.items.append(Item("fingerprint.json", ""))
        
        # Version info
        folder.items.append(Item("version.number", ""))

    def check_workers_status(self) -> bool:
        """
        The function checks the status of workers and returns True if all workers are not working,
        otherwise it returns False.
        :return: a boolean value. It returns True if there are no workers in the list, and False
        otherwise.
        """

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
        """
        The function waits until all workers have finished their tasks.
        """

        while True:
            if self.check_workers_status():
                break

    def add_worker(self, basepath: str, chain: ItemChain) -> bool:
        """
        The function adds a worker to the download queue if the maximum number of workers has not been
        reached.
        
        :param basepath: The `basepath` parameter is a string that represents the base path where the
        downloaded files will be saved. It is used to determine the location where the downloaded files
        will be stored
        :type basepath: str
        :param chain: The `chain` parameter is an instance of the `ItemChain` class. It represents a
        chain of items that need to be downloaded
        :type chain: ItemChain
        :return: a boolean value. If the length of the `self.workers` list is less than the maximum
        number of workers (`self.max_workers`), the function will return `True`. Otherwise, it will
        return `False`.
        """

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
        """
        The function stops all workers by setting their "is_working" attribute to False and waits for
        them to finish their current tasks.
        """

        for worker in self.workers:
            worker.is_working = False
            
        self.wait_for_workers()

    @DownloaderDecorator
    def download(self, folder: ItemChain, basepath: str = "") -> None:
        """
        The `download` function takes a folder and downloads its contents, splitting them into worker
        chunks to be downloaded concurrently.
        
        :param folder: The `folder` parameter is an instance of the `ItemChain` class, which represents
        a collection of items. Each item can be either a file or a subfolder
        :type folder: ItemChain
        :param basepath: The `basepath` parameter is a string that represents the base path where the
        items will be downloaded. It is used to create the directory structure for the downloaded items
        :type basepath: str
        """

        # Folders prepare
        current_dir = os.path.join(self.output_folder, basepath)
        os.makedirs(
            current_dir, exist_ok=True
        )
        
        # worker_max_items sorting & existing files removing
        worker_chunks: list[ItemChain] = []
        
        i = 0
        temp_chunk = ItemChain(folder.name)
        
        for item in folder.items:
            if isinstance(item, ItemChain): continue
            
            asset_path = os.path.join(current_dir, item.name)
            
            valid_file = False
            if (self.strict_level >= 1):
                valid_file = os.path.exists(asset_path) and len(item.hash) != 0 
            
            if (self.strict_level >= 2):
                if (valid_file):
                    with open(asset_path, "rb") as file:
                        digest = sha1(file.read())
                        valid_file = digest.hexdigest() == item.hash
            
            if (valid_file): continue
            
            if (i >= self.worker_max_items):
                i = 0
                worker_chunks.append(temp_chunk)
                temp_chunk = ItemChain(folder.name)
            
            temp_chunk.items.append(item)
            i += 1
        
        # Append last small chunk
        if (len(temp_chunk.items) != 0):
            worker_chunks.append(temp_chunk)
                

        for worker_chunk in worker_chunks:
            while True:
                self.check_workers_status()
                if self.add_worker(basepath, worker_chunk):
                    break

        for item in folder.items:
            if isinstance(item, Item):
                continue

            self.download(item, posixpath.join(basepath, item.name))
            
    @DownloaderDecorator
    def download_folder(self, folder: ItemChain)  -> None:
        """
        The function `download_folder` downloads a folder and waits for the download to finish.
        
        :param folder: The `folder` parameter is of type `ItemChain`. It represents a folder or
        directory that needs to be downloaded
        :type folder: ItemChain
        """

        print("Downloading...")
        self.download(folder)
        self.wait_for_workers()
        print("Downloading is finished")
    
    @DownloaderDecorator
    def download_fingerprint(self, fingerprint: dict) -> None:
        """
        The function downloads a folder and its contents based on a given fingerprint.
        
        :param fingerprint: The `fingerprint` parameter is a dictionary that represents fingerprint data.
        :type fingerprint: dict
        """
    
        root = ItemChain.from_fingerprint(fingerprint)
        Downloader.add_unlisted_items(root)
        self.download_folder(root)
        
