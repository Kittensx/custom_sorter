import os
import json
import re
from sort_methods.exif import extract_exiftool_metadata
from sort_methods.prompt_filter import PromptFilter

class MetadataExtractor:
    def __init__(self, metadata_folder=None):
        """Initialize the metadata extractor with an optional metadata storage folder."""
        self.metadata_folder = metadata_folder  

    @staticmethod
    def clean_metadata_prompt(prompt):
        """Cleans and refines metadata prompt strings."""
        prompt = re.sub(r"[~!]+", "", prompt)  # Remove unwanted characters like "~", "!"
        prompt = re.sub(r"(:\d+(\.\d+)?%-\d+%?)|(:\d+(\.\d+)?)|(-\d+%?)", "", prompt)  # Remove numeric modifiers

        prompt = prompt.replace("::", ", ").replace("//", ", ")  # Normalize separators
        prompt = re.sub(r"_(\{[^}]+\})", r", \1", prompt)  # Special rule: Replace underscores before `{}` with commas

        # Extract bracketed content separately
        bracketed_groups = re.findall(r"\{([^}]*)\}", prompt)
        for group in bracketed_groups:
            items = group.split(", ")
            replacement = ", ".join(items)  # Expand {a, b, c} to "a, b, c"
            prompt = prompt.replace(f"{{{group}}}", replacement)

        # Process words and remove duplicates
        words = re.split(r"[,:]", prompt)  # Split by commas and colons
        words = [word.strip().replace("_", " ") for word in words if word.strip()]  # Convert underscores normally
        words_cleaned = sorted(set(words), key=words.index)

        return words_cleaned  # Return as a list instead of a string

    def process_prompts(self, metadata):
        """Extracts and cleans positive and negative prompts, ensuring proper metadata extraction."""
        
        if "Parameters" in metadata:
            parsed_metadata = PromptFilter.parse_parameters(metadata["Parameters"])
            metadata.update(parsed_metadata)
            del metadata["Parameters"]  # ✅ Remove raw 'Parameters' field

        has_negative_prompt = "negative_prompt" in metadata
        has_positive_prompt = "positive_prompt" in metadata

        # ✅ Convert prompts to lists
        # ✅ Ensure `positive_prompts` is **always a list**
        positive_prompts = metadata.get("positive_prompts", [])
        if isinstance(positive_prompts, str):  
            positive_prompts = [p.strip() for p in positive_prompts.split(",") if p.strip()]  # ✅ Convert back to list

        # ✅ Ensure `negative_prompt` is also a list
        negative_prompts = metadata.get("negative_prompt", [])
        if isinstance(negative_prompts, str):
            negative_prompts = [p.strip() for p in negative_prompts.split(",") if p.strip()]


        # ✅ Step 1: Detect `\n` inside first positive prompt
        temp_metadata_list = []
        steps_value = None  # ✅ Store Steps separately

        if positive_prompts and "\n" in positive_prompts[0]:
            first_prompt, extra_data = positive_prompts[0].split("\n", 1)
            positive_prompts[0] = first_prompt.strip()  # ✅ Keep only the first prompt
            temp_metadata_list = extra_data.strip().split(",")  # ✅ Store remaining text for metadata parsing

            # ✅ Print extracted entries for debugging
            print(f"DEBUG: Extracted first prompt → {first_prompt}")
            print(f"DEBUG: Extracted remaining entries → {temp_metadata_list}")

        # ✅ Step 2: Find `"Steps"` and store its value separately
        if "steps" in [p.lower() for p in temp_metadata_list]:
            steps_index = next((i for i, p in enumerate(temp_metadata_list) if p.lower() == "steps"), None)

            if steps_index is not None:
                # ✅ Ensure `"Steps"` is not the last element before removing its value
                if steps_index + 1 < len(temp_metadata_list):
                    steps_value = temp_metadata_list.pop(steps_index + 1)  # ✅ Extract `"Steps"` value
                temp_metadata_list.pop(steps_index)  # ✅ Remove `"Steps"`

                print(f"DEBUG: Extracted Steps → {steps_value}")  # ✅ Print Steps for verification

        # ✅ Step 3: Append `"Steps"` to the end of the metadata list
        if steps_value is not None:
            temp_metadata_list.append("Steps")
            temp_metadata_list.append(steps_value)

        # ✅ Step 4: Move remaining metadata fields from `positive_prompts` to metadata
        extracted_metadata_list = []
        cleaned_prompts = []
        for item in positive_prompts:
            if re.match(r"^[\w\s-]+:\s*\S+", item):  # ✅ Detect "Key: Value" pairs
                extracted_metadata_list.append(item)
            else:
                cleaned_prompts.append(item)  # ✅ Keep valid descriptive prompts

        positive_prompts = cleaned_prompts  # ✅ Remove metadata from prompts

        # ✅ Step 5: Extract key-value pairs from extracted metadata
        metadata_fields = {}
        full_metadata_list = extracted_metadata_list + temp_metadata_list  # ✅ Merge both lists

        for i in range(0, len(full_metadata_list) - 1, 2):
            key = full_metadata_list[i].strip().lower().replace(" ", "_")
            value = full_metadata_list[i + 1].strip()

            # ✅ Ensure proper data type conversion
            if value.isdigit():
                metadata_fields[key] = int(value)
            else:
                try:
                    metadata_fields[key] = float(value) if "." in value else value
                except ValueError:
                    metadata_fields[key] = value

        # ✅ Step 6: Handle `"hashes"` correctly
        hashes = {}
        if "model_hash" in metadata_fields:
            hashes["model"] = metadata_fields.pop("model_hash")

        # ✅ Update metadata
        metadata.update(metadata_fields)
        metadata["hashes"] = hashes
        #metadata["positive_prompts"] = positive_prompts if positive_prompts else []
        #metadata["negative_prompt"] = negative_prompts if negative_prompts else []
        
        # ✅ Store cleaned values back into metadata
        metadata["positive_prompts"] = positive_prompts
        metadata["negative_prompt"] = negative_prompts

        return metadata  # ✅ Return cleaned metadata

    def process_steps(self, metadata):
        """Converts the `steps` list into structured key-value pairs inside metadata."""
        if "steps" in metadata and isinstance(metadata["steps"], list):
            steps_dict = {}

            for entry in metadata["steps"]:
                match = re.match(r"([\w\s-]+):\s*(.+)", entry)  # Extract "Key: Value" pairs
                if match:
                    key = match.group(1).strip().lower().replace(" ", "_")
                    value = match.group(2).strip()

                    # ✅ Convert numerical values where applicable
                    if value.isdigit():
                        steps_dict[key] = int(value)
                    else:
                        try:
                            steps_dict[key] = float(value) if "." in value else value
                        except ValueError:
                            pass  # Keep as a string if not convertible

                    steps_dict[key] = value
                else:
                    # ✅ Handle standalone numbers like "40" (assumed as Steps)
                    if entry.isdigit():
                        steps_dict["steps"] = int(entry)

            # ✅ Instead of replacing "steps", merge values into metadata
            metadata.update(steps_dict)
            del metadata["steps"]  # ✅ Remove "steps" key after merging

        return metadata



    def extract_metadata(self, image_path):
        """Extract metadata from an image file and save it as a JSON file."""
        _, ext = os.path.splitext(image_path)

        if ext.lower() not in [".jpg", ".jpeg", ".png", ".webp", ".tiff"]:
            #print(f"⏩ Skipping non-image file: {image_path}")
            return {}

        # ✅ First, try to extract metadata from the image file
        metadata = extract_exiftool_metadata(image_path)  # **Primary Extraction (ExifTool)**

        # ✅ If metadata is already extracted, skip text file processing
        if metadata and "Error" in metadata:     
       
            # ✅ If ExifTool failed, try extracting metadata from the `.txt` file
            #print(f"⚠️ ExifTool failed for {image_path}. Trying text file extraction...")
            txt_path = image_path.replace(ext, ".txt")
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as file:
                    text_data = file.read().strip()
                    metadata = PromptFilter.parse_parameters(text_data)  # **Fallback Method**
            else:
                #print(f"❌ No metadata found for {image_path}")
                return {}

        # ✅ Process Positive and Negative Prompts
        metadata = self.process_prompts(metadata)

        # ✅ Process Steps and Key-Value List
        metadata = self.process_steps(metadata)

        # ✅ Fix Hashes & Remove Redundant Entry
        if "Hashes" in metadata:
            try:
                parsed_hashes = json.loads(metadata["Hashes"])  # ✅ Convert JSON string to dict
                metadata["hashes"] = parsed_hashes
            except json.JSONDecodeError:
                print(f"⚠️ Error decoding hashes for {image_path}. Skipping...")

            del metadata["Hashes"]  # ✅ Remove old string-based entry

        # ✅ Save Extracted Metadata to JSON
        json_filename = os.path.splitext(os.path.basename(image_path))[0] + ".json"
        json_path = os.path.join(self.metadata_folder, json_filename) if self.metadata_folder else os.path.join(os.path.dirname(image_path), json_filename)

        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump({"metadata": metadata}, json_file, indent=4)

        #print(f"📄 Metadata saved to: {json_path}")
        return {"metadata": metadata}

