import struct

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
        current_node = self.root
        while not current_node.is_leaf:
            idx = 0
            # Procurar a posição correta no nó
            while idx < len(current_node.keys) and key > current_node.keys[idx]:
                idx += 1
            # Descer para o nó filho
            current_node = current_node.pointers[idx]
        
        # Agora estamos em um nó folha
        try:
            idx = current_node.keys.index(key)
            return current_node.pointers[idx]  # Retorna o ponteiro associado
        except ValueError:
            return None  # Chave não encontrada

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

def load_indices_from_struct_in_chunks(file_path, struct_format, chunk_size):
    indices = []
    record_size = struct.calcsize(struct_format)
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size * record_size)
            if not chunk:
                break
            for i in range(0, len(chunk), record_size):
                record = chunk[i:i+record_size]
                if len(record) < record_size:
                    break
                unpacked_data = struct.unpack(struct_format, record)
                indices.append((unpacked_data[0], unpacked_data[1]))  # Apenas os dois primeiros campos
    return indices

def build_b_tree_in_chunks(file_path, order, struct_format, chunk_size):
    # Criar a Árvore B
    b_tree = BTree(order)
    
    # Processar o arquivo em blocos
    record_size = struct.calcsize(struct_format)
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size * record_size)
            if not chunk:
                break
            print(f"Lendo {chunk_size} de registros e inserindo na árvore.")
            for i in range(0, len(chunk), record_size):
                record = chunk[i:i+record_size]
                if len(record) < record_size:
                    break
                unpacked_data = struct.unpack(struct_format, record)
                key, pointer = unpacked_data[1], unpacked_data[0]
                b_tree.insert(key, pointer)
    
    return b_tree

def build_hash_index(file_path, struct_format, column_index, hash_table_size):
    """Constrói uma tabela hash para uma coluna específica do arquivo binário."""
    hash_table = HashTable(hash_table_size)
    record_size = struct.calcsize(struct_format)
    
    with open(file_path, 'rb') as file:
        while True:
            record = file.read(record_size)
            if len(record) < record_size:
                break
            unpacked_data = struct.unpack(struct_format, record)
            key = unpacked_data[column_index]  # Coluna usada como chave
            value = unpacked_data[1]  # ID do produto (ou outro identificador)
            hash_table.insert(key, value)
    
    return hash_table

# Configurações e execução
FILE_PATH = r'D:\Arquivo\products.bin'  # Ajustar caminho conforme necessário
STRUCT_FORMAT = 'QQ20sQd20sc'  # Novo formato do arquivo
ORDER = 4  # Ordem da Árvore B
CHUNK_SIZE = 5000000  # Número de registros por bloco

b_tree = build_b_tree_in_chunks(FILE_PATH, ORDER, STRUCT_FORMAT, CHUNK_SIZE)
print("Árvore B construída com sucesso!")


# Buscar uma chave na Árvore B
key_to_search = 17200506  # Substitua pela chave que deseja buscar
result = b_tree.search(key_to_search)

if result is not None:
    print(f"Chave {key_to_search} encontrada no índice {result}.")
else:
    print(f"Chave {key_to_search} não encontrada.")