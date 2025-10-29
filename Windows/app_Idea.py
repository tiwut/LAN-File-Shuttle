import sys
import socket
import os
import threading
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QFileDialog,
                             QProgressBar, QTextEdit, QMessageBox, QGroupBox,
                             QListWidget, QListWidgetItem)
from PyQt5.QtCore import QObject, pyqtSignal, QThread, Qt, QTimer
from PyQt5.QtGui import QIntValidator

# --- Konfiguration ---
DEFAULT_PORT = 65432
BUFFER_SIZE = 4096
RECEIVE_DIR = 'received_files'
DISCOVERY_PORT = 50000

def get_local_ip():
    """Ermittelt die lokale IP-Adresse des Computers."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class FileSender(QObject):
    progress_updated = pyqtSignal(int)
    status_message = pyqtSignal(str)
    transfer_complete = pyqtSignal(bool, str)
    speed_updated = pyqtSignal(str)
    next_file_requested = pyqtSignal()

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self._is_running = True
        self.file_queue = []
        self._current_file_path = None
        self._current_file_size = 0
        self._bytes_sent = 0

    def add_file(self, filepath):
        self.file_queue.append(filepath)

    def stop(self):
        self._is_running = False

    def run(self):
        self.status_message.emit("Sende-Worker gestartet. Warte auf Dateien...")
        while self._is_running:
            if not self.file_queue:
                time.sleep(0.1)
                continue

            filepath = self.file_queue.pop(0)
            self._current_file_path = filepath

            if not os.path.exists(self._current_file_path):
                self.transfer_complete.emit(False, f"Fehler: Datei '{self._current_file_path}' nicht gefunden.")
                continue

            self._current_file_size = os.path.getsize(self._current_file_path)
            self._bytes_sent = 0

            resume_file_path = f"{self._current_file_path}.part"
            if os.path.exists(resume_file_path):
                self._bytes_sent = os.path.getsize(resume_file_path)
                self.status_message.emit(f"Wiederaufnahme für {os.path.basename(self._current_file_path)} von {self._bytes_sent} Bytes.")

            self._send_single_file()

            self.next_file_requested.emit()

        self.status_message.emit("Sende-Worker gestoppt.")

    def _send_single_file(self):
        filename = os.path.basename(self._current_file_path)
        self.status_message.emit(f"Verbinde mit {self.host}:{self.port}...")
        start_time = time.time()
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                self.status_message.emit("Verbunden. Sende Metadaten...")

                metadata = f"{filename}|{self._current_file_size}|{self._bytes_sent}".encode('utf-8')
                s.sendall(metadata)
                
                s.settimeout(10)
                confirmation = s.recv(BUFFER_SIZE).decode('utf-8')
                
                if confirmation != "READY":
                    self.transfer_complete.emit(False, "Empfänger nicht bereit oder unerwartete Antwort.")
                    return

                self.status_message.emit(f"Sende Datei: {filename} ({self._current_file_size / (1024*1024):.2f} MB)")

                with open(self._current_file_path, 'rb') as f:
                    if self._bytes_sent > 0:
                        f.seek(self._bytes_sent)

                    while self._is_running:
                        bytes_read = f.read(BUFFER_SIZE)
                        if not bytes_read:
                            break
                        
                        s.sendall(bytes_read)
                        self._bytes_sent += len(bytes_read)
                        progress = int((self._bytes_sent / self._current_file_size) * 100)
                        self.progress_updated.emit(progress)
                        
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed_mbps = (self._bytes_sent / elapsed_time) / (1024*1024)
                            self.speed_updated.emit(f"{speed_mbps:.2f} MB/s")

                if self._is_running:
                    self.transfer_complete.emit(True, f"Datei '{filename}' erfolgreich gesendet!")
                    resume_file_path = f"{self._current_file_path}.part"
                    if os.path.exists(resume_file_path):
                        os.remove(resume_file_path)
                else:
                    self.transfer_complete.emit(False, "Dateiübertragung abgebrochen.")

        except ConnectionRefusedError:
            self.transfer_complete.emit(False, f"Verbindung zu {self.host}:{self.port} verweigert. Ist der Empfänger gestartet?")
        except socket.timeout:
            self.transfer_complete.emit(False, "Verbindungs-Timeout. Empfänger antwortet nicht.")
        except Exception as e:
            self.transfer_complete.emit(False, f"Ein Fehler beim Senden ist aufgetreten: {e}")
        finally:
            self.progress_updated.emit(0)
            self.speed_updated.emit("0.00 MB/s")
            self._current_file_path = None
            self._current_file_size = 0
            self._bytes_sent = 0

class FileReceiver(QObject):
    progress_updated = pyqtSignal(int)
    status_message = pyqtSignal(str)
    transfer_complete = pyqtSignal(bool, str)
    server_started = pyqtSignal(bool, str)
    speed_updated = pyqtSignal(str)

    def __init__(self, host, port, save_dir):
        super().__init__()
        self.host = host
        self.port = port
        self.save_dir = save_dir
        self._is_running = False
        self._server_socket = None

    def run(self):
        os.makedirs(self.save_dir, exist_ok=True)
        self._is_running = True

        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(5)
            self.status_message.emit(f"Warte auf Verbindung auf {self.host}:{self.port}...")
            self.server_started.emit(True, f"Server gestartet auf {self.host}:{self.port}")

            while self._is_running:
                try:
                    self._server_socket.settimeout(1)
                    conn, addr = self._server_socket.accept()
                    with conn:
                        self.status_message.emit(f"Verbunden von {addr}. Empfange Metadaten...")
                        self._handle_client(conn)
                except socket.timeout:
                    pass
                except Exception as e:
                    if self._is_running:
                        self.transfer_complete.emit(False, f"Ein Fehler beim Empfangen ist aufgetreten: {e}")
        except Exception as e:
            self.server_started.emit(False, f"Fehler beim Starten des Servers: {e}")
            self._is_running = False
        finally:
            if self._server_socket:
                self._server_socket.close()
            self.status_message.emit("Empfangs-Server gestoppt.")
            self._is_running = False
            self.progress_updated.emit(0)
            self.speed_updated.emit("0.00 MB/s")

    def _handle_client(self, conn):
        try:
            conn.settimeout(10)
            received = conn.recv(BUFFER_SIZE).decode('utf-8')
            parts = received.split('|')
            filename, filesize_str, bytes_received_str = parts
            filesize = int(filesize_str)
            resume_pos = int(bytes_received_str)

            filepath = os.path.join(self.save_dir, filename)
            write_mode = 'wb'
            current_bytes = 0

            if resume_pos > 0 and os.path.exists(filepath):
                current_bytes = os.path.getsize(filepath)
                if current_bytes == resume_pos:
                    self.status_message.emit(f"Wiederaufnahme-Anfrage für {filename}. Setze bei {current_bytes} Bytes fort.")
                    write_mode = 'ab'
                else:
                    self.status_message.emit(f"Fehler bei Wiederaufnahme für {filename}: Positionen stimmen nicht überein.")
                    conn.sendall("ERROR".encode('utf-8'))
                    return
            
            self.status_message.emit(f"Empfange Datei: {filename} ({filesize / (1024*1024):.2f} MB)")
            conn.sendall("READY".encode('utf-8'))
            
            with open(filepath, write_mode) as f:
                bytes_received = current_bytes
                start_time = time.time()
                
                while bytes_received < filesize and self._is_running:
                    bytes_read = conn.recv(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    
                    f.write(bytes_read)
                    bytes_received += len(bytes_read)
                    
                    progress = int((bytes_received / filesize) * 100)
                    self.progress_updated.emit(progress)
                    
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 0:
                        speed_mbps = (bytes_received - current_bytes) / elapsed_time / (1024*1024)
                        self.speed_updated.emit(f"{speed_mbps:.2f} MB/s")

            if self._is_running and bytes_received == filesize:
                self.transfer_complete.emit(True, f"Datei '{filename}' erfolgreich empfangen!")
                if write_mode == 'ab':
                    os.rename(filepath, os.path.join(self.save_dir, filename))
            elif self._is_running and bytes_received < filesize:
                self.transfer_complete.emit(False, f"Fehler: Verbindung vor Abschluss der Datei '{filename}' getrennt.")
                if bytes_received > 0:
                    os.rename(filepath, f"{filepath}.part")
            else:
                self.transfer_complete.emit(False, "Empfangsvorgang abgebrochen.")
                if os.path.exists(filepath):
                    os.remove(filepath)

        except Exception as e:
            if self._is_running:
                self.transfer_complete.emit(False, f"Ein Fehler beim Empfangen ist aufgetreten: {e}")
        finally:
            self.progress_updated.emit(0)
            self.speed_updated.emit("0.00 MB/s")

    def stop(self):
        self.status_message.emit("Versuche, Empfangs-Server zu stoppen...")
        self._is_running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError as e:
                self.status_message.emit(f"Fehler beim Schließen des Sockets: {e}")

class DeviceDiscovery(QObject):
    device_found = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self._is_running = False

    def run(self):
        self._is_running = True
        self.status_message = "Starte Netzwerk-Erkennung..."

        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(('', DISCOVERY_PORT))

        broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self._is_running:
            # Broadcast "hello" every 5 seconds
            try:
                message = f"LAN_SHUTTLE_DISCOVERY:{DEFAULT_PORT}".encode('utf-8')
                broadcaster.sendto(message, ('<broadcast>', DISCOVERY_PORT))
            except Exception as e:
                self.status_message = f"Fehler beim Broadcast: {e}"

            # Listen for responses for 5 seconds
            listener.settimeout(5)
            try:
                while True:
                    data, addr = listener.recvfrom(1024)
                    ip_address = addr[0]
                    hostname = socket.gethostbyaddr(ip_address)[0] if ip_address != '127.0.0.1' else 'localhost'
                    
                    if data.decode('utf-8') == f"LAN_SHUTTLE_DISCOVERY_RESPONSE:{DEFAULT_PORT}":
                        self.device_found.emit(ip_address, hostname)
            except socket.timeout:
                pass
            except Exception as e:
                self.status_message = f"Fehler beim Lauschen auf Antworten: {e}"

    def stop(self):
        self._is_running = False

class DiscoveryResponseServer(QObject):
    def __init__(self):
        super().__init__()
        self._is_running = False
        self._listener_socket = None
        self.status_message = "Response Server bereit."

    def run(self):
        self._is_running = True
        self._listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self._listener_socket.bind(('', DISCOVERY_PORT))
        except OSError as e:
            self.status_message = f"Konnte nicht auf Discovery-Port binden: {e}"
            self._is_running = False
            return

        while self._is_running:
            self._listener_socket.settimeout(1)
            try:
                data, addr = self._listener_socket.recvfrom(1024)
                if data.decode('utf-8') == f"LAN_SHUTTLE_DISCOVERY:{DEFAULT_PORT}":
                    response = f"LAN_SHUTTLE_DISCOVERY_RESPONSE:{DEFAULT_PORT}".encode('utf-8')
                    self._listener_socket.sendto(response, addr)
            except socket.timeout:
                pass
            except Exception as e:
                self.status_message = f"Fehler im Discovery Response Server: {e}"
                
    def stop(self):
        self._is_running = False
        if self._listener_socket:
            self._listener_socket.close()

class FileTransferApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.sender_thread = None
        self.receiver_thread = None
        self.sender_worker = None
        self.receiver_worker = None
        self.file_queue = []
        self.current_transfer_label = QLabel("Warte auf Übertragung...")
        self.discovered_devices = {}

        os.makedirs(RECEIVE_DIR, exist_ok=True)
        self.receiver_save_path_input.setText(os.path.abspath(RECEIVE_DIR))
        
        # Threads für Discovery und Response Server vorbereiten
        self.discovery_thread = QThread()
        self.discovery_worker = DeviceDiscovery()
        self.discovery_worker.moveToThread(self.discovery_thread)
        self.discovery_worker.device_found.connect(self.add_discovered_device)

        self.response_server_thread = QThread()
        self.response_server_worker = DiscoveryResponseServer()
        self.response_server_worker.moveToThread(self.response_server_thread)
        
        # Threads starten, sobald die GUI sichtbar ist
        QTimer.singleShot(100, self.start_background_threads)

    def start_background_threads(self):
        self.discovery_thread.start()
        self.response_server_thread.start()

    def init_ui(self):
        self.setWindowTitle('Python LAN File Shuttle Pro 🚀')
        self.setGeometry(100, 100, 800, 700)
        
        main_layout = QVBoxLayout()
        
        # --- Sender Sektion ---
        sender_group = QGroupBox("Datei(en) senden")
        sender_layout = QVBoxLayout()

        # Netzwerk-Geräte
        network_layout = QVBoxLayout()
        network_label = QLabel("Gefundene Geräte im Empfangsmodus:")
        self.device_list_widget = QListWidget()
        self.device_list_widget.setMaximumHeight(100)
        self.device_list_widget.itemClicked.connect(self.select_device_from_list)
        network_layout.addWidget(network_label)
        network_layout.addWidget(self.device_list_widget)
        sender_layout.addLayout(network_layout)
        
        # Dateiauswahl
        file_select_layout = QHBoxLayout()
        self.file_list_widget = QListWidget()
        self.file_list_widget.setMaximumHeight(100)
        self.browse_file_button = QPushButton("Datei(en) wählen...")
        self.browse_file_button.clicked.connect(self.browse_files)
        file_select_layout.addWidget(self.file_list_widget)
        file_select_layout.addWidget(self.browse_file_button)
        sender_layout.addLayout(file_select_layout)
        
        # Empfänger IP/Port
        recipient_layout = QHBoxLayout()
        recipient_layout.addWidget(QLabel("Empfänger IP:"))
        self.recipient_ip_input = QLineEdit("127.0.0.1")
        recipient_layout.addWidget(self.recipient_ip_input)
        recipient_layout.addWidget(QLabel("Port:"))
        self.sender_port_input = QLineEdit(str(DEFAULT_PORT))
        self.sender_port_input.setValidator(QIntValidator(1024, 65535))
        recipient_layout.addWidget(self.sender_port_input)
        sender_layout.addLayout(recipient_layout)
        
        # Senden-Button & Fortschritt
        progress_layout_sender = QVBoxLayout()
        self.current_transfer_label = QLabel("Bereit zum Senden.")
        self.sender_speed_label = QLabel("Geschw.: 0.00 MB/s")
        self.sender_progress_bar = QProgressBar()
        self.sender_progress_bar.setValue(0)
        
        progress_layout_sender.addWidget(self.current_transfer_label)
        progress_layout_sender.addWidget(self.sender_speed_label)
        progress_layout_sender.addWidget(self.sender_progress_bar)
        
        self.send_button = QPushButton("Übertragung starten")
        self.send_button.clicked.connect(self.start_sending)
        self.send_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        sender_layout.addLayout(progress_layout_sender)
        sender_layout.addWidget(self.send_button)

        sender_group.setLayout(sender_layout)
        main_layout.addWidget(sender_group)

        # --- Empfänger Sektion ---
        receiver_group = QGroupBox("Datei empfangen")
        receiver_layout = QVBoxLayout()
        
        # Speicherverzeichnis
        save_dir_layout = QHBoxLayout()
        self.receiver_save_path_input = QLineEdit()
        self.receiver_save_path_input.setReadOnly(True)
        self.browse_save_dir_button = QPushButton("Ordner wählen...")
        self.browse_save_dir_button.clicked.connect(self.browse_save_directory)
        save_dir_layout.addWidget(self.receiver_save_path_input)
        save_dir_layout.addWidget(self.browse_save_dir_button)
        receiver_layout.addLayout(save_dir_layout)
        
        # Lausche IP/Port
        listen_layout = QHBoxLayout()
        listen_layout.addWidget(QLabel("Lausche IP:"))
        self.listen_ip_input = QLineEdit("0.0.0.0")
        listen_layout.addWidget(self.listen_ip_input)
        listen_layout.addWidget(QLabel("Port:"))
        self.receiver_port_input = QLineEdit(str(DEFAULT_PORT))
        self.receiver_port_input.setValidator(QIntValidator(1024, 65535))
        listen_layout.addWidget(self.receiver_port_input)
        receiver_layout.addLayout(listen_layout)
        
        # Start/Stop Empfangen Buttons
        receive_buttons_layout = QHBoxLayout()
        self.start_receive_button = QPushButton("Empfang starten")
        self.start_receive_button.clicked.connect(self.start_receiving)
        self.start_receive_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.stop_receive_button = QPushButton("Empfang stoppen")
        self.stop_receive_button.clicked.connect(self.stop_receiving)
        self.stop_receive_button.setEnabled(False)
        self.stop_receive_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        receive_buttons_layout.addWidget(self.start_receive_button)
        receive_buttons_layout.addWidget(self.stop_receive_button)
        receiver_layout.addLayout(receive_buttons_layout)
        
        progress_layout_receiver = QVBoxLayout()
        self.receiver_speed_label = QLabel("Geschw.: 0.00 MB/s")
        self.receiver_progress_bar = QProgressBar()
        self.receiver_progress_bar.setValue(0)
        progress_layout_receiver.addWidget(self.receiver_speed_label)
        progress_layout_receiver.addWidget(self.receiver_progress_bar)
        
        receiver_layout.addLayout(progress_layout_receiver)
        
        receiver_group.setLayout(receiver_layout)
        main_layout.addWidget(receiver_group)
        
        # --- Statusanzeige ---
        status_group = QGroupBox("Status/Logs")
        status_layout = QVBoxLayout()
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setFontPointSize(10)
        status_layout.addWidget(self.status_log)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        self.setLayout(main_layout)
        self.show()

    def add_discovered_device(self, ip, hostname):
        if ip not in self.discovered_devices:
            self.discovered_devices[ip] = hostname
            item = QListWidgetItem(f"{hostname} ({ip})")
            self.device_list_widget.addItem(item)
            self.log_status(f"Discovery: Gerät gefunden: {hostname} ({ip})")

    def select_device_from_list(self, item):
        ip = item.text().split('(')[-1].replace(')', '')
        self.recipient_ip_input.setText(ip)
        self.log_status(f"Ausgewählt: {item.text()}")

    def browse_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Datei(en) zum Senden auswählen")
        if filenames:
            self.file_queue = filenames
            self.file_list_widget.clear()
            for file in filenames:
                self.file_list_widget.addItem(os.path.basename(file))
            self.current_transfer_label.setText(f"{len(self.file_queue)} Datei(en) ausgewählt.")

    def browse_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Verzeichnis zum Speichern auswählen")
        if directory:
            self.receiver_save_path_input.setText(directory)

    def start_sending(self):
        if not self.file_queue:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie mindestens eine Datei zum Senden.")
            return

        recipient_ip = self.recipient_ip_input.text()
        sender_port = int(self.sender_port_input.text())
        
        self.send_button.setEnabled(False)
        self.sender_progress_bar.setValue(0)
        self.log_status("Sender: Starte Übertragung...")
        self.current_transfer_label.setText("Warte auf Übertragung...")

        self.sender_thread = QThread()
        self.sender_worker = FileSender(recipient_ip, sender_port)
        self.sender_worker.moveToThread(self.sender_thread)
        
        for file in self.file_queue:
            self.sender_worker.add_file(file)

        self.sender_worker.progress_updated.connect(self.sender_progress_bar.setValue)
        self.sender_worker.status_message.connect(lambda msg: self.log_status(f"Sender: {msg}"))
        self.sender_worker.transfer_complete.connect(self.on_sender_complete)
        self.sender_worker.speed_updated.connect(self.sender_speed_label.setText)
        self.sender_worker.next_file_requested.connect(self.update_sender_ui)

        self.sender_thread.started.connect(self.sender_worker.run)
        self.sender_thread.start()

    def update_sender_ui(self):
        if self.file_queue:
            next_file = self.file_queue[0]
            self.current_transfer_label.setText(f"Sende: {os.path.basename(next_file)}")
            self.log_status(f"Sender: Starte Übertragung von {os.path.basename(next_file)}...")
            self.file_list_widget.takeItem(0)

    def on_sender_complete(self, success, message):
        self.log_status(f"Sender: {message}")
        if not success:
            QMessageBox.critical(self, "Sende-Fehler", message)
            
        if not self.file_queue:
            self.send_button.setEnabled(True)
            self.log_status("Sender: Alle Dateien erfolgreich gesendet.")
            self.current_transfer_label.setText("Übertragung abgeschlossen.")
            
            if self.sender_thread:
                self.sender_worker.stop()
                self.sender_thread.quit()
                self.sender_thread.wait()
                self.sender_thread = None
                self.sender_worker = None

    def start_receiving(self):
        listen_ip = self.listen_ip_input.text()
        receiver_port = int(self.receiver_port_input.text())
        save_dir = self.receiver_save_path_input.text()

        if not os.path.isdir(save_dir):
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein gültiges Speicherverzeichnis.")
            return

        self.start_receive_button.setEnabled(False)
        self.stop_receive_button.setEnabled(True)
        self.log_status("Empfänger: Starte Server...")
        self.receiver_progress_bar.setValue(0)

        self.receiver_thread = QThread()
        self.receiver_worker = FileReceiver(listen_ip, receiver_port, save_dir)
        self.receiver_worker.moveToThread(self.receiver_thread)

        self.receiver_worker.progress_updated.connect(self.receiver_progress_bar.setValue)
        self.receiver_worker.status_message.connect(lambda msg: self.log_status(f"Empfänger: {msg}"))
        self.receiver_worker.transfer_complete.connect(self.on_receiver_complete)
        self.receiver_worker.server_started.connect(self.on_receiver_server_status)
        self.receiver_worker.speed_updated.connect(self.receiver_speed_label.setText)

        self.receiver_thread.started.connect(self.receiver_worker.run)
        self.receiver_thread.start()

    def on_receiver_server_status(self, started, message):
        self.log_status(f"Empfänger Server Status: {message}")
        if not started:
            self.start_receive_button.setEnabled(True)
            self.stop_receive_button.setEnabled(False)
            QMessageBox.critical(self, "Server Fehler", message)

    def on_receiver_complete(self, success, message):
        self.log_status(f"Empfänger: {message}")
        self.receiver_progress_bar.setValue(0)
        self.receiver_speed_label.setText("Geschw.: 0.00 MB/s")
        if not success:
            QMessageBox.critical(self, "Empfangs-Fehler", message)
        else:
            QMessageBox.information(self, "Empfang abgeschlossen", message)

    def stop_receiving(self):
        if self.receiver_thread and self.receiver_worker:
            self.log_status("Empfänger: Stoppe Server (kann einen Moment dauern)...")
            self.receiver_worker.stop()
            self.receiver_thread.quit()
            self.receiver_thread.wait(5000)
            if self.receiver_thread.isRunning():
                self.receiver_thread.terminate()
                self.log_status("Empfänger: Thread wurde terminiert.")
            self.receiver_thread = None
            self.receiver_worker = None
            self.start_receive_button.setEnabled(True)
            self.stop_receive_button.setEnabled(False)
            self.log_status("Empfänger: Server erfolgreich gestoppt.")
            self.receiver_progress_bar.setValue(0)
            self.receiver_speed_label.setText("Geschw.: 0.00 MB/s")
            
    def log_status(self, message):
        self.status_log.append(message)
        self.status_log.verticalScrollBar().setValue(self.status_log.verticalScrollBar().maximum())

    def closeEvent(self, event):
        if self.sender_worker and self.sender_thread and self.sender_thread.isRunning():
            self.sender_worker.stop()
            self.sender_thread.quit()
            self.sender_thread.wait(2000)
            if self.sender_thread.isRunning():
                self.sender_thread.terminate()

        if self.receiver_worker and self.receiver_thread and self.receiver_thread.isRunning():
            self.receiver_worker.stop()
            self.receiver_thread.quit()
            self.receiver_thread.wait(5000)
            if self.receiver_thread.isRunning():
                self.receiver_thread.terminate()

        if self.discovery_worker and self.discovery_thread and self.discovery_thread.isRunning():
            self.discovery_worker.stop()
            self.discovery_thread.quit()
            self.discovery_thread.wait(2000)
            if self.discovery_thread.isRunning():
                self.discovery_thread.terminate()

        if self.response_server_worker and self.response_server_thread and self.response_server_thread.isRunning():
            self.response_server_worker.stop()
            self.response_server_thread.quit()
            self.response_server_thread.wait(2000)
            if self.response_server_thread.isRunning():
                self.response_server_thread.terminate()

        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileTransferApp()
    sys.exit(app.exec_())