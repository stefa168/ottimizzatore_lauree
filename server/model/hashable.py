import hashlib


class Hashable:
    def hash(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def hash_data(data) -> str:
        # Ensure the data is in bytes
        if not isinstance(data, bytes):
            data = repr(data).encode('utf-8')
        return hashlib.sha256(data).hexdigest()
