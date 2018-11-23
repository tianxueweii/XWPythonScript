#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-05-21 11:19:55
# @Author  : 382447269@qq.com
# @Version : $1.0.0$

import os
import argparse
import subprocess

PODS_REPO_FILEPATH = '~/.cocoapods/repos'

def func_print_failed(txt):
	print("\033[1;31;43m*** %s ***\033[0m" %txt)

def func_print_schedule(txt):
	print("\033[1;32;40m*** %s ***\033[0m" %txt)

# 比较版本号
def func_version_cmp(a, b):  
    la = a.split('.')  
    lb = b.split('.')  
    f = 0  
    if len(la) > len(lb):  
        f = len(la)  
    else:  
        f = len(lb)  
    for i in range(f):  
        try:  
            if int(la[i]) > int(lb[i]):  
                print(a + '>' + b)  
                return True
            elif int(la[i]) == int(lb[i]):  
                continue  
            else:  
                print(a + '<' + b)  
                return False
        except IndexError as e:  
            if len(la) > len(lb):  
                print(a + '>' + b)  
                return True
            else:  
                print(a + '<' + b)  
                return False
    print(a + '=' + b) 


# 删除目录
def func_remove_dir(path):
	cmd = 'rm' + ' ' + '-rf' + ' ' + path
	sub_process = subprocess.Popen(cmd, shell=True)
	sub_process.communicate()

	export_return_code = sub_process.returncode

	if export_return_code != 0:
		print('Failed remove ' + path)
		return False
	else:
		print('Success remove ' + path)
		return True


def func_formattingVersionFile(path):
	flagPath = '-1'
	
	for file in os.listdir(path):
		
		if file[0:1] is '.':
			continue

		if flagPath is '-1':
			flagPath = file
			# func_print_failed('-1')
		else:
			
			if func_version_cmp(flagPath, file):
				func_remove_dir(os.path.join(path, file))
			else:
				func_remove_dir(os.path.join(path, flagPath))
				flagPath = file

# 格式化Repo
def func_formatting(path):  
	func_print_schedule(path)
	for file in os.listdir(path): 
		file_path = os.path.join(path, file)

		if file[0:1] is '.':
			print(file_path + ' pass...')
		else:
			func_print_schedule(file_path + ' formatting...')
			func_formattingVersionFile(file_path)



# 构建一个新的Repo
def func_getNewsRepo(options):
	
	# 1. 取出项目库内容
	newRepoName = options.repo + '-' + options.version

	cmd = 'cp' + ' ' + '-r' + ' ' + PODS_REPO_FILEPATH + '/' + options.repo + ' ' + './' + newRepoName
	print(cmd)

	sub_process = subprocess.Popen(cmd, shell=True)
	sub_process.communicate()

	export_return_code = sub_process.returncode

	if export_return_code != 0:
		func_print_failed('Failed: copy repo fail !!!')
		return False
	else:
		func_print_schedule('Success: copy success !!!')
		func_formatting('./' + newRepoName)
		return True


##### ##### ##### 入口 ##### ##### ##### 

def func_main():
	
	parser = argparse.ArgumentParser() 

	parser.add_argument('-v', '--version', required=True, help='输入当前封版版本号', metavar="leastVersion")
	parser.add_argument('-r', '--repo', required=True, help='Repo库', metavar="repoUrl")

	options = parser.parse_args()

	# 1. 获取指定Repo copy并更名为 repo-version
	# 2. 遍历Repo中文件夹
	# 3. 遍历组件文件夹，删除并只保留当前最大版本号组件
	func_getNewsRepo(options)

if __name__ == '__main__':
	func_main()