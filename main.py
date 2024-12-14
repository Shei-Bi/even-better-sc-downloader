import posixpath
from typing import Any
from lib.client import Client, HelloServerResponse
from lib.config import Config
from lib.downloader import Downloader, DownloaderWorker
from lib.item_chain import ItemChain, Item
import os
from shutil import move as fmove
from shutil import copyfile as fcopy

class ScDownloader:
    def __init__(self) -> None:
        self.config = Config("config.json")
        
        # Servers
        print("Choose server to connect: ")

        for i, descriptor in enumerate(self.config.servers):
            print(f'{i}. "{descriptor.short_name}": {descriptor.server_address}"')

        server_index = int(input("\nServer index: "))
        self.active_server = self.config.servers[server_index]

        self.assets_path = f"assets/{self.config.custom_hash or self.active_server.short_name}/"
        self.patches_path = f"patches/{self.active_server.short_name}"
        
        os.makedirs(self.assets_path, exist_ok=True)
        if (self.config.make_patches):
            os.makedirs(self.patches_path, exist_ok=True)
        
        # Downloading by hash stuff
        if (self.config.custom_hash):
            self.config.asset_servers_override = self.config.asset_servers_override or self.get_latest_asset_servers()

            hash_fingerprint = DownloaderWorker.download_file(
                self.config.asset_servers_override,
                self.config.custom_hash,
                "fingerprint.json"
            )
            
            if (isinstance(hash_fingerprint, int)):
                raise Exception(f"Failed to get fingerprint.json by hash {self.config.custom_hash}. Request failed with code {hash_fingerprint}")
            
            os.makedirs(self.assets_path, exist_ok=True)
            with open(os.path.join(self.assets_path, "fingerprint.json"), "wb") as file:
                file.write(hash_fingerprint)
            
        self.client = Client(self.assets_path)
        self.client.dump = self.config.save_dump
    
    @staticmethod
    def ask_question_bool(question: str) -> bool:
        """
        The function `ask_question_bool` prompts the user with a question and returns a boolean value
        based on their response.
        
        :param question: A string representing the question that will be asked to the user
        :type question: str
        :return: The function `ask_question_bool` returns a boolean value.
        """
    
        answer = str(input(f"{question} (yes/no): ")).lower()
        
        if answer.startswith("y"): return True
        if answer.startswith("n"): return False
        
        if answer.isdigit():
            return int(answer) >= 1
    
    @staticmethod
    def make_patch_chain(current: ItemChain, latest: ItemChain) -> list[ItemChain, ItemChain, ItemChain]:
        """
        The `make_patch_chain` function takes in two `ItemChain` objects, `current` and `latest`, and
        returns a list of three `ItemChain` objects representing new files, changed files, and deleted
        files between the two chains.
        
        :param current: The `current` parameter is an instance of the `ItemChain` class, which
        represents the current state of a chain of items. It contains a list of items
        :type current: ItemChain
        :param latest: The "latest" parameter is an instance of the ItemChain class, which represents
        the most recent version of a chain of items. It contains a collection of items, where each item
        can be either a file or a folder. The items in the "latest" chain may have been added, modified 
        or deleted
        :type latest: ItemChain
        :return: The function `make_patch_chain` returns a list containing three `ItemChain` objects:
        `new_files_result`, `changed_files_result`, and `deleted_files_result`.
        """

        def make_chain(current: ItemChain, new: ItemChain) -> list[ItemChain, ItemChain, ItemChain]:
            current_items_names = [item.name for item in current.items]
            
            new_files_result = ItemChain(current.name) 
            changed_files_result = ItemChain(current.name) 
            deleted_files_result = ItemChain(current.name) 
            deleted_files_indices = [True for _ in current.items]

            new_files_result = ItemChain(current.name) 
            for new_item in new.items:
                # New Files
                if new_item.name not in current_items_names:
                        new_files_result.items.append(new_item)
                        continue
                
                current_item_index = current_items_names.index(new_item.name)
                current_item = current.items[current_item_index]
                deleted_files_indices[current_item_index] = False
                
                if isinstance(new_item, Item):
                    # Changed Files
                    if (new_item.hash != current_item.hash):
                        changed_files_result.items.append(new_item)
                else:
                    # Folder Processing
                    new_files_chain, changed_files_chain, deleted_files_chain = make_chain(current_item, new_item)
                    
                    if (len(new_files_chain.items) != 0):
                        new_files_result.items.append(new_files_chain)
                        
                    if (len(changed_files_chain.items) != 0):
                        changed_files_result.items.append(changed_files_chain)
                    
                    if (len(deleted_files_chain.items) != 0):
                        deleted_files_result.items.append(deleted_files_chain)
                
            for i in range(len(current.items)):
                current_item = current.items[i]
                is_deleted = deleted_files_indices[i]
                
                if (is_deleted):
                    deleted_files_result.items.append(current_item)
            
            return [new_files_result, changed_files_result, deleted_files_result]
        return make_chain(current, latest)
    
    def download_all(self):
        """
        Downloads all files from client fingerprint to `self.client.assets_path`
        """
        
        asset_servers_urls = self.config.asset_servers_override or \
            [self.client.assets_url, self.client.assets_url_2, self.client.content_url]

        downloader = Downloader(
            asset_servers_urls,
            self.client.content_hash,
            self.client.assets_path,
            self.config.max_workers,
            self.config.worker_max_items,
            int(self.config.repair) + int(self.config.strict_repair),
        )
        downloader.download_fingerprint(self.client.fingerprint)
    
    def get_latest_client(self) -> Client:
        """
        The function `get_latest_client` returns client with the latest data.
        :return: an instance of the Client class.
        """
        client_latest = Client("")
        client_latest.major = client_latest.build = client_latest.revision = 0
        client_latest.connect(self.active_server.server_address)
        
        return client_latest
    
    def get_latest_asset_servers(self) -> list[str]:
        """
        The function `get_latest_asset_servers` returns a list of asset servers from the latest client.
        :return: a list of strings, specifically the assets URLs of the latest client.
        """
        client = self.get_latest_client()
        
        return [client.assets_url, client.assets_url_2, client.content_url]
    
    def check_update(self) -> tuple[bool, Client]:
        """
        The function `check_update` compares the content version of the current client with the content
        version of the latest client on the active server and returns a tuple indicating whether they
        are different and the latest client.
        :return: a tuple containing two values. The first value is a boolean indicating whether the
        client version is different from the latest version, and the second value is an instance of the
        Client class representing the latest client version.
        """
        client_latest = self.get_latest_client()
        is_different = False in [client_latest.content_version[i] <= self.client.content_version[i] for i in range(3)]
        # print(f"Current version is {client_latest.content_version}, Server Version is {self.client.content_version}")
        return (is_different, client_latest)

    def make_update(self, latest_client: Client or None = None) -> None:
        """
        The function `make_update` is responsible for updating the client's assets by downloading new
        and changed files, and deleting unnecessary files.
        
        :param latest_client: The `latest_client` parameter is an instance of the `Client` class or
        `None`. It represents the latest version of the client that needs to be updated. If it is
        `None`, the `check_update()` method is called to get the latest client version
        :type latest_client: Client or None
        :return: The function does not return anything. It has a return type annotation of `None`.
        """

        if latest_client is None:
            latest_client = self.get_latest_client()
        
        print("Updating...")
        downloader = Downloader(
            [latest_client.assets_url, latest_client.assets_url_2, latest_client.content_url],
            latest_client.content_hash,
            self.client.assets_path,
            self.config.max_workers,
            self.config.worker_max_items,
        )
        
        latest_chain = ItemChain.from_fingerprint(latest_client.fingerprint)
        current_chain = ItemChain.from_fingerprint(self.client.fingerprint)
        
        new_files, changed_files, deleted_files = ScDownloader.make_patch_chain(current_chain, latest_chain)
        
        if (len(new_files.items) == 0):
            print("There are no new files here")
        else:
            print("New Files: ")
            downloader.download_folder(new_files)
            
        print("Downloading changed files")
        Downloader.add_unlisted_items(changed_files)
        downloader.download_folder(changed_files)
        
        print("Deleting unnecessary files")
        
        # Some prepares for patching
        old_version = ".".join([str(num) for num in self.client.content_version])
        new_version = ".".join([str(num) for num in latest_client.content_version])
        patch_name = f"{old_version} {new_version}"
        patch_path = os.path.join(self.patches_path, patch_name)
        deleted_patch_path = os.path.join(patch_path, "deleted")
        changed_patch_path = os.path.join(patch_path, "changed")
        new_patch_path = os.path.join(patch_path, "new")
        
        def remove_files(folder: ItemChain, basepath: str = ""):
            # Macro optimization to avoid calling makedirs for each file
            destination_basepath: str or None = None
            if (self.config.make_detailed_patches):
                destination_basepath = os.path.join(deleted_patch_path, basepath)
                os.makedirs(destination_basepath, exist_ok=True)

            for item in folder.items:
                if isinstance(item, ItemChain):
                    remove_files(item, posixpath.join(basepath, item.name))
                else:
                    asset_path = os.path.join(self.client.assets_path, basepath, item.name)
                    
                    if (self.config.make_detailed_patches):
                        asset_destination = os.path.join(destination_basepath, item.name)
                        
                        try:
                            fmove(asset_path, asset_destination)
                        except FileNotFoundError:
                            print(f"Failed to move file: {os.path.normpath(asset_path)} -> {os.path.normpath(asset_destination)}")
                            
                    else:
                        os.remove(asset_path)
        
        def move_files(folder: ItemChain, output_path: str, basepath: str = ""):
            destination_basepath = os.path.join(output_path, basepath)
            os.makedirs(destination_basepath, exist_ok=True)

            for item in folder.items:
                if isinstance(item, ItemChain):
                    move_files(item, output_path, posixpath.join(basepath, item.name))
                else:
                    asset_path = os.path.join(self.client.assets_path, basepath, item.name)
                    asset_destination = os.path.join(destination_basepath, item.name)
                    
                    try:
                        fcopy(asset_path, asset_destination)
                    except FileNotFoundError:
                        print(f"Failed to copy file: {os.path.normpath(asset_path)} -> {os.path.normpath(asset_destination)}")
                    
        
        remove_files(deleted_files)                                                                         # Deleted Files Move
        if (not self.config.make_patches): return
        
        move_files(new_files, new_patch_path if self.config.make_detailed_patches else patch_path)          # New Files Copy
        move_files(changed_files, changed_patch_path if self.config.make_detailed_patches else patch_path)  # Changed Files Copy

    def make_connect(self) -> bool:
        status = self.client.connect(self.active_server.server_address)
            
        if status == HelloServerResponse.Success:
            print(f"Successfully connected to {self.active_server.short_name}")
            return True
        elif status == HelloServerResponse.NeedUpdate:
            print(
                f"Successfully connected to {self.active_server.short_name} but server requires update. Updating..."
            )
            self.make_update()
            return True
            
        return False
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """
        The function checks if the client is connected to a server, updates the server if necessary,
        downloads assets if it's the first connection, and checks for updates and downloads them if
        requested.
        """
        
        major, _, _ = self.client.content_version

        if self.active_server.server_address=="game.clashroyaleapp.com":
            self.client.major=7 #speed up
        # Downloading from scratch
        if major == 0: 
            print("Detected first connection. This can take a little bit long time. Downloading all assets...")
            if (not self.make_connect()): return
            self.download_all()
            return

        if not self.client.fingerprint:
            if (not self.make_connect()): return

        # User hash handling
        if (self.config.custom_hash): 
            print(f"Downloading assets using hash {self.config.custom_hash}")
            self.download_all()
            return
        
        if (self.config.repair):
            self.download_all()
            return

        # Update Check
        is_update_available, client_latest = self.check_update()
        
        if is_update_available:
            is_update_granted = self.config.auto_update
            
            old_version = ".".join([str(num) for num in self.client.content_version])
            new_version = ".".join([str(num) for num in client_latest.content_version])
            
            if (self.config.auto_update):
                print(f"New update found {old_version} -> {new_version}")
            else:
                is_update_granted = ScDownloader.ask_question_bool(f"New update found {old_version} -> {new_version}. Do you want download it?")
                
            if (is_update_granted):
                self.make_update(client_latest)

        else:
            print("All files are ok and do not require updates")

if __name__ == "__main__":
    downloader = ScDownloader()
    downloader()