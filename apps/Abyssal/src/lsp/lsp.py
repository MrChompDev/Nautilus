import asyncio
import json
import socket
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LSPPosition:
    line: int  # 0-based
    character: int  # 0-based

    def to_dict(self) -> dict:
        return {"line": self.line, "character": self.character}

    @classmethod
    def from_dict(cls, data: dict) -> 'LSPPosition':
        return cls(data.get("line", 0), data.get("character", 0))


@dataclass
class LSPLocation:
    uri: str
    range: Any = None
    language_id: str = None
    version: int = None

    def to_dict(self) -> dict:
        result = {"uri": self.uri}
        if self.range:
            result["range"] = self.range
        if self.language_id:
            result["languageId"] = self.language_id
        if self.version is not None:
            result["version"] = self.version
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'LSPLocation':
        return cls(
            uri=data.get("uri", ""),
            range=data.get("range"),
            language_id=data.get("languageId"),
            version=data.get("version")
        )


@dataclass
class LSPCompletionItem:
    label: str
    kind: int = 1  # Text
    detail: str | None = None
    documentation: str | None = None
    sort_text: str | None = None
    insert_text: str | None = None
    text_edit: Any | None = None
    data: Any | None = None

    def to_dict(self) -> dict:
        result = {
            "label": self.label,
            "kind": self.kind,
        }
        if self.detail:
            result["detail"] = self.detail
        if self.documentation:
            result["documentation"] = self.documentation
        if self.sort_text:
            result["sortText"] = self.sort_text
        if self.insert_text:
            result["insertText"] = self.insert_text
        if self.text_edit:
            result["textEdit"] = self.text_edit
        if self.data:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'LSPCompletionItem':
        return cls(
            label=data.get("label", ""),
            kind=data.get("kind", 1),
            detail=data.get("detail"),
            documentation=data.get("documentation"),
            sort_text=data.get("sortText"),
            insert_text=data.get("insertText"),
            text_edit=data.get("textEdit"),
            data=data.get("data")
        )


@dataclass
class LSPHover:
    contents: Any
    range: Any | None = None

    def to_dict(self) -> dict:
        result = {
            "contents": self.contents
        }
        if self.range:
            result["range"] = self.range
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'LSPHover':
        return cls(
            contents=data.get("contents"),
            range=data.get("range")
        )


@dataclass
class LSPSymbolInformation:
    name: str
    kind: int = 0
    location: LSPLocation | None = None
    container_name: str | None = None

    def to_dict(self) -> dict:
        result = {
            "name": self.name,
            "kind": self.kind,
        }
        if self.location:
            result["location"] = self.location.to_dict()
        if self.container_name:
            result["containerName"] = self.container_name
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'LSPSymbolInformation':
        return cls(
            name=data.get("name", ""),
            kind=data.get("kind", 0),
            location=LSPLocation.from_dict(data.get("location", {})) if data.get("location") else None,
            container_name=data.get("containerName")
        )


@dataclass
class LSPLocationLink:
    origin_location: LSPLocation
    target_uri: str
    target_range: Any
    target_selection_range: Any
    origin_selection_range: Any = None

    def to_dict(self) -> dict:
        result = {
            "originSelectionRange": self.origin_selection_range.to_dict() if self.origin_selection_range else None,
            "targetUri": self.target_uri,
            "targetRange": self.target_range.to_dict() if self.target_range else None,
            "targetSelectionRange": self.target_selection_range.to_dict() if self.target_selection_range else None,
        }
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'LSPLocationLink':
        return cls(
            origin_location=LSPLocation.from_dict(data.get("originLocation", {})),
            target_uri=data.get("targetUri", ""),
            target_range=data.get("targetRange"),
            target_selection_range=data.get("targetSelectionRange"),
            origin_selection_range=data.get("originSelectionRange")
        )


class LSPMessage:
    def __init__(self, msg_id: str | None, method: str, params: Any | None = None):
        self.id = msg_id
        self.method = method
        self.params = params
        self._jsonrpc = "2.0"

    def to_dict(self) -> dict:
        result = {
            "jsonrpc": self._jsonrpc,
            "method": self.method
        }
        if self.id is not None:
            result["id"] = self.id
        if self.params is not None:
            result["params"] = self.params
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'LSPMessage':
        msg_id = data.get("id")
        if msg_id is not None:
            msg_id = str(msg_id)
        return cls(msg_id=msg_id, method=data.get("method", ""), params=data.get("params"))

    def is_request(self) -> bool:
        return self.id is not None

    def is_response(self) -> bool:
        return isinstance(self.id, str) and "response" in self.method.lower()


