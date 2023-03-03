import json
import os
import yaml

# Directory containing the JSON files
directory = '/path/to/json/directory/'

# Loop through each file in the directory
for filename in os.listdir(directory):
    if not filename.endswith('.json'):
        continue
    input_filename = os.path.join(directory, filename)
    output_filename = os.path.splitext(filename)[0] + '.yaml'
    # Open the JSON file
    with open(input_filename) as json_file:
        # Load the JSON data
        data = json.load(json_file)
    # Create the output YAML filename
    with open(os.path.join(directory, output_filename), 'w') as yaml_file:
        # Write the YAML data
        yaml.dump(data, yaml_file)
    # Remove JSON file
    os.unlink(input_filename)
