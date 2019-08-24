# 简介
Device_Tracer https://www.home-assistant.io/components/device_tracker/ 主要的功能是判断人是否在家和追踪GPS设备的位置，这两个都是实现自动化触发的优秀条件。

举个例子：工作日早上7：30~8:30之间，从“在家”变成“不在家”，说明取上班了，可以触发一些自动化，比如推送路况到手机。同样，GPS追踪的话，可以在下班时间段，离家2公里以内，室内温度高于28度，就打开空调。

判断是否在家比较靠谱的就是通过路由器拉取在线的mac地址列表，然后与事先定义好的 known_devices.yaml进行比较，
比较遗憾的是，tp-link没有通用device_tracker的官方插件，好在万能论坛有人实现了 https://bbs.hassbian.com/thread-4737-1-1.html

由于ha升级较快，在0.96版本中已经需要稍作修改才能用，所以本人稍作修改，github了一把。

# 安装
放入 <config directory>/custom_components/ 目录

# 配置
**Example configuration.yaml:**
```yaml
device_tracker:
  - platform: tplink_tracker
    host: 192.168.2.1
    username: admin
    password: 你的密码 
    interval_seconds: 12
    consider_home: 60
    new_device_defaults:
      track_new_devices: false
      hide_if_away: false
```

# 属性说明
| 属性 | 说明 | 
| :-------------: |:-------------:| 
| host | 无线路由器的登陆地址 | 
| username | 没啥好说的 |
| password | 没啥好说的 | 
| interval_seconds | 两次扫描在线设备的时间间隔（秒） | 
| consider_home | 当设备不在线多长时间(秒)后，判断为离家 | 
| track_new_devices | 在路由器上自动发现known_devices.yaml定义以外的设备，是否要追踪，这个最好false，否则家里的在线设备阿狗阿猫都上来了） | 
| hide_if_away | 判断为离家后，是否隐藏，这个默认为false | 

每次扫描完成后，如果发现known_devices.yaml文件中没有的设备，会自动添加到known_devices.yaml
即便track_new_devices: false也不例外，只是track:属性变为false，不追踪。

# 前台界面

![avatar](https://github.com/aalavender/tplink_tracker/blob/master/1.PNG)

