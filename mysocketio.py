import socketio
import zlib
import exchange
import os
# 从config库中导入CONFIG类
from config import CONFIG

# 实例化客户端（浏览器）
sio = socketio.Client();
# 配置
gDirIn = CONFIG.inDir;
gDirOut = CONFIG.outDir;
gServer = CONFIG.server; #服务器端
gIsBusy = False;


# 默认事件：与客户端建立好连接(特殊事件，建立连接后自动执行)
@sio.event
def connect():
    print("I'm connected!")
    # 发送给服务器请求消息（事件），注册客户端（将触发服务器端的CONV_REGISTER事件的处理函数）
    sio.emit('CONV_REGISTER', {
        'clientKey': 'a56cb044285e017a329401182ec58578',
        'fileType': ['stp', 'step', 'sldprt', 'sldasm']
    });

# 自定义事件CONV_REGISTER：注册客户端
# 事件处理函数中的参数data来自服务器端发送的消息数据，作用：客户端注册是否成功
@sio.on('CONV_REGISTER')
def on_message(data):
    if data['registerOk']:
        print('register successful')
        return;
    print('register failed');

# 默认事件：与服务器端没有成功建立连接
@sio.event
def connect_error(data):
    print("The connection failed!")


# 默认事件：与服务器端断开连接(特殊事件：与客户端断开连接后自动执行)
# 服务器端的事件处理函数：def on_disconnect(sid):
@sio.event
def disconnect():
    print("I'm disconnected!")
    # 发送给服务器端CONV_DEREGISTER事件，触发其事件处理函数
    sio.emit('CONV_DEREGISTER', {
        'clientKey': 123,
        'fileType': ['stp', 'step']
    });


# 传输响应失败的相关信息给服务器端，msg传递给服务器端失败类型的消息
def response_failure(data, msg):
    # 发送给服务器处理失败的信息
    sio.emit(msg, {
        'fileName': data['fi'] + '.ifc',
        'socketId': data['socketId'],
        'uuid': data['uuid'],
        'fi': data['fi'],
        'userId': data['userId'],
        'convSuccess': False,
        'callbackId': data['callbackId']
    })


# 自定义事件CONV_REQUEST：客户端得到来自服务器端的转格式请求（用户有上传文件的操作）
# data是上传的文件数据
@sio.on('CONV_REQUEST')
def on_message(data):
    global gIsBusy;
    print('I received a message!')
    print(gIsBusy)
    # 判断当前是否进行格式转换
    if gIsBusy:
        response_failure(data, 'CONV_BUSY')
        return;
    gIsBusy = True;
    in_path = gDirIn; # 输入文件的路径
    # 处理来自服务器端的文件，将其创建并保存在本地指定路径
    try:
        # 判断是否存在导入文件的存放目录，如果不存在该目录，则创建
        if not os.path.exists(in_path):
            os.mkdir(in_path)
        # 在指定路径创建本地空白文件，读取方式为二进制写操作
        fp = open(in_path + "\\" + data['fileName'], 'wb');
        if data['zipped']:
            fp.write(zlib.decompress(data['data']));
        else:
            # 在本地将客户端上传的数据写入文件
            fp.write(data['data']);
        fp.close();
        print('create file ' + data['fileName']);
    except Exception as e:
        print(e)
        gIsBusy = False
        response_failure(data, 'CONV_RESPONSE')
        return;

    filename = data['fileName']
    # 输出与文件的路径
    out_path = gDirOut
    # --------------------文件转换
    count = 2
    zippedContent = None
    while count > 0:
        count = count - 1
        try:
            # result = 'F:\\SVN\\convertServer\\exchange\\assetsOut\\kk35-7.ifc'
            # os.getcwd()返回当前工作目录
            # 输入路径 os.getcwd() + "\\" + in_path + "\\"
            # result返回的结果是格式转换完成对应的文件名
            result = exchange.autoexchange(os.getcwd() + "\\" + in_path + "\\", filename, os.getcwd() + "\\" + out_path + "\\")
            if result == -1:
                response_failure(data, 'CONV_RESPONSE')
                gIsBusy = False;
                return
            print("文件转换完成")
            # fp2打开转换完成后的文件对象，以rb二进制格式只读打开文件
            fp2 = open(result, 'rb');
            # print(fp2)
            # 读取文件操作
            content = fp2.read();
            # print(len(content));
            zippedContent = zlib.compress(content);
            # print(len(zippedContent));
            break
        except Exception as e:
            exchange.kill_process('Exchanger')
            print(e)
    # 文件转换完成的后续处理
    if zippedContent == None:
        response_failure(data, 'CONV_RESPONSE')
        gIsBusy = False
        return

    # 客户端群发消息,事件类型是CONV_RESPONSE
    # 消息的内容一部分是响应中的数据文件中的参数，另一部分是压缩完成的文件转换的数据
    sio.emit('CONV_RESPONSE', {
        'fileName': data['fi'] + '.ifc',
        'socketId': data['socketId'],
        'uuid': data['uuid'],
        'fi': data['fi'],
        'convSuccess': True,
        'userId': data['userId'],
        'callbackId': data['callbackId'],
        'zipped': True,
        'data': zippedContent
    });
    # 文件转换完成，取消繁忙状态
    gIsBusy = False
    print('send back')

# ---------------------客户端的事件处理------------

# sio.connect('http://localhost:8092');
# sio.connect('http://47.92.115.234:8090');
# sio.connect('http://192.168.50.185:8092');
# sio.connect('http://192.168.31.138:8092');

# 将客户端与服务器端连接
sio.connect(gServer)
sio.wait()
