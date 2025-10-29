#!/usr/bin/env python3

import sys
import socket
import os
import threading
import time
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QFileDialog,
                             QProgressBar, QTextEdit, QMessageBox, QGroupBox,
                             QListWidget, QListWidgetItem)
from PyQt5.QtCore import QObject, pyqtSignal, QThread, Qt, QTimer
from PyQt5.QtGui import QIntValidator

# --- Configuration ---
DEFAULT_PORT = 65432
BUFFER_SIZE = 4096
RECEIVE_DIR = 'received_files'
DISCOVERY_PORT = 50000
DISCOVERY_INTERVAL = 3

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_hostname():
    try:
        return socket.gethostname()
    except Exception:
        return "Unknown"

class FileSender(QObject):
    progress_updated = pyqtSignal(int)
    status_message = pyqtSignal(str)
    transfer_complete = pyqtSignal(bool, str)
    speed_updated = pyqtSignal(str)

    def __init__(self, host, port, file_queue):
        super().__init__()
        self.host = host
        self.port = port
        self.file_queue = file_queue.copy()
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        self.status_message.emit("Starting file transfer...")
        
        for i, filepath in enumerate(self.file_queue):
            if not self._is_running:
                break
                
            self.status_message.emit(f"Sending file {i+1}/{len(self.file_queue)}: {os.path.basename(filepath)}")
            success, message = self._send_single_file(filepath)
            
            if not success:
                self.transfer_complete.emit(False, message)
                return
        
        if self._is_running:
            self.transfer_complete.emit(True, "All files sent successfully!")

    def _send_single_file(self, filepath):
        if not os.path.exists(filepath):
            return False, f"File '{filepath}' not found."

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((self.host, self.port))
                
                metadata = json.dumps({
                    'filename': filename,
                    'filesize': filesize
                }).encode('utf-8')
                
                s.sendall(len(metadata).to_bytes(4, 'big'))
                s.sendall(metadata)
                
                confirmation = s.recv(4)
                if confirmation != b'OK':
                    return False, "Receiver not ready."

                bytes_sent = 0
                start_time = time.time()
                
                with open(filepath, 'rb') as f:
                    while bytes_sent < filesize and self._is_running:
                        chunk = f.read(BUFFER_SIZE)
                        if not chunk:
                            break
                        
                        s.sendall(chunk)
                        bytes_sent += len(chunk)
                        
                        progress = int((bytes_sent / filesize) * 100)
                        self.progress_updated.emit(progress)
                        
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed_mbps = (bytes_sent / elapsed_time) / (1024*1024)
                            self.speed_updated.emit(f"{speed_mbps:.2f} MB/s")

                return True, f"File '{filename}' sent successfully!"

        except ConnectionRefusedError:
            return False, f"Connection to {self.host}:{self.port} refused. Is the receiver started?"
        except socket.timeout:
            return False, "Connection timeout. Receiver not responding."
        except Exception as e:
            return False, f"Error while sending: {e}"
        finally:
            self.progress_updated.emit(0)
            self.speed_updated.emit("0.00 MB/s")

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
            
            local_ip = get_local_ip()
            self.server_started.emit(True, f"Server started on {local_ip}:{self.port}")
            self.status_message.emit(f"Waiting for connections on {local_ip}:{self.port}...")

            while self._is_running:
                try:
                    self._server_socket.settimeout(1)
                    conn, addr = self._server_socket.accept()
                    self.status_message.emit(f"Connection from {addr[0]} accepted.")
                    self._handle_client(conn, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._is_running:
                        self.status_message.emit(f"Error accepting connection: {e}")

        except Exception as e:
            self.server_started.emit(False, f"Error starting server: {e}")
        finally:
            if self._server_socket:
                self._server_socket.close()
            self.status_message.emit("Receiver server stopped.")
            self.progress_updated.emit(0)
            self.speed_updated.emit("0.00 MB/s")

    def _handle_client(self, conn, addr):
        try:
            with conn:
                conn.settimeout(30)
                
                metadata_length = int.from_bytes(conn.recv(4), 'big')
                metadata_bytes = conn.recv(metadata_length)
                metadata = json.loads(metadata_bytes.decode('utf-8'))
                
                filename = metadata['filename']
                filesize = metadata['filesize']
                
                filepath = os.path.join(self.save_dir, filename)
                
                conn.sendall(b'OK')
                
                self.status_message.emit(f"Receiving file: {filename} ({filesize / (1024*1024):.2f} MB)")
                
                bytes_received = 0
                start_time = time.time()
                
                with open(filepath, 'wb') as f:
                    while bytes_received < filesize and self._is_running:
                        remaining = min(BUFFER_SIZE, filesize - bytes_received)
                        chunk = conn.recv(remaining)
                        
                        if not chunk:
                            break
                            
                        f.write(chunk)
                        bytes_received += len(chunk)
                        
                        progress = int((bytes_received / filesize) * 100)
                        self.progress_updated.emit(progress)
                        
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed_mbps = (bytes_received / elapsed_time) / (1024*1024)
                            self.speed_updated.emit(f"{speed_mbps:.2f} MB/s")

                if bytes_received == filesize:
                    self.transfer_complete.emit(True, f"File '{filename}' received successfully!")
                else:
                    self.transfer_complete.emit(False, f"Incomplete transfer of '{filename}'")
                    if os.path.exists(filepath):
                        os.remove(filepath)

        except Exception as e:
            self.transfer_complete.emit(False, f"Error while receiving: {e}")
        finally:
            self.progress_updated.emit(0)
            self.speed_updated.emit("0.00 MB/s")

    def stop(self):
        self._is_running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except:
                pass

class DeviceDiscovery(QObject):
    device_found = pyqtSignal(str, str, bool)
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._is_running = False
        self._discovered_devices = {}
        self._last_seen = {}

    def run(self):
        self._is_running = True
        self.status_update.emit("Network Discovery started...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)

        while self._is_running:
            try:
                local_ip = get_local_ip()
                hostname = get_hostname()
                
                discovery_data = {
                    'type': 'DISCOVERY_REQUEST',
                    'sender_ip': local_ip,
                    'sender_hostname': hostname,
                    'timestamp': time.time()
                }
                
                message = json.dumps(discovery_data).encode('utf-8')
                
                # Send broadcast to the local network
                sock.sendto(message, ('<broadcast>', DISCOVERY_PORT))

                current_time = time.time()
                for ip in list(self._last_seen.keys()):
                    if current_time - self._last_seen[ip] > 15: # 15 seconds timeout
                        del self._last_seen[ip]
                        if ip in self._discovered_devices:
                            del self._discovered_devices[ip]

                time.sleep(DISCOVERY_INTERVAL)

            except Exception as e:
                self.status_update.emit(f"Discovery Error: {e}")
                time.sleep(1)

        sock.close()
        self.status_update.emit("Discovery stopped.")

    def stop(self):
        self._is_running = False

class DiscoveryResponseServer(QObject):
    device_discovered = pyqtSignal(str, str, bool)
    status_update = pyqtSignal(str)
    
    def __init__(self, is_receiving_callback):
        super().__init__()
        self._is_running = False
        self.is_receiving_callback = is_receiving_callback

    def run(self):
        self._is_running = True
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('', DISCOVERY_PORT))
            sock.settimeout(1)
            self.status_update.emit("Discovery Response Server started.")
            
            while self._is_running:
                try:
                    data, addr = sock.recvfrom(1024)
                    sender_ip = addr[0]
                    
                    try:
                        discovery_data = json.loads(data.decode('utf-8'))
                        
                        if discovery_data.get('type') == 'DISCOVERY_REQUEST':
                            local_ip = get_local_ip()
                            hostname = get_hostname()
                            
                            response_data = {
                                'type': 'DISCOVERY_RESPONSE',
                                'sender_ip': local_ip,
                                'sender_hostname': hostname,
                                'is_receiving': self.is_receiving_callback(),
                                'timestamp': time.time()
                            }
                            
                            response = json.dumps(response_data).encode('utf-8')
                            sock.sendto(response, addr)
                            
                            if sender_ip != local_ip:
                                sender_hostname = discovery_data.get('sender_hostname', 'Unknown')
                                self.device_discovered.emit(sender_ip, sender_hostname, False)
                        
                        elif discovery_data.get('type') == 'DISCOVERY_RESPONSE':
                            sender_hostname = discovery_data.get('sender_hostname', 'Unknown')
                            is_receiving = discovery_data.get('is_receiving', False)
                            
                            if sender_ip != get_local_ip():
                                self.device_discovered.emit(sender_ip, sender_hostname, is_receiving)
                    
                    except json.JSONDecodeError:
                        pass
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._is_running:
                        self.status_update.emit(f"Response Server Error: {e}")
                        
        except Exception as e:
            self.status_update.emit(f"Could not start Discovery Response Server: {e}")
        finally:
            sock.close()
            self.status_update.emit("Discovery Response Server stopped.")

    def stop(self):
        self._is_running = False

class FileTransferApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        self.sender_thread = None
        self.receiver_thread = None
        self.sender_worker = None
        self.receiver_worker = None
        self.file_queue = []
        self.discovered_devices = {}
        self.is_receiving = False
        
        self.discovery_thread = None
        self.discovery_worker = None
        self.response_server_thread = None
        self.response_server_worker = None
        
        os.makedirs(RECEIVE_DIR, exist_ok=True)
        self.receiver_save_path_input.setText(os.path.abspath(RECEIVE_DIR))
        
        QTimer.singleShot(500, self.start_discovery_system)
        QTimer.singleShot(1000, self.start_receiving) # Automatically start the receiver server
        
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.update_device_list_ui)
        self.ui_update_timer.start(1000)

    def start_discovery_system(self):
        self.discovery_thread = QThread()
        self.discovery_worker = DeviceDiscovery()
        self.discovery_worker.moveToThread(self.discovery_thread)
        
        self.discovery_worker.device_found.connect(self.add_discovered_device)
        self.discovery_worker.status_update.connect(lambda msg: self.log_status(f"Discovery: {msg}"))
        
        self.discovery_thread.started.connect(self.discovery_worker.run)
        self.discovery_thread.start()
        
        self.response_server_thread = QThread()
        self.response_server_worker = DiscoveryResponseServer(lambda: self.is_receiving)
        self.response_server_worker.moveToThread(self.response_server_thread)
        
        self.response_server_worker.device_discovered.connect(self.add_discovered_device)
        self.response_server_worker.status_update.connect(lambda msg: self.log_status(f"Response Server: {msg}"))
        
        self.response_server_thread.started.connect(self.response_server_worker.run)
        self.response_server_thread.start()
        
        self.log_status("Discovery system started - continuously searching for devices...")

    def init_ui(self):
        self.setWindowTitle('Tiwut LAN File Shuttle Pro 🚀')
        self.setGeometry(100, 100, 900, 750)
        
        main_layout = QVBoxLayout()
        
        info_label = QLabel(f"Local IP: {get_local_ip()} | Hostname: {get_hostname()}")
        info_label.setStyleSheet("font-weight: bold; color: #2196F3; padding: 5px;")
        main_layout.addWidget(info_label)
        
        sender_group = QGroupBox("📤 Send File(s)")
        sender_layout = QVBoxLayout()

        network_layout = QVBoxLayout()
        network_label = QLabel("🌐 Available Devices on Network:")
        self.device_list_widget = QListWidget()
        self.device_list_widget.setMaximumHeight(120)
        self.device_list_widget.itemClicked.connect(self.select_device_from_list)
        self.refresh_devices_button = QPushButton("🔄 Refresh Devices")
        self.refresh_devices_button.clicked.connect(self.refresh_devices)
        
        device_button_layout = QHBoxLayout()
        device_button_layout.addWidget(self.device_list_widget)
        device_button_layout.addWidget(self.refresh_devices_button)
        
        network_layout.addWidget(network_label)
        network_layout.addLayout(device_button_layout)
        sender_layout.addLayout(network_layout)
        
        file_select_layout = QVBoxLayout()
        file_select_label = QLabel("📁 Files to Send:")
        self.file_list_widget = QListWidget()
        self.file_list_widget.setMaximumHeight(100)
        
        file_buttons_layout = QHBoxLayout()
        self.browse_file_button = QPushButton("📄 Select File(s)...")
        self.browse_file_button.clicked.connect(self.browse_files)
        self.clear_files_button = QPushButton("🗑️ Clear List")
        self.clear_files_button.clicked.connect(self.clear_files)
        file_buttons_layout.addWidget(self.browse_file_button)
        file_buttons_layout.addWidget(self.clear_files_button)
        
        file_select_layout.addWidget(file_select_label)
        file_select_layout.addWidget(self.file_list_widget)
        file_select_layout.addLayout(file_buttons_layout)
        sender_layout.addLayout(file_select_layout)
        
        recipient_layout = QHBoxLayout()
        recipient_layout.addWidget(QLabel("🎯 Target IP:"))
        self.recipient_ip_input = QLineEdit("192.168.1.100")
        recipient_layout.addWidget(self.recipient_ip_input)
        recipient_layout.addWidget(QLabel("Port:"))
        self.sender_port_input = QLineEdit(str(DEFAULT_PORT))
        self.sender_port_input.setValidator(QIntValidator(1024, 65535))
        recipient_layout.addWidget(self.sender_port_input)
        sender_layout.addLayout(recipient_layout)
        
        self.sender_progress_bar = QProgressBar()
        self.sender_speed_label = QLabel("Speed: 0.00 MB/s")
        
        self.send_button = QPushButton("🚀 Start Transfer")
        self.send_button.clicked.connect(self.start_sending)
        self.send_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        sender_layout.addWidget(self.sender_progress_bar)
        sender_layout.addWidget(self.sender_speed_label)
        sender_layout.addWidget(self.send_button)

        sender_group.setLayout(sender_layout)
        main_layout.addWidget(sender_group)

        receiver_group = QGroupBox("📥 Receive File")
        receiver_layout = QVBoxLayout()
        
        save_dir_layout = QHBoxLayout()
        save_dir_layout.addWidget(QLabel("💾 Save Location:"))
        self.receiver_save_path_input = QLineEdit()
        self.receiver_save_path_input.setReadOnly(True)
        self.browse_save_dir_button = QPushButton("📂 Select Folder...")
        self.browse_save_dir_button.clicked.connect(self.browse_save_directory)
        save_dir_layout.addWidget(self.receiver_save_path_input)
        save_dir_layout.addWidget(self.browse_save_dir_button)
        receiver_layout.addLayout(save_dir_layout)
        
        listen_layout = QHBoxLayout()
        listen_layout.addWidget(QLabel("🔗 Listen IP:"))
        self.listen_ip_input = QLineEdit("0.0.0.0")
        listen_layout.addWidget(self.listen_ip_input)
        listen_layout.addWidget(QLabel("Port:"))
        self.receiver_port_input = QLineEdit(str(DEFAULT_PORT))
        self.receiver_port_input.setValidator(QIntValidator(1024, 65535))
        listen_layout.addWidget(self.receiver_port_input)
        receiver_layout.addLayout(listen_layout)
        
        # The buttons have been removed as per the original logic update
        
        self.receiver_progress_bar = QProgressBar()
        self.receiver_speed_label = QLabel("Speed: 0.00 MB/s")
        receiver_layout.addWidget(self.receiver_progress_bar)
        receiver_layout.addWidget(self.receiver_speed_label)
        
        receiver_group.setLayout(receiver_layout)
        main_layout.addWidget(receiver_group)
        
        status_group = QGroupBox("📋 Status & Logs")
        status_layout = QVBoxLayout()
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(150)
        self.status_log.setStyleSheet("font-family: monospace; font-size: 9pt;")
        
        log_buttons_layout = QHBoxLayout()
        clear_log_button = QPushButton("🧹 Clear Log")
        clear_log_button.clicked.connect(self.status_log.clear)
        log_buttons_layout.addWidget(clear_log_button)
        log_buttons_layout.addStretch()
        
        status_layout.addWidget(self.status_log)
        status_layout.addLayout(log_buttons_layout)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        self.setLayout(main_layout)
        self.log_status("🚀 LAN File Shuttle Pro Started!")
        self.show()

    def add_discovered_device(self, ip, hostname, is_receiving):
        device_key = f"{ip}:{hostname}"
        self.discovered_devices[device_key] = {
            'ip': ip,
            'hostname': hostname,
            'is_receiving': is_receiving,
            'last_seen': time.time()
        }

    def update_device_list_ui(self):
        current_time = time.time()
        
        for key in list(self.discovered_devices.keys()):
            if current_time - self.discovered_devices[key]['last_seen'] > 15: # 15 second timeout
                del self.discovered_devices[key]
        
        self.device_list_widget.clear()
        for device_info in self.discovered_devices.values():
            status_icon = "🟢" if device_info['is_receiving'] else "🔴"
            item_text = f"{status_icon} {device_info['hostname']} ({device_info['ip']})"
            if device_info['is_receiving']:
                item_text += " [Ready to Receive]"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, device_info)
            self.device_list_widget.addItem(item)

    def select_device_from_list(self, item):
        device_info = item.data(Qt.UserRole)
        if device_info:
            self.recipient_ip_input.setText(device_info['ip'])
            self.log_status(f"✅ Device selected: {device_info['hostname']} ({device_info['ip']})")

    def refresh_devices(self):
        self.discovered_devices.clear()
        self.device_list_widget.clear()
        self.log_status("🔄 Refreshing device list...")

    def browse_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Select File(s) to Send")
        if filenames:
            self.file_queue = filenames
            self.file_list_widget.clear()
            total_size = 0
            for filepath in filenames:
                filename = os.path.basename(filepath)
                filesize = os.path.getsize(filepath)
                total_size += filesize
                size_mb = filesize / (1024*1024)
                self.file_list_widget.addItem(f"{filename} ({size_mb:.1f} MB)")
            
            total_size_mb = total_size / (1024*1024)
            self.log_status(f"📁 {len(self.file_queue)} file(s) selected (Total: {total_size_mb:.1f} MB)")

    def clear_files(self):
        self.file_queue.clear()
        self.file_list_widget.clear()
        self.log_status("🗑️ File list cleared")

    def browse_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.receiver_save_path_input.setText(directory)
            self.log_status(f"💾 Save location changed: {directory}")

    def start_sending(self):
        if not self.file_queue:
            QMessageBox.warning(self, "No Files", "Please select at least one file to send.")
            return

        recipient_ip = self.recipient_ip_input.text()
        sender_port = int(self.sender_port_input.text())
        
        if not recipient_ip:
            QMessageBox.warning(self, "No Target IP", "Please enter a target IP address.")
            return
        
        self.send_button.setEnabled(False)
        self.sender_progress_bar.setValue(0)
        self.log_status(f"🚀 Starting transfer of {len(self.file_queue)} file(s) to {recipient_ip}:{sender_port}")

        self.sender_thread = QThread()
        self.sender_worker = FileSender(recipient_ip, sender_port, self.file_queue)
        self.sender_worker.moveToThread(self.sender_thread)

        self.sender_worker.progress_updated.connect(self.sender_progress_bar.setValue)
        self.sender_worker.status_message.connect(lambda msg: self.log_status(f"📤 {msg}"))
        self.sender_worker.transfer_complete.connect(self.on_sender_complete)
        self.sender_worker.speed_updated.connect(lambda speed: self.sender_speed_label.setText(f"Speed: {speed}"))

        self.sender_thread.started.connect(self.sender_worker.run)
        self.sender_thread.start()

    def on_sender_complete(self, success, message):
        self.log_status(f"📤 {message}")
        
        if success:
            QMessageBox.information(self, "Transfer Successful", message)
            self.clear_files()
        else:
            QMessageBox.critical(self, "Transfer Error", message)
            
        self.send_button.setEnabled(True)
        self.sender_progress_bar.setValue(0)
        self.sender_speed_label.setText("Speed: 0.00 MB/s")
        
        if self.sender_thread:
            self.sender_worker.stop()
            self.sender_thread.quit()
            self.sender_thread.wait(3000)
            if self.sender_thread.isRunning():
                self.sender_thread.terminate()
            self.sender_thread = None
            self.sender_worker = None

    def start_receiving(self):
        listen_ip = self.listen_ip_input.text()
        receiver_port = int(self.receiver_port_input.text())
        save_dir = self.receiver_save_path_input.text()

        if not os.path.isdir(save_dir):
            QMessageBox.warning(self, "Invalid Path", "Please select a valid save directory.")
            return

        self.is_receiving = True
        
        self.receiver_progress_bar.setValue(0)
        
        self.log_status(f"📥 Starting receiver server on {listen_ip}:{receiver_port}")

        self.receiver_thread = QThread()
        self.receiver_worker = FileReceiver(listen_ip, receiver_port, save_dir)
        self.receiver_worker.moveToThread(self.receiver_thread)

        self.receiver_worker.progress_updated.connect(self.receiver_progress_bar.setValue)
        self.receiver_worker.status_message.connect(lambda msg: self.log_status(f"📥 {msg}"))
        self.receiver_worker.transfer_complete.connect(self.on_receiver_complete)
        self.receiver_worker.server_started.connect(self.on_receiver_server_status)
        self.receiver_worker.speed_updated.connect(lambda speed: self.receiver_speed_label.setText(f"Speed: {speed}"))

        self.receiver_thread.started.connect(self.receiver_worker.run)
        self.receiver_thread.start()

    def on_receiver_server_status(self, started, message):
        if started:
            self.log_status(f"✅ Server started: {message}")
        else:
            self.log_status(f"❌ Server Error: {message}")
            QMessageBox.critical(self, "Server Error", message)
            # Since the receiver is auto-started, we don't call stop_receiving() here to avoid loops.
            # The server thread will simply end.

    def on_receiver_complete(self, success, message):
        if success:
            self.log_status(f"✅ {message}")
            QMessageBox.information(self, "File Received", message)
        else:
            self.log_status(f"❌ {message}")
            QMessageBox.warning(self, "Reception Error", message)
        
        self.receiver_progress_bar.setValue(0)
        self.receiver_speed_label.setText("Speed: 0.00 MB/s")

    def stop_receiving(self): # This function is kept for manual intervention or future use
        self.is_receiving = False
        
        if self.receiver_thread and self.receiver_worker:
            self.log_status("📥 Stopping receiver server...")
            self.receiver_worker.stop()
            self.receiver_thread.quit()
            self.receiver_thread.wait(5000)
            if self.receiver_thread.isRunning():
                self.receiver_thread.terminate()
                self.log_status("⚠️ Receiver thread forcibly terminated")
            self.receiver_thread = None
            self.receiver_worker = None
        
        self.receiver_progress_bar.setValue(0)
        self.receiver_speed_label.setText("Speed: 0.00 MB/s")
        self.log_status("📥 Receiver server stopped")

    def log_status(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.status_log.append(f"[{timestamp}] {message}")
        self.status_log.verticalScrollBar().setValue(self.status_log.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.log_status("🔄 Exiting application...")
        
        if self.sender_worker and self.sender_thread:
            self.sender_worker.stop()
            self.sender_thread.quit()
            self.sender_thread.wait(2000)
            if self.sender_thread.isRunning():
                self.sender_thread.terminate()

        if self.receiver_worker and self.receiver_thread:
            self.receiver_worker.stop()
            self.receiver_thread.quit()
            self.receiver_thread.wait(3000)
            if self.receiver_thread.isRunning():
                self.receiver_thread.terminate()

        if self.discovery_worker and self.discovery_thread:
            self.discovery_worker.stop()
            self.discovery_thread.quit()
            self.discovery_thread.wait(2000)
            if self.discovery_thread.isRunning():
                self.discovery_thread.terminate()

        if self.response_server_worker and self.response_server_thread:
            self.response_server_worker.stop()
            self.response_server_thread.quit()
            self.response_server_thread.wait(2000)
            if self.response_server_thread.isRunning():
                self.response_server_thread.terminate()

        if hasattr(self, 'ui_update_timer'):
            self.ui_update_timer.stop()

        self.log_status("👋 Application closed")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setApplicationName("LAN File Shuttle Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Tiwut")
    
    try:
        window = FileTransferApp()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
