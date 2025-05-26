import os
import json

input_folder = 'drdo_output2'
output_file = 'newoutput.json'

with open(output_file, 'w', encoding='utf-8') as out_file:
    out_file.write('[\n')  # Start of JSON array
    first_entry = True

    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(input_folder, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                if lines and lines[0].startswith('URL:'):
                    url = lines[0].replace('URL:', '').strip()
                    content = ''.join(lines[1:]).strip()

                    record = {
                        "url": url,
                        "content": content
                    }

                    if not first_entry:
                        out_file.write(',\n')  # Add comma between JSON objects
                    else:
                        first_entry = False

                    json.dump(record, out_file, ensure_ascii=False)

    out_file.write('\n]\n')  # End of JSON array

print("✅ Conversion complete: output saved to 'output.json'")
