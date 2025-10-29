# 🚀 LAN File Shuttle Pro: Application Guide

LAN File Shuttle Pro is a desktop application written in Python that allows you to easily **send and receive files** over a local area network (LAN). It features a simple graphical user interface (GUI) and uses multi-threading to handle transfers in the background, ensuring the application remains responsive.

---

### 💻 Platform Support

This application is designed to be cross-platform and is available for the following operating systems:

*   **Windows**: Installer and standalone executable available.
*   **Linux**: Provided as a `.deb` package for Debian-based distributions (like Ubuntu, Mint).
*   **Tiwut Launcher**: Also accessible for quick launch via the Tiwut Launcher at [https://launcher.tiwut.de/](https://launcher.tiwut.de/).

---

### Key Features

*   **Automatic Receiver**: The application starts the file receiver automatically upon launch, so you don't need to manually click a button to begin listening for files.
*   **Network Discovery**: It automatically scans the network for other devices running the same application, making it easy to find a recipient.
*   **Multi-file Transfer**: Send multiple files in a single transfer session.
*   **Progress and Speed Display**: Monitor the real-time progress and transfer speed of your files.
*   **Logging**: A built-in log panel tracks all application activities, transfers, and network events.

---

### 📝 User Manual

#### A. The Main Interface

The application's window is divided into three main sections: **Send File(s)**, **Receive File**, and **Status & Logs**.

*   **📤 Send File(s)**
    *   **Available Devices on Network**: This list automatically populates with other computers on your network that are running the same application. A green circle indicates a device is ready to receive files.
    *   **Files to Send**: Use the "Select File(s)..." button to browse and add files to your transfer queue. The "Clear List" button removes all files from the queue.
    *   **Target IP**: The IP address of the recipient. You can either type it manually or click on a device from the "Available Devices" list to auto-fill this field.
    *   **Start Transfer**: Click this button to begin sending the files in your queue to the specified target.

*   **📥 Receive File**
    *   **Save Location**: This shows the directory where received files will be saved. You can change this folder by clicking "Select Folder...".
    *   **Listen IP & Port**: These fields show the IP address and port where the application is listening for incoming files. The receiver is **always running automatically** when the application is open.

*   **📋 Status & Logs**
    *   This panel provides a chronological log of all application events, including server startup messages, transfer statuses, and any errors that occur. Use the "Clear Log" button to empty the log panel.

---

#### B. Step-by-Step Instructions

**To Send a File:**
1.  Launch the application.
2.  Wait for the "Available Devices" list to populate.
3.  Click on the device you want to send files to. Its IP address will appear in the **Target IP** field.
4.  Click "Select File(s)..." and choose one or more files from your computer. The files will be added to the "Files to Send" list.
5.  Click the "**Start Transfer**" button. The progress bar will update as the files are sent.
6.  A message box will appear upon completion, indicating success or failure.

**To Receive a File:**
1.  Simply launch the application. The receiver starts automatically.
2.  Ensure your firewall is not blocking the application's port (default is 65432).
3.  Instruct the sender to launch the application, select your device from their list, and send the files.
4.  The received files will be automatically saved to the folder specified in the **Save Location** field.
