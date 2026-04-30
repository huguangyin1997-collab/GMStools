sn="";

adb root && adb reboot bootloader

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
	
echo $OSTYPE

if [ $OSTYPE = "cygwin" ]; then
    fastboot_command=fastboot.exe
else
    fastboot_command=fastboot
fi

./$fastboot_command oem get_identifier_token &> temp.txt

sed -i 's/\r//g' temp.txt
sed -i '/OKAY/d' temp.txt
sed -i '/finished/d' temp.txt
sed -i '/^$/d' temp.txt
sed -i 's/(bootloader) //g' temp.txt
sed -i 's/Identifier token://g' temp.txt
sed -i '1d' temp.txt

for line in `cat temp.txt`; do
sn="${sn}${line}"
done

./signidentifier_unlockbootloader.sh ${sn%Finished*} rsa4096_vbmeta-T610.pem sign.bin
echo output sign.bin

echo press volume button to continue...

./$fastboot_command flashing unlock_bootloader sign.bin

rm temp.txt 2>/dev/null
#rm signature.bin 2>/dev/null