class LSPStream(ABC):
    @abstractmethod
    def write(self, data: str):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def is_closed(self) -> bool:
        pass

    @abstractmethod
    def read_line(self) -> str:
        pass

    @abstractmethod
    async def async_read_line(self) -> str:
        pass


class TCPLSPStream(LSPStream):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.reader_thread = None
        self.message_queue = []
        self._closed = False
        self._connected = False
        self._lock = threading.Lock()

    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self._connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to LSP server: {e}")
            return False

    def write(self, data: str):
        with self._lock:
            if self.socket and self._connected:
                try:
                    self.socket.sendall(data.encode('utf-8'))
                except Exception as e:
                    print(f"Error writing to LSP stream: {e}")
                    self._connected = False

    def close(self):
        self._closed = True
        with self._lock:
            if self.socket:
                self.socket.close()
                self.socket = None
                self._connected = False

    def is_closed(self) -> bool:
        return self._closed

    def read_line(self) -> str:
        with self._lock:
            if not self.socket or not self._connected:
                return ""
            try:
                self.socket.settimeout(1.0)
                data = self.socket.recv(4096)
                if not data:
                    self._connected = False
                    return ""
                return data.decode('utf-8')
            except Exception:
                return ""

    async def async_read_line(self) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_line)


class LSPConnection:
    def __init__(self, stream: LSPStream, handler: 'LSPHandler'):
        self.stream = stream
        self.handler = handler
        self.message_queue = []
        self.next_id = 1
        self._reader_thread = None
        self._closed = False
        self._send_lock = threading.Lock()

    def start(self):
        if not self.stream.is_closed() and not self.stream.connect():
            raise ConnectionError("Failed to connect to LSP server")

        self._reader_thread = threading.Thread(target=self._read_messages)
        self._reader_thread.daemon = True
        self._reader_thread.start()

    def send_request(self, method: str, params: Any | None = None) -> Any:
        msg_id = str(self.next_id)
        self.next_id += 1
        message = LSPMessage(msg_id, method, params)
        response = self._send_message_with_response(message)
        return response

    def send_notification(self, method: str, params: Any | None = None):
        message = LSPMessage(None, method, params)
        self._send_message(message)

    def _send_message(self, message: LSPMessage):
        with self._send_lock:
            data = json.dumps(message.to_dict()) + '\n'
            self.stream.write(data)

    def _send_message_with_response(self, message: LSPMessage) -> Any:
        with self._send_lock:
            data = json.dumps(message.to_dict()) + '\n'
            self.stream.write(data)
            return self._get_response(message.id)

    def _read_messages(self):
        while not self._closed:
            line = self.stream.read_line()
            if not line:
                continue

            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                self.handler.handle_message(data)
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error processing LSP message: {e}")

    def _get_response(self, msg_id: str, timeout: float = 10.0) -> Any:
        start_time = time.time()
        while time.time() - start_time < timeout:
            for msg in self.message_queue:
                if msg.get("id") == msg_id and "result" in msg:
                    return msg["result"]
            time.sleep(0.1)
        
        raise TimeoutError(f"No response received for request {msg_id}")

    def close(self):
        self._closed = True
        self.stream.close()
        if self._reader_thread:
            self._reader_thread.join(timeout=5.0)


class LSPHandler(ABC):
    @abstractmethod
    def on_initialize(self, params: dict, info: dict) -> dict:
        pass

    @abstractmethod
    def on_shutdown(self, params: dict) -> dict:
        pass

    @abstractmethod
    def on_completion(self, params: dict) -> dict:
        pass

    @abstractmethod
    def on_hover(self, params: dict) -> dict:
        pass

    @abstractmethod
    def on_definition(self, params: dict) -> dict:
        pass

    @abstractmethod
    def on_symbol(self, params: dict) -> dict:
        pass

    def on_open_document(self, params: dict) -> dict:
        return {}

    def on_change_document(self, params: dict) -> dict:
        return {}

    def on_close_document(self, params: dict) -> dict:
        return {}
