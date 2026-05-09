import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    visible: true
    width: 900
    height: 700
    title: "LAN Shuttle Pro"
    
    Material.theme: Material.System
    Material.accent: Material.Blue

    FileDialog {
        id: fileDialog
        title: "Select Files to Send"
        fileMode: FileDialog.OpenFiles
        onAccepted: {
            webServer.startSharing(currentFiles)
        }
    }

    RowLayout {
        anchors.fill: parent
        
        Rectangle {
            Layout.preferredWidth: 250
            Layout.fillHeight: true
            color: Material.dialogColor
            
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 20
                
                Text {
                    text: "📱 Web & QR Share"
                    font.pixelSize: 20
                    font.bold: true
                    color: Material.foreground
                }
                
                Image {
                    source: webServer.qrCodeImage !== "" ? webServer.qrCodeImage : ""
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 200
                    visible: webServer.serverUrl !== ""
                }
                
                Text {
                    text: webServer.serverUrl
                    color: Material.accentColor
                    font.pixelSize: 14
                    visible: webServer.serverUrl !== ""
                }

                Button {
                    text: "Select Files to Share"
                    highlighted: true
                    onClicked: fileDialog.open()
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
                    text: "🔒 Secure App-to-App Transfer"
                    font.pixelSize: 24
                    font.bold: true
                    color: Material.foreground
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
                            transferEngine.sendFileSecurely(modelData.ip, 65432, "/path/to/file.mp4")
                        }
                    }
                }
                
                Text {
                    text: "Looking for devices on your network..."
                    color: "gray"
                    visible: deviceList.count === 0
                    Layout.alignment: Qt.AlignHCenter
                }

                ProgressBar {
                    Layout.fillWidth: true
                    value: transferEngine.progress / 100.0
                }
                Text {
                    text: transferEngine.speed + " MB/s | Encrypted TLS 1.3 🔒"
                    color: "gray"
                }
            }
        }
    }
}
