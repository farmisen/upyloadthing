from io import BytesIO
from typing import List

from upyloadthing import UploadResult, UTApi


def main():
    print("🚀 UploadThing API Demo\n")

    # Initialize the client
    api = UTApi()

    # Get usage info
    print("📊 Getting usage info...")
    usage_info = api.get_usage_info()
    print(f"Total bytes used: {usage_info.total_bytes}")
    print(f"Files uploaded: {usage_info.files_uploaded}")
    print(f"Storage limit: {usage_info.limit_bytes}\n")

    # List files
    print("📋 Listing files...")
    file_list = api.list_files(limit=5)
    print(
        f"Fetched {len(file_list.files)} files, has more: {file_list.has_more}"
    )
    for file in file_list.files:
        print(file)
    print()

    # Prepare test files
    print("📤 Uploading test images...")

    # Prepare PNG file
    with open("./examples/test.png", "rb") as f:
        image_content = f.read()
    png_file = BytesIO(image_content)
    png_file.name = "test.png"

    # Prepare Jpeg file
    with open("./examples/test.jpg", "rb") as f:
        image_content = f.read()
    jpeg_file = BytesIO(image_content)
    jpeg_file.name = "test.jpg"

    # Upload both files
    upload_results: List[UploadResult] = api.upload_files(
        [png_file, jpeg_file], acl="public-read"
    )

    print("Upload results:")
    for result in upload_results:
        print(f"- {result.name}: {result.file_key}")
    print()

    # Delete the uploaded files
    print("🗑️ Deleting test files...")
    file_keys = [result.file_key for result in upload_results]
    delete_result = api.delete_files(file_keys)
    print(f"Deleted {delete_result.deleted_count} file(s)")
    print(f"Success: {delete_result.success}\n")


if __name__ == "__main__":
    main()
