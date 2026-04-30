adb reboot bootloader
# 查看设备是否存在
while true
	do
		./fastboot devices >devices.txt 2>&1
  	fastboot_line1=`cat devices.txt | sed  -n "1p"`
  	echo $fastbootline1
		if [ -n "$fastboot_line1" ];then
			break;
		fi
		echo "fastboot no devices,wait for devices"
		sleep 3s
	done
rm -rf devices.txt
# 查看系统
echo $OSTYPE
if [ $OSTYPE = "cygwin" ]; then
    fastboot_command=fastboot.exe
else
    fastboot_command=fastboot
fi
echo -e "开始执行上锁lock...."
echo -e "等待10秒...."
sleep 10s
./$fastboot_command flashing lock
echo -e "上锁完毕...."