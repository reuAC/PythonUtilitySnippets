# ==============================================================================
# 工具名称: TCP流量转发代理 (TCP_Proxy_Forwarder.py)
# 作用说明: 这是一个轻量级的TCP流量转发工具，可以将特定监听端口接收到的所有TCP连接
#           和数据透明地转发到预设的目标主机和端口。适用于网络调试、本地服务映射
#           或绕过简单网络限制等场景。
#
# 适配Python版本: Python 2.7
# 依赖模块: 无
# ==============================================================================

# -*- coding: utf-8 -*-

import socket
import threading
import select
import sys
import time

# --- 本地测试专用配置 ---
# 本地监听的端口
LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 3307

# 代理目标
REMOTE_HOST = '127.0.0.1'
REMOTE_PORT = 3306 
# -------------------------

BUFFER_SIZE = 4096

def forward_traffic(client_socket, remote_socket, client_address):
    sockets_to_watch = [client_socket, remote_socket]
    
    print "    (D) [%s] 进入双向数据转发循环..." % str(client_address)
    sys.stdout.flush()

    while True:
        try:
            readable, _, exceptional = select.select(sockets_to_watch, [], sockets_to_watch, 180)

            if exceptional:
                print "    (!) [%s] Socket连接异常，关闭." % str(client_address)
                sys.stdout.flush()
                break

            if not readable:
                # print "    (i) [%s] select 超时，继续等待..." % str(client_address)
                # sys.stdout.flush()
                continue
            
            for sock in readable:
                data = sock.recv(BUFFER_SIZE)
                if data:
                    if sock is client_socket:
                        print "    (->) [%s] C->S 转发 %d bytes" % (str(client_address), len(data))
                        sys.stdout.flush()
                        remote_socket.sendall(data)
                    elif sock is remote_socket:
                        print "    (<-) [%s] S->C 转发 %d bytes" % (str(client_address), len(data))
                        sys.stdout.flush()
                        client_socket.sendall(data)
                else:
                    print "    (i) [%s] 检测到一方关闭连接，即将关闭双向通道." % str(client_address)
                    sys.stdout.flush()
                    return
        
        except Exception as e:
            print "    (!) [%s] 转发循环中发生错误: %s" % (str(client_address), e)
            sys.stdout.flush()
            break

def handle_client(client_socket, client_address):
    print "\n(A) 线程启动，处理来自 %s:%d 的新连接" % client_address
    sys.stdout.flush()
    
    remote_socket = None
    try:
        print "(B) [%s] 准备连接到目标数据库 %s:%d..." % (str(client_address), REMOTE_HOST, REMOTE_PORT)
        sys.stdout.flush()
        
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.settimeout(5)
        remote_socket.connect((REMOTE_HOST, REMOTE_PORT))
        
        print "(C) [%s] 成功连接到目标数据库!" % str(client_address)
        sys.stdout.flush()
        
        forward_traffic(client_socket, remote_socket, client_address)

    except socket.timeout:
        print "(!) [%s] 连接目标数据库 %s:%d 超时！请检查目标服务是否正常，端口是否正确。" % (str(client_address), REMOTE_HOST, REMOTE_PORT)
        sys.stdout.flush()
    except socket.error as e:
        print "(!) [%s] 连接目标数据库 %s:%d 失败！错误: %s" % (str(client_address), REMOTE_HOST, REMOTE_PORT, e)
        sys.stdout.flush()
    except Exception as e:
        print "(!) [%s] 处理线程发生未知错误: %s" % (str(client_address), e)
        sys.stdout.flush()
    finally:
        if client_socket:
            client_socket.close()
        if remote_socket:
            remote_socket.close()
        print "(F) [%s] 连接已完全关闭." % str(client_address)
        sys.stdout.flush()

def start_proxy():
    print "(1) 代理服务器准备启动..."
    sys.stdout.flush()
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((LISTEN_HOST, LISTEN_PORT))
        server_socket.listen(10)
        
        print "(2) 代理服务器启动成功! 正在监听 %s:%d" % (LISTEN_HOST, LISTEN_PORT)
        sys.stdout.flush()

    except Exception as e:
        print "(!) 代理服务器启动失败: %s" % e
        sys.stdout.flush()
        sys.exit(1)
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print "\n(3) 接收到新连接，准备创建处理线程..."
            sys.stdout.flush()
            
            proxy_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            proxy_thread.daemon = True
            proxy_thread.start()
        except KeyboardInterrupt:
            print "\n[*] 正在关闭服务器..."
            server_socket.close()
            sys.exit(0)

if __name__ == '__main__':
    start_proxy()