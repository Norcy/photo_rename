#!/usr/bin/env python
# -*- coding: utf-8 -*-  

'''
1. 根据照片创建时间来重命名照片，使用的是目前发现最准的方法，mdls 命令，经测试 stat/GetFileInfo/exifread/sips 这些命令都不准
2. iPhone 导出的照片中可能会有 .png/.jpg/.jpeg 和重名的 .heic，一般照片经过编辑之后原件就会变成 .heic
这个脚本的 deleteDuplicate 就是删除这些同名的 .heic
3. 支持文件夹嵌套
'''

import os
import time
import sys
from subprocess import Popen, PIPE


MY_DATE_FORMAT = '%Y-%m-%d_%H%M%S'
MY_DATE_FORMAT_REPEAT = '%Y-%m-%d_%H%M%S_%f'
SUFFIX_FILTER = ['.jpg','.png','.mpg','.mp4','.thm','.bmp','.jpeg',\
'.avi','.mov', '.gif', '.heic']
# 可能与 heic 重复的
HEIC_DUPLICATE_FILTER = ['.jpg','.png', '.jpeg', '.gif', '.heic']
DELETE_FILES = ['thumbs.db','sample.dat']
FILENAME_DIC = {}

def isFormatedFileName(filename):
    '判断是否已经是格式化过的文件名'
    return False
    try:
        filename_nopath = os.path.basename(filename)
        f,e = os.path.splitext(filename_nopath)
        time.strptime(f, MY_DATE_FORMAT)
        return True
    except ValueError:
        try:
            time.strptime(f, MY_DATE_FORMAT_REPEAT)
            return True
        except ValueError:
            return False
        
def isTargetedFileType(filename):
    '根据文件扩展名，判断是否是需要处理的文件类型'
    filename_nopath = os.path.basename(filename)
    f,e = os.path.splitext(filename_nopath)
    if e.lower() in SUFFIX_FILTER:
        return True
    else:
        return False    

def isDeleteFile(filename):
    '判断是否是指定要删除的文件'
    filename_nopath = os.path.basename(filename)
    f,e = os.path.splitext(filename_nopath)
    if e.lower() == ".heic":
        for fType in HEIC_DUPLICATE_FILTER:
            if os.path.exists(f+fType):
                return True
        return False   
        
def generateNewFileName(filename):
    '根据照片的拍照时间生成新的文件名（如果获取不到拍照时间，则使用文件的创建时间）'
    try:
        if os.path.isfile(filename):
            fd = open(filename, 'rb')
        else:
            raise "[%s] is not a file!\n" % filename
    except:
        raise "unopen file[%s]\n" % filename
        
    dateStr = ""

    # 方法 1
    #data = exifread.process_file(fd)
    #t = data['Image DateTime']
    #转换成 yyyy-mm-dd_hhmmss的格式
    #dateStr = str(t).replace(":","-")[:10] + "_" + str(t)[11:].replace(":","")

    # 方法 2
    # state = os.stat(filename)
    # dateStr = time.strftime("%Y-%m-%d_%H%M%S", time.localtime(state[-2]))

    # 方法 3
    '''
    p = Popen(['GetFileInfo', '-d', filename], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    output = p.stdout.read().decode('utf-8')
    array = str(output)[:10].split('/')
    prefix = array[2] + '-' + array[0] + '-' + array[1]
    dateStr = prefix + "_" + str(output)[11:].replace(":","")
    '''

    # 方法 4
    p = Popen(['mdls', '-raw', '-name', 'kMDItemContentCreationDate', filename], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    output = p.stdout.read().decode('utf-8')
    output = output.replace('\n', '')
    createTime = output
    print(createTime)
    p = Popen(['date', '-f', r'%F %T %z', '-j', createTime, r'+%Y-%m-%d_%H%M%S'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    dateStr = p.stdout.read().decode('utf-8')
 
    
    dateStr = dateStr.replace('\n', '')
    dateStr = dateStr.replace('\r', '')
    dirname = os.path.dirname(filename)
    filename_nopath = os.path.basename(filename)
    f,e = os.path.splitext(filename_nopath)
    newFileName = os.path.join(dirname, dateStr + e).lower()
    while os.path.exists(newFileName) and newFileName != filename:
        if newFileName in FILENAME_DIC:
            FILENAME_DIC[newFileName] += 1
        else:
            FILENAME_DIC[newFileName] = 1
        oldFileName = newFileName
        newFileName = os.path.join(dirname, dateStr + "_" + str(FILENAME_DIC[newFileName]) + e).lower()
        print("命名重复 {} -> {}，再次重命名为 {}".format(filename, oldFileName, newFileName))

    return newFileName
    

def scandir(startdir):
    os.chdir(startdir)
    for obj in os.listdir(os.curdir) :
        if os.path.isfile(obj):
            if isTargetedFileType(obj) and isFormatedFileName(obj) == False:
                #对满足过滤条件的文件进行改名处理
                newFileName = generateNewFileName(obj)
                # print("rename [%s] => [%s]" % (obj, newFileName))
                os.rename(obj, newFileName)

        if os.path.isdir(obj):
            scandir(obj)
            os.chdir(os.pardir)
    
def deleteDuplicate(startdir):
    os.chdir(startdir)
    for obj in os.listdir(os.curdir) :
        if os.path.isfile(obj):
            if isDeleteFile(obj):
                #删除指定的文件
                print("delete [%s]: " % obj)
                os.remove(obj)

        if os.path.isdir(obj):
            deleteDuplicate(obj)
            os.chdir(os.pardir)

if __name__ == "__main__":
    curPath = sys.argv[1]
    scandir(curPath)
    os.chdir(curPath)
    deleteDuplicate(curPath)