import os
import re
import binascii
import gzip
import tempfile
import tarfile

os.environ['TMP'] = 'D:\\'
os.environ['TEMP'] = 'D:\\'

def read_hex_file(hex_filename):
    with open(hex_filename, 'r') as f:
        hex_string = f.read()
    return re.sub('[^0-9A-Fa-f]', '', hex_string)

def hex_to_bin(hex_string):
    return binascii.unhexlify(hex_string)

def write_temp_file(binary_data):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    with open(temp_file.name, 'wb') as f:
        f.write(binary_data)
    return temp_file.name

def compress_file(temp_filename):
    compressed_file = tempfile.NamedTemporaryFile(suffix='.tgz', delete=False)
    with gzip.open(temp_filename, 'rb') as f_in:
        with open(compressed_file.name, 'wb') as f_out:
            f_out.write(f_in.read())
    return compressed_file.name

def extract_tar(tar_filename, extract_path):
    with tarfile.open(tar_filename, 'r') as tar:
        tar.extractall(path=extract_path)

def hex_to_tar(hex_filename, tar_filename, extract_path):
    hex_string = read_hex_file(hex_filename)
    binary_data = hex_to_bin(hex_string)
    temp_filename = write_temp_file(binary_data)
    compressed_filename = compress_file(temp_filename)
    os.rename(compressed_filename, tar_filename)
    extract_tar(tar_filename, extract_path)
    os.remove(tar_filename)  # 刪除.tar檔案



# 使用範例
hex_filename = 'D:/EAP/Recipe/WB_KS/recipe_hex.txt'
tar_filename = 'D:/EAP/Recipe/WB_KS/output.tar'
extract_path = 'D:/EAP/Recipe/WB_KS/temp_recipe'
hex_to_tar(hex_filename, tar_filename, extract_path)