from scripts.cs import CustomSorter

if __name__ == "__main__":
    # Initialize the sorter with the test configuration
    sorter = CustomSorter("custom_sorter_config.yaml")

    # Run the sorting process
    sorter.sort_images_and_texts()

    print("Sorting process completed for test folder")
