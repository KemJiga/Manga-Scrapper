import difflib
from collections import OrderedDict

def search_by_accuracy(search_term, titles_dict):
    # Extract the list of titles from the dictionary
    titles = list(titles_dict.keys())
    
    # Find the closest match
    closest_matches = difflib.get_close_matches(search_term, titles, n=1, cutoff=0.6)
    
    # Return the closest match if found, otherwise return None
    if closest_matches:
        return closest_matches[0]
    else:
        return None
    
def reverse_order_dict(original_dict):
    reversed_order_dict = OrderedDict(reversed(list(original_dict.items())))
    return reversed_order_dict

import zipfile
from io import BytesIO
import os
def zip_specific_folder(folder_path):
    # Create a BytesIO object to hold the zip file in memory
    memory_file = BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Create the full file path
                file_path = os.path.join(root, file)
                
                # Write the file to the zip, using relative path
                zf.write(file_path, os.path.relpath(file_path, folder_path))
    
    memory_file.seek(0)
    return memory_file