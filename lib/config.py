import json
import argparse
from enum import Enum

class ServerDescriptor:
    def __init__(self, name: str = "", address: str = "") -> None:
        self.short_name = name
        self.server_address = address

class Config:
    def __init__(self, filepath: str) -> None:
        file = open(filepath, "rb")
        data: dict = json.load(file)
        file.close()

        # self.server_specific_data: dict = data["server_specific_data"]
        self.save_dump = True if data.get("save_dump") else False
        self.auto_update = True if data.get("auto_update") else False
        self.make_patches = True if data.get("make_patches") else False
        self.make_detailed_patches = (
            True if data.get("make_detailed_patches") else False
        )
        self.max_workers = data.get("max_workers") or 1
        self.worker_max_items = data.get("worker_max_items") or 1

        servers_data: dict = data.get("servers")
        self.servers: list[ServerDescriptor] = []

        # Session Settings
        parser = argparse.ArgumentParser(
            prog="SC-Downloader", description="Asset Downloader for Supercell Games"
        )

        parser.add_argument(
            "--hash",
            type=str,
            help="Specify your version hash by which you want to download assets",
            default=None,
        )

        parser.add_argument(
            "--asset-servers",
            help="You can provide your own links to asset servers",
            nargs="+",
            default=None,
        )

        parser.add_argument(
            "--repair-mode",
            action=argparse.BooleanOptionalAction,
            help="Checks if all files exist and loads them if they are missing",
            default=False,
        )

        parser.add_argument(
            "--strict-repair-mode",
            action=argparse.BooleanOptionalAction,
            help="Checks file content and if it is corrupted, downloads it again. Much slower than default mode.",
            default=False,
        )

        args = parser.parse_args()

        self.custom_hash: str = "" or args.hash
        self.asset_servers_override = args.asset_servers

        self.strict_repair: bool = args.strict_repair_mode
        self.repair: bool = args.repair_mode or self.strict_repair
        
        # Server specific variables
        self.status_code_size = 4 # int
        self.variable_schema: list = []

        for server in servers_data:
            self.servers.append(ServerDescriptor(server, servers_data[server]))
            
    def load_server_specific_data(self, name: str) -> None:
        data = self.server_specific_data
        pass
