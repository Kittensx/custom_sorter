import os
import json
import re


class PromptFilter:
    """A class to process and clean metadata prompts from Automatic1111 files."""

    FILTER_PATTERNS = [
        r":\d+[-%]?\d*%?",  # Remove numbered weights like ":15-30" or ":15%-100%"
        r"[~!]+",  # Remove weight markers (~, !, !!)
    ]

    def __init__(self, metadata_file):
        self.metadata_file = metadata_file
        self.parameters = self._read_metadata_file()

    def _read_metadata_file(self):
        """Reads the metadata file and extracts the raw parameter text."""
        if not os.path.exists(self.metadata_file):
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_file}")

        with open(self.metadata_file, "r", encoding="utf-8") as file:
            return file.read()

      
    def extract_metadata_fields(self):
        """Extracts metadata fields dynamically, ensuring correct key-value pairs."""
        metadata = {}
        positive_prompts = []
        metadata_fields = {}
        hashes = {}

        # ✅ Split input into lines
        lines = self.parameters.strip().split("\n")

        found_metadata = False  # ✅ Track when we detect metadata
        for line in lines:
            line = line.strip()

            # ✅ Detect key-value pairs (metadata starts here)
            match = re.match(r"([\w\s-]+):\s*(.+)", line)
            if match:
                found_metadata = True  # ✅ We've detected metadata
                key = match.group(1).strip().lower().replace(" ", "_")
                value = match.group(2).strip()

                # ✅ Convert numerical values properly
                if value.isdigit():
                    metadata_fields[key] = int(value)
                else:
                    try:
                        metadata_fields[key] = float(value) if "." in value else value
                    except ValueError:
                        metadata_fields[key] = value

                continue  # ✅ Move to the next line

            # ✅ If we haven't found metadata yet, assume it's part of the positive prompts
            if not found_metadata:
                positive_prompts.append(line)

        # ✅ Handle hashes separately
        if "model_hash" in metadata_fields:
            hashes["model"] = metadata_fields.pop("model_hash")

        # ✅ Store extracted data
        metadata["positive_prompts"] = positive_prompts if positive_prompts else []
        metadata["negative_prompt"] = []  # ✅ Always include this field, even if empty
        metadata["hashes"] = hashes
        metadata.update(metadata_fields)

        return metadata

    def extract_metadata(self, key):
        """
        Extracts the correct metadata value, ensuring that it only searches below "Negative prompt:".
        """
        # Locate the position of "Negative prompt:"
        neg_prompt_index = self.parameters.lower().find("negative prompt:")

        if neg_prompt_index != -1:
            text = self.parameters[neg_prompt_index:]  # Start searching from here
        else:
            text = self.parameters

        # Match 'Key:' exactly, but ignore 'Model hash' and 'Hashes'
        pattern = rf"(?<!hash\s)({key}:\s*([^,]+))"
        match = re.search(pattern, text, re.IGNORECASE)  # Case-insensitive search

        if match:
            return match.group(2).strip()  # Extract only the value

        return "Unknown"

    def process_metadata(self, output_file):
        """Processes the metadata file and extracts structured metadata."""
        metadata_fields = self.extract_metadata_fields()

        # Extract positive prompts and store inside metadata
        metadata_fields["positive_prompts"] = self.extract_positive_prompts()

        parsed_data = {"metadata": metadata_fields}

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(parsed_data, file, indent=4)

        #print(f"✅ Parsed metadata saved to {output_file}")
        return parsed_data

 
    @staticmethod
    def parse_parameters(parameters_text):
        """
        Extracts structured metadata fields from JSON or text files.
        - ✅ Extracts full positive prompt
        - ✅ Removes everything after "Negative prompt:"
        - ✅ Parses metadata fields dynamically (Steps, Sampler, etc.)
        - ✅ Supports ExifTool JSON format & A1111 text format
        """

        metadata = {}  # Dictionary to store extracted data

        # **Ensure Input is a String**
        if isinstance(parameters_text, dict) and "Parameters" in parameters_text:
            parameters_text = parameters_text["Parameters"]  # ✅ Extract only "Parameters" field

        # **Step 1: Split Positive Prompt from Metadata Fields**
        neg_prompt_index = parameters_text.lower().find("negative prompt:")
        if neg_prompt_index != -1:
            positive_prompt = parameters_text[:neg_prompt_index].strip()  # ✅ Everything above is the Positive Prompt
            metadata_section = parameters_text[neg_prompt_index:].strip()  # ✅ Everything below is Metadata Fields
        else:
            positive_prompt = parameters_text.strip()  # ✅ If no Negative Prompt, assume all is positive prompt
            metadata_section = ""

        # **Store Extracted Positive Prompt**
        metadata["positive_prompts"] = positive_prompt  # ✅ Store in metadata dictionary

        # **Step 2: Extract Metadata Fields (Below Negative Prompt)**
        metadata_lines = re.findall(r"\n?([\w\s-]+):\s*([^\n]+)", metadata_section)
        for key, value in metadata_lines:
            key = key.strip().lower().replace(" ", "_")  # ✅ Normalize key format

            # **Ensure Metadata Fields Are Stored Correctly**
            if "," in value and not value.startswith("{"):  # ✅ Ignore JSON-like values
                values = [v.strip() for v in value.split(",") if v.strip()]
                metadata[key] = values  # ✅ Store as a list instead of a single string
            else:
                metadata[key] = value.strip()

        # **Step 3: Extract Hashes Properly**
        hashes_match = re.search(r'Hashes:\s*\{.*?"model":\s*"([\da-fA-F]+)".*?\}', metadata_section)
        if hashes_match:
            metadata["hashes"] = {"model": hashes_match.group(1)}

        return metadata




