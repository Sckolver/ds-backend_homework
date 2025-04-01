import requests
import logging

class ImageDownloadError(Exception):
    pass


class ImageProviderClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url
        self.timeout = timeout

    def get_image(self, image_id: int) -> bytes:
        url = f"{self.base_url}/images/{image_id}"
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code != 200:
                raise ImageDownloadError(
                    f"Failed to get image {image_id}, status code {response.status_code}"
                )
            return response.content
        except requests.exceptions.RequestException as e:
            logging.error(f"Exception while downloading image {image_id}: {e}")
            raise ImageDownloadError(f"Exception while downloading image {image_id}: {e}")