import struct
import time
import os

FILE_PATH = r'products.bin'
STRUCT_FORMAT = 'QQ20sQd20sc'
ORDER = 4  # Ordem da Árvore B
CHUNK_SIZE = 5000000 

class HashTable:
    def __init__(self, size):
        self.size = size
        self.table = [[] for _ in range(size)]
    
    def _hash_function(self, key):
        return hash(key) % self.size
    
    def insert(self, key, value):
        index = self._hash_function(key)
        self.table[index].append((key, value))
    
    def search(self, key):
        index = self._hash_function(key)
        for k, v in self.table[index]:
            if k == key:
                return v
        return None

def build_hash_index(file_path, struct_format, hash_table_size):
    start_time = time.time()
    hash_table = HashTable(hash_table_size)
    record_size = struct.calcsize(struct_format)
    
    with open(file_path, 'rb') as file:
        while True:
            record = file.read(record_size)
            if len(record) < record_size:
                break
            unpacked_data = struct.unpack(struct_format, record)
            endereco = unpacked_data[0] 
            id_categoria = unpacked_data[3]  
            hash_table.insert(id_categoria, endereco) 
    
    print("Índice Hash construído em %s segundos" % (time.time() - start_time))
    return hash_table

def search_hash_index(hash_table, id_produto):
    endereco = hash_table.search(id_produto)
    return endereco

class BTreeNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.pointers = []

class BTree:
    def __init__(self, order):
        self.root = BTreeNode(is_leaf=True)
        self.order = order
    
    def search(self, key):
        start_time = time.time()
        current_node = self.root
        while not current_node.is_leaf:
            idx = 0
            while idx < len(current_node.keys) and key > current_node.keys[idx]:
                idx += 1
            current_node = current_node.pointers[idx]
        
        try:
            idx = current_node.keys.index(key)            
            return current_node.pointers[idx]
        except ValueError:
            return None

    def insert(self, key, pointer):
        root = self.root
        if len(root.keys) == 2 * self.order - 1:
            new_root = BTreeNode()
            new_root.pointers.append(self.root)
            self.split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, key, pointer)

    def _insert_non_full(self, node, key, pointer):
        if node.is_leaf:
            idx = 0
            while idx < len(node.keys) and node.keys[idx] < key:
                idx += 1
            node.keys.insert(idx, key)
            node.pointers.insert(idx, pointer)
        else:
            idx = len(node.keys) - 1
            while idx >= 0 and key < node.keys[idx]:
                idx -= 1
            idx += 1
            if len(node.pointers[idx].keys) == 2 * self.order - 1:
                self.split_child(node, idx)
                if key > node.keys[idx]:
                    idx += 1
            self._insert_non_full(node.pointers[idx], key, pointer)

    def split_child(self, parent, idx):
        order = self.order
        child = parent.pointers[idx]
        new_child = BTreeNode(is_leaf=child.is_leaf)
        parent.keys.insert(idx, child.keys[order - 1])
        parent.pointers.insert(idx + 1, new_child)
        new_child.keys = child.keys[order:]
        new_child.pointers = child.pointers[order:]
        child.keys = child.keys[:order - 1]
        child.pointers = child.pointers[:order]

def build_b_tree(file_path, order, struct_format, chunk_size):
    start_time = time.time()
    b_tree = BTree(order)
    
    record_size = struct.calcsize(struct_format)
    with open(file_path, 'rb') as file:
        while True:
            record = file.read(record_size)
            if len(record) < record_size:
                break
            unpacked_data = struct.unpack(struct_format, record)
            key, pointer = unpacked_data[1], unpacked_data[0]
            b_tree.insert(key, pointer)
    
    print(f"Árvore B construída em {time.time() - start_time} segundos")
    return b_tree
   
def add_entry():
    struct = [
        0,
        int(input("Digite o id do produto: ")),
        input("Digite a marca do produto: ").ljust(20, " ").encode('utf-8')[:20],
        int(input("Digite o id da categoria do produto: ")),
        float(input("Digite o preço do produto: ")),
        input("Digite o tipo do evento: ").ljust(20, " ").encode('utf-8')[:20], 
        "N".encode('utf-8')[:1]
    ]
    
    start_time = time.time() 
    print("Inserindo no arquivo de dados")
    insert_to_file(tuple(struct), STRUCT_FORMAT, FILE_PATH, False)
    print(f"Dado inserido em {time.time() - start_time} segundos")

def insert_to_file(struct_data, struct_format, filepath, found):
    with open(filepath, 'r+b') as file:
        entry_size = struct.calcsize(struct_format)  
        offset = struct_data[0] * entry_size
        print(f'Produto será inserido na chave {struct_data[0]} offset {offset}')

        file.seek(0, os.SEEK_END)
        file_size = file.tell()

        bytes_to_shift = file_size - offset

        current_position = offset
        while bytes_to_shift > 0:
            read_size = min(CHUNK_SIZE, bytes_to_shift)
            file.seek(current_position) 
            data_to_shift = file.read(read_size) 

            file.seek(current_position + entry_size) 

            file.write(data_to_shift)

            current_position += read_size
            bytes_to_shift -= read_size
        
        for i in range(struct_data[0] + 1, (file_size // entry_size) + 1):
            file.seek(i * entry_size)
            record = file.read(entry_size)

            if len(record) < entry_size:
                break 

            unpacked = list(struct.unpack(struct_format, record))
            unpacked[0] += 1 
                
            file.seek(i * entry_size)
            file.write(struct.pack(struct_format, *unpacked))
        
        file.seek(offset) 

        file.write(struct.pack(struct_format, *struct_data))

    file.close()

while(True):
    print("1 - Construir a Árvore B")
    print("2 - Buscar uma chave na Árvore B")
    print("3 - Construir o Índice Hash")
    print("4 - Buscar uma chave no Índice Hash")
    print("5 - Adicionar produto")
    print("0 - Sair")
    opcao = int(input("Digite a opção desejada: "))
    if opcao == 1:
        b_tree = build_b_tree(FILE_PATH, ORDER, STRUCT_FORMAT, CHUNK_SIZE)
        print("Árvore B construída com sucesso!")
    elif opcao == 2:
        start_time = time.time()
        id_to_search = int(input("Digite o id do produto: "))
        result = b_tree.search(id_to_search)
        if result is not None:
            
            print(f"Chave {id_to_search} encontrada no índice {result}.")
        else:
            print(f"Chave {id_to_search} não encontrada.")
        print(f"Operação de busca realizada em {time.time() - start_time} segundos")
    elif opcao == 3:
        hash_index = build_hash_index(FILE_PATH, STRUCT_FORMAT, 5000001)
    elif opcao == 4:
        start_time = time.time()
        id_to_search = int(input("Digite o id da categoria: "))
        result = search_hash_index(hash_index, id_to_search)
        if result is not None:
            print(f"Chave {id_to_search} encontrada no índice {result}.")
        else:
            print(f"Chave {id_to_search} não encontrada.")
        print(f"Operação de busca realizada em {time.time() - start_time} segundos")
    elif opcao == 5:
        add_entry()
        b_tree = build_b_tree(FILE_PATH, ORDER, STRUCT_FORMAT, CHUNK_SIZE)
        hash_index = build_hash_index(FILE_PATH, STRUCT_FORMAT, 5000001)
    elif opcao == 0:
        break
