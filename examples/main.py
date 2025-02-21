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

    # Add rename test
    print("✏️ Renaming test files...")
    rename_updates = [
        {"fileKey": upload_results[0].file_key, "newName": "renamed_test.png"},
        {"fileKey": upload_results[1].file_key, "newName": "renamed_test.jpg"},
    ]
    rename_result = api.rename_files(rename_updates)
    print(f"Renamed {len(rename_updates)} files")
    print(f"Success: {rename_result.success}\n")

    # Verify renamed files
    print("📋 Verifying renamed files...")
    updated_files = api.list_files(limit=5)
    print("Current files:")
    for file in updated_files.files:
        print(f"- {file.name}: {file.key}")

    # Verify the new names match what we expected
    expected_names = {"renamed_test.png", "renamed_test.jpg"}
    actual_names = {file.name for file in updated_files.files}
    if expected_names.issubset(actual_names):
        print("✅ Files were renamed successfully!")
    else:
        print("❌ Files were not renamed as expected!")
        print(f"Expected to find: {expected_names}")
        print(f"Found: {actual_names}")
    print()

    # Update ACL test
    print("🔒 Updating ACL settings...")
    acl_updates = [
        {"fileKey": upload_results[0].file_key, "acl": "public-read"},
        {"fileKey": upload_results[1].file_key, "acl": "public-read"},
    ]
    acl_result = api.update_acl(acl_updates)
    print(f"Updated ACL for {len(acl_updates)} files")
    print(f"Success: {acl_result.success}")
    print(f"Updated count: {acl_result.updated_count}\n")

    # Delete the uploaded files
    print("🗑️ Deleting test files...")
    file_keys = [result.file_key for result in upload_results]
    delete_result = api.delete_files(file_keys)
    print(f"Deleted {delete_result.deleted_count} file(s)")
    print(f"Success: {delete_result.success}\n")


if __name__ == "__main__":
    main()
