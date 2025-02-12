import hashlib
import hmac
import time
from urllib.parse import urlencode


def make_presigned_url(
    region_alias: str,
    file_key: str,
    api_key: str,
    app_id: str,
    file_name: str,
    file_size: int,
    file_type: str | None = None,
    custom_id: str | None = None,
    content_disposition: str | None = "inline",
    acl: str | None = "public-read",
) -> str:
    """
    Constructs a pre-signed URL for uploading a file.

    This function creates a URL with signed query parameters for a file upload.
    It includes required and optional parameters, calculates an expiration
    time, encodes the URL, and appends an HMAC-SHA256 signature to ensure
    secure access to the upload endpoint.

    Args:
        region_alias (str): The region alias to be used in the URL (e.g.,
                            "us-east"). This is a subdomain for the base URL.
        file_key (str): The unique file key or identifier used in the URL path.
        api_key (str): The API key used to generate the HMAC-SHA256 signature.
        app_id (str): The application identifier.
        file_name (str): The name of the file being uploaded.
        file_size (int): The size of the file in bytes.
        file_type (str | None, optional): The MIME type of the file.
        custom_id (str | None, optional): An optional custom identifier for
        the file.
        content_disposition (str | None, optional): Content disposition
        directive.
        acl (str | None, optional): Access control list setting for the file.


    Returns:
        str: A fully constructed pre-signed URL including the signature that
        can be used to securely upload the file.
    """
    expires = int(time.time() * 1000) + 60 * 60 * 1000  # 1 hour from now
    params = {
        "expires": expires,
        "x-ut-identifier": app_id,
        "x-ut-file-name": file_name,
        "x-ut-file-size": file_size,
    }

    # Optional parameters: add if provided
    if file_type:
        params["x-ut-file-type"] = file_type
    if custom_id:
        params["x-ut-custom-id"] = custom_id
    if content_disposition:
        params["x-ut-content-disposition"] = content_disposition
    if acl:
        params["x-ut-acl"] = acl

    # Construct the base URL.
    base_url = f"https://{region_alias}.ingest.uploadthing.com/{file_key}"

    # Encode the parameters.
    encoded_params = urlencode(params)

    # Construct the URL with parameters.
    url = f"{base_url}?{encoded_params}"

    # Calculate the signature using HMAC-SHA256.
    signature = hmac_sha256(url, api_key)

    # Append the signature to the URL.
    url_with_signature = f"{url}&signature={signature}"

    return url_with_signature


def hmac_sha256(url: str, api_key: str) -> str:
    """
    Calculates the HMAC-SHA256 signature of the given URL.

    This function takes the URL and an API key, then returns a signature
    string in the format required by UploadThing.

    Args:
        url (str): The URL string to be signed.
        api_key (str): The secret API key used to generate the HMAC signature.

    Returns:
        str: A string containing the HMAC-SHA256 signature prefixed with
             "hmac-sha256=".
    """
    message = url.encode("utf-8")
    secret = api_key.encode("utf-8")
    hmac_obj = hmac.new(secret, message, hashlib.sha256)
    signature = hmac_obj.hexdigest()
    return f"hmac-sha256={signature}"
