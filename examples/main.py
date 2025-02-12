from io import BytesIO

from upyloadthing.client import UTApi
from upyloadthing.schemas import UploadResult


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

    # Upload an image file
    print("📤 Uploading test image...")
    with open("./examples/test.png", "rb") as f:
        image_content = f.read()
    image_file = BytesIO(image_content)
    image_file.name = "test.png"
    upload_result: UploadResult = api.upload_files(
        image_file, acl="public-read"
    )  # type: ignore
    file_key = upload_result.url.split("/")[-1]
    print(f"File uploaded with result: {upload_result}\n")

    # Delete the uploaded file
    print("🗑️ Deleting test file...")
    delete_result = api.delete_files(file_key)
    print(f"Deleted {delete_result.deleted_count} file(s)")
    print(f"Success: {delete_result.success}\n")


if __name__ == "__main__":
    main()
