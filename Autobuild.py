#!/usr/bin/env python
#-*- coding:utf8 -*-

"""iOS auto build   ps:only support workspace build!!!"""

import os
import time
import argparse
import subprocess
import requests
import smtplib

from email.mime.text import MIMEText
from email.header import Header

CONFIGURATION = 'Debug'
ARCHIVE_PATH = './Build/archive.xcarchive'
EXPORT_PATH = './Build'

PGYER_UPLOAD_URL = 'https://www.pgyer.com/apiv2/app/upload'
PGYER_API_KEY = ''
PGYER_DOWNLOAD_BASE_URL = 'http://www.pgyer.com'

SMTP_SERVICE = ''
SMTP_SENDER_EMAIL = ''
SMTP_SENDER_PASSWORD = ''
SMTP_RECEIVER_EMAIL = []

##### ##### ##### 系统 ##### ##### ##### 

def func_printFailed(txt):
	print("\033[1;31;43m*** %s ***\033[0m" %txt)

def func_printSchedule(txt):
	print("\033[1;32;40m*** %s ***\033[0m" %txt)

def func_currentPositionProj():

	files = os.listdir(".")  

	for filename in files:
		portion = os.path.splitext(filename)

		if portion[1] == '.xcworkspace':
			return filename

	return None


##### ##### ##### Cocoapods ##### ##### ##### 
def func_cocoapodsUpdate():
	
	func_printSchedule('pods update ...')
	cmd = 'pod update'

	sub_process = subprocess.Popen(cmd, shell=True)
	sub_process.communicate()

	update_return_code = sub_process.returncode

	if update_return_code != 0:
		func_printFailed('Failed: update fail !!!')
		return False
	else:
		func_printSchedule('Success: update success !!!')
		return True


##### ##### ##### xcodebuild ##### ##### ##### 

#构建
def func_xcodebuild(options):

	#检查ExportOptions
	if os.path.exists('%s' %options.exportOptionsPlist) is False:
		func_printFailed('%s inexistence' %options.exportOptionsPlist)
		return False

	#检查Workspace
	workspaceFileName = func_currentPositionProj()
	if workspaceFileName is None:
		func_printFailed('Failed: workspace cound\'t found !!!')
		return False
	else: 
		return func_xcodeArchiveWorkspace(options)



#编译-workspace
def func_xcodeArchiveWorkspace(options):

	workspace = options.workspace
	scheme = options.scheme
	configuration = options.configuration

	if configuration is None:
		configuration = CONFIGURATION


	#清理
	func_printSchedule('begin clean workspace %s ...' %(workspace))
	cmd = 'xcodebuild clean -workspace %s -scheme %s -configuration %s' %(workspace, scheme, configuration)
	sub_process = subprocess.Popen(cmd, shell=True)
	sub_process.communicate()

	#clean结果处理
	returnCode = sub_process.returncode
	if returnCode != 0:
		func_printFailed('Failed: clean workspace %s failed !!!' %(workspace))
		return False

	#编译
	func_printSchedule('begin archive workspace %s ...' %(workspace))
	cmd = 'xcodebuild -workspace %s -scheme %s -configuration %s archive -archivePath %s' %(workspace, scheme, configuration, ARCHIVE_PATH)
	sub_process = subprocess.Popen(cmd, shell=True)
	sub_process.communicate()

	#编译结果处理
	returnCode = sub_process.returncode
	if returnCode != 0:
		func_printFailed('Failed: archive workspace %s failed !!!' %(workspace))
		return False
	else:
		func_printSchedule('Success: archive workspace %s success !!!' %(workspace))
		#导出ipa包
		return func_ipaExport(options.exportPath, options.exportOptionsPlist)



#导出ipa
def func_ipaExport(exportPath, plist):
	

	if exportPath is None:
		exportPath = EXPORT_PATH

	cmd = 'xcodebuild -exportArchive -archivePath %s -exportPath %s/ipa -exportOptionsPlist %s' %(ARCHIVE_PATH, exportPath, plist)
	func_printSchedule('begin export ipa ...')

	sub_process = subprocess.Popen(cmd, shell=True)
	sub_process.communicate()

	returnCode = sub_process.returncode

	if returnCode != 0:
		func_printFailed('Failed: export fail !!!')
		return False
	else:
		func_printSchedule('Success: export success !!!')
		return True
		


