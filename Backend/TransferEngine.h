#pragma once
#include <QObject>
#include <QSslSocket>
#include <QFile>

class TransferEngine : public QObject {
    Q_OBJECT
    Q_PROPERTY(int progress READ progress NOTIFY progressChanged)
    Q_PROPERTY(QString speed READ speed NOTIFY speedChanged)

public:
    explicit TransferEngine(QObject *parent = nullptr);
    
    Q_INVOKABLE void sendFileSecurely(const QString& ip, int port, const QString& filePath);
    
    int progress() const;
    QString speed() const;

signals:
    void progressChanged();
    void speedChanged();
    void transferComplete(bool success, QString message);

private slots:
    void onEncrypted();
    void writeNextChunk();

private:
    QSslSocket* m_socket;
    QFile* m_currentFile;
    qint64 m_bytesSent;
    qint64 m_totalBytes;
    int m_progress = 0;
    QString m_speed = "0.00";
};
