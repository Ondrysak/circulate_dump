import base64
from pathlib import Path
import re
import urllib.request    
import os

def dump_patch_from_base64(base64_encoded_patch,folder):
    decoded_patch = base64.b64decode(base64_encoded_patch).decode("utf-8") 

    #print(decoded_patch)
    patch_bytes = []
    for byte_string in str(decoded_patch).split(','):
        patch_bytes += [int(byte_string)]
    #print(patch_bytes)
    name = ''.join([ chr(c) for c in patch_bytes[9:25] ]).strip()
    name = name.replace(' ', '_')
    print(f'  {name}')
    with open(f'{folder}\{name}.syx', 'wb') as f:
        for i in patch_bytes:
            f.write(bytes((i,)))


def find_unique_patches_in_html_dump(html_file_path):
    with open(html_file_path, 'r', encoding='UTF-8') as file:
        html_shit = file.read().replace('\n', '')
    #print(html_shit)
    matches = re.findall(r'atob\(.[0-9a-zA-Z=]+.\)', html_shit)
    unique_patches = set(matches)
    #print(unique_patches)
    patches_list = list(unique_patches)
    #print(patches_list)
    return [p[5:-2] for p in patches_list]

i = 0
urllib.request.urlretrieve("https://circulate.neuma.studio/", "source.html")
dump_folder = "dumps"
try:
    os.mkdir("dumps")
except FileExistsError:
    print(f"{dump_folder} already exists") 
for b64_patch in find_unique_patches_in_html_dump('source.html'):
    i += 1
    dump_patch_from_base64(b64_patch, dump_folder)

print(f'DUMPING FINISHED - {i} patches dumped')