##### ##### ##### SMTP ##### ##### ##### 

def func_smtpSendemail(json):

	#send email to trouble tester
	func_printSchedule('send email to trouble tester ...')
	print('...')
	
	build_name = json['buildName']
	build_version = json['buildBuildVersion']
	downloadUrl = PGYER_DOWNLOAD_BASE_URL + '/' + json['buildShortcutUrl']
	version = json['buildVersion'] 
	dsc = json['buildUpdateDescription']

	txt = '各位同事：\n\n大家好，本次发出是iOS修复bug后的安装包，具体信息如下：\n\n平台：iOS\n版本号：%s\nbuild号：%s\n包下载地址：%s\n\n修复内容：%s' %(version, build_version, downloadUrl, dsc)

	#构建邮件
	username = SMTP_SENDER_EMAIL
	password = SMTP_SENDER_PASSWORD
	

	msg = MIMEText(txt, 'plain', 'utf-8')
	#iOS最新安装包 2017-11-10 build11
	subject = 'iOS'+ '-' + build_name + '-' + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + '-' + 'build' + build_version
	msg['Subject'] = Header(subject, 'utf-8')

	try:
		smtp = smtplib.SMTP()
	
		smtp.connect(SMTP_SERVICE)
		smtp.login(username, password)
		smtp.sendmail(SMTP_SENDER_EMAIL, SMTP_RECEIVER_EMAIL, msg.as_string())

		func_printSchedule('Success: send email success')

	except smtplib.SMTPException:
		func_printFailed('Error: send email fail')
	


##### ##### ##### Pgyer ##### ##### ##### 

def func_pgyerUpload(options):

	func_printSchedule('pgyer uploading ...')

	if options.exportPath is None:
		ipa_path = '%s/ipa/Apps/%s.ipa' %(EXPORT_PATH, options.scheme)
	else:
		ipa_path = '%s/ipa/Apps/%s.ipa' %(options.exportPath, options.scheme)

	if options.updateDescription is None:
		update_description = '%s' %options.scheme
	else:
		update_description = options.updateDescription

	file = {'file': open(ipa_path, 'rb')}
	payload = {'_api_key' : PGYER_API_KEY, 'buildUpdateDescription' : update_description}
	headers = {'enctype':'multipart/form-data'}

	#请求api
	r = requests.post(PGYER_UPLOAD_URL, headers=headers, data=payload, files=file)

	if r.status_code == requests.codes.ok:
		result = r.json()
		resultCode = result['code']
		if resultCode == 0:
			func_printSchedule('Success: upload success')
			downloadUrl = PGYER_DOWNLOAD_BASE_URL + '/' + result['data']['buildShortcutUrl']
			func_printSchedule('DownloadUrl: %s' %(downloadUrl))
			#func_smtpSendemail(result['data'])
		else:
			func_printFailed('UploadFailed:' + result['message'])
	else:
		func_printFailed('Failed: httpError')
	



##### ##### ##### Main ##### ##### ##### 

def func_main():
	
	parser = argparse.ArgumentParser() 
	# 必填
	parser.add_argument('-s', '--scheme', required=True, help='Build the scheme specified by schemename. Required if building a workspace.', metavar="schemename")
	parser.add_argument('-l', '--exportOptionsPlist', required=True, help='Export ipa need a exportOptionsPlist.', metavar='name.plist')
	# 非必填
	parser.add_argument('-c', '--configuration', help='Build with a configuration Debug/Release. Default is Debug')
	parser.add_argument('-w', '--workspace', help='Build the workspace name.xcworkspace.', metavar='name.xcworkspace')
	parser.add_argument('-e', '--exportPath', help='Export ipa need a point path.', metavar='exportpath')
	parser.add_argument('-d', '--updateDescription', help='Upload your ipa to pgyer with description if need', metavar='description')

	options = parser.parse_args()

	if func_cocoapodsUpdate() is False:
	 	return 
	if func_xcodebuild(options) is False:
		return
	func_pgyerUpload(options)
	

if __name__ == '__main__':
	func_main()

    