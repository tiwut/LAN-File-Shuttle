import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    visible: true
    width: 900
    height: 700
    title: "LAN Shuttle Pro"
    
    Material.theme: Material.Dark
    Material.accent: Material.Blue

    property string selectedTargetIp: ""

    Connections {
        target: receiveEngine
        function onIncomingTransfer(fileName, fileSize) {
            saveFolderDialog.title = "Save incoming file: " + fileName + " (" + (fileSize / 1024 / 1024).toFixed(2) + " MB)"
            saveFolderDialog.open()
        }
    }

    FolderDialog {
        id: saveFolderDialog
        onAccepted: {
            var folderUrl = currentFolder.toString()
            if (!folderUrl.endsWith("/")) folderUrl += "/"
            
            var fullSavePath = folderUrl + receiveEngine.currentFileName
            receiveEngine.acceptTransfer(fullSavePath)
        }
        onRejected: {
            receiveEngine.rejectTransfer()
        }
    }

    FileDialog {
        id: directTransferDialog
        title: "Select File to Send"
        fileMode: FileDialog.OpenFile
        onAccepted: {
            var realPath = currentFile.toString().replace("file://", "")
            transferEngine.sendFileSecurely(selectedTargetIp, 65432, realPath)
        }
    }

    FileDialog {
        id: webFileDialog
        title: "Select Files for Web Share"
        fileMode: FileDialog.OpenFiles
        onAccepted: {
            var fileList = []
            for (var i = 0; i < currentFiles.length; i++) {
                fileList.push(currentFiles[i].toString())
            }
            webServer.startSharing(fileList) 
        }
    }

    RowLayout {
        anchors.fill: parent
        
        Rectangle {
            Layout.preferredWidth: 320
            Layout.fillHeight: true
            color: Material.dialogColor
            
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 20
                
                Text {
                    text: "📱 Web & QR Share"
                    font.pixelSize: 20
                    font.bold: true
                    color: "white"
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Image {
                    source: webServer.qrCodeImage
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 200
                    visible: webServer.serverUrl !== ""
                    fillMode: Image.PreserveAspectFit
                }
                
                Text {
                    text: webServer.serverUrl
                    color: Material.accentColor
                    font.pixelSize: 16
                    font.bold: true
                    visible: webServer.serverUrl !== ""
                    Layout.alignment: Qt.AlignHCenter
                }

                Button {
                    text: webServer.serverUrl === "" ? "📂 Select Files & Start Web" : "🛑 Stop Sharing"
                    highlighted: true
                    Layout.alignment: Qt.AlignHCenter
                    onClicked: {
                        if (webServer.serverUrl === "") {
                            webFileDialog.open()
                        } else {
                            webServer.stopSharing()
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Material.backgroundColor
            
            ColumnLayout {
                anchors.margins: 40
                anchors.fill: parent
                spacing: 20

                Text {
                    text: "📡 Send to Devices"
                    font.pixelSize: 24
                    font.bold: true
                    color: "white"
                }

                ListView {
                    id: deviceList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: discoveryService.activeDevices
                    
                    delegate: ItemDelegate {
                        text: "💻 " + modelData.hostname + "  (" + modelData.ip + ")"
                        width: parent.width
                        font.pixelSize: 16
                        onClicked: {
                            selectedTargetIp = modelData.ip
                            directTransferDialog.open() 
                        }
                    }
                }

                Text {
                    text: "Scanning for nearby devices..."
                    color: "gray"
                    visible: deviceList.count === 0
                }

                Text { text: "📤 Sending Progress:"; color: "white"; visible: transferEngine.progress > 0 }
                ProgressBar {
                    Layout.fillWidth: true
                    value: transferEngine.progress / 100.0
                    visible: transferEngine.progress > 0
                }

                Text { 
                    text: "📥 Receiving: " + receiveEngine.currentFileName
                    color: "white"
                    visible: receiveEngine.receiveProgress > 0 && receiveEngine.receiveProgress < 100
                }
                ProgressBar {
                    Layout.fillWidth: true
                    value: receiveEngine.receiveProgress / 100.0
                    visible: receiveEngine.receiveProgress > 0 && receiveEngine.receiveProgress < 100
                    Material.accent: Material.Green
                }
            }
        }
    }
}
