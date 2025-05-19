import socket
import os


def receive_image(save_dir='E:\\mlsa\\imageod', port=5001):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)  # 如果目录不存在，则创建
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print('等待图片...')
    while True:
        conn, addr = s.accept()
        print('连接自:', addr)
        # 先接收文件名长度和文件名
        name_len = int.from_bytes(conn.recv(2), 'big')
        filename = conn.recv(name_len).decode()
        # 再接收文件大小和内容
        size = int.from_bytes(conn.recv(8), 'big')
        img_data = b''
        while len(img_data) < size:
            packet = conn.recv(4096)
            if not packet:
                break
            img_data += packet
        img_path = os.path.join(save_dir, filename)
        with open(img_path, 'wb') as f:
            f.write(img_data)
        print('图片已保存:', img_path)
        conn.close()


if __name__ == '__main__':
    receive_image()
