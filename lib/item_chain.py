from __future__ import annotations
import os


''' Representation of "File" or asset with hash and name '''
class Item:
    def __init__(self, name: str, hash: str) -> None:
        self.name = name
        self.hash = hash

''' Representation of "Folder" or "Chain of asset files" '''
class ItemChain:
    def __init__(self, name: str, *args) -> None:
        self.name = name
        self.items: list[Item or ItemChain] = list(args)
    
    def get(self, name: str) -> Item or ItemChain or None:
        """
        The function "get" searches for an item with a given name in a list of items and returns the
        item if found, otherwise it returns None.
        
        :param name: A string representing the name of the item to search for
        :type name: str
        :return: an instance of the class "Item" or "ItemChain" if an item with the specified name is found in the list
        of items. If no matching item is found, it returns "None".
        """
        for item in self.items:
            if item.name == name:
                return item

        return None

    def get_chain(self, chain_names: list[str], auto_create=False) -> ItemChain or None:
        """
        The `get_chain` function retrieves a specific chain from a list of chain names, optionally
        creating the chain if it doesn't exist.
        
        :param chain_names: A list of strings representing the names of the chains to be retrieved
        :type chain_names: list[str]
        :param auto_create: The `auto_create` parameter is a boolean flag that determines whether a new
        `ItemChain` should be automatically created if the specified chain name does not exist. If
        `auto_create` is set to `True`, a new `ItemChain` will be created and added to the `items` list,
        defaults to False (optional)
        :return: The function `get_chain` returns an instance of `ItemChain` or `None`.
        """
        if (len(chain_names) == 0): return self
        
        result_item = None
        for chain_name in chain_names:
            iterable_item: ItemChain = result_item if result_item is not None else self
            iterable_item_result: ItemChain or None = None
            
            for item in iterable_item.items:
                if not isinstance(item, ItemChain):
                    continue

                if item.name == chain_name:
                    iterable_item_result = item
                    break

            if iterable_item_result is None:
                if auto_create:
                    result_item = ItemChain(chain_name)
                    iterable_item.items.append(result_item)
                else:
                    return None
            else:
                result_item = iterable_item_result

        return result_item

    @staticmethod
    def from_fingerprint(data: dict):
        """
        The `from_fingerprint` function takes in a dictionary of file descriptors and creates a
        hierarchical structure of folders and files based on the file paths and hashes provided.
        
        :param data: The `data` parameter is a dictionary that contains information about asset files.
        :type data: dict
        :return: an instance of the ItemChain class, which represents a hierarchical structure of items
        (files and folders) based on the provided fingerprint data.
        """
        root = ItemChain("")

        files: list[dict] = data["files"]

        for descriptor in files:
            name = str(descriptor["file"])
            hash = str(descriptor["sha"])

            folder = root

            basename = os.path.dirname(name)
            if (basename):
                folder_name_chain = os.path.normpath(basename).split(os.sep)
            else:
                folder_name_chain = []
            
            folder: ItemChain = root.get_chain(folder_name_chain, True)
            folder.items.append(Item(os.path.basename(name), hash))

        return root
