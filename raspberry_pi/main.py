# coding: utf-8
from bluetooth.ble import BeaconService
from math import pow

import time,wiringpi as pi
import threading

from sqlalchemy import create_engine
from monster_db import Base, User
from sqlalchemy.orm import sessionmaker

import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime

engine = create_engine('sqlite:///BLE.db')

Base.metadata.bind = engine

Session = sessionmaker(bind=engine)
session = Session()

FROM_ADDRESS = '*@gmail.com'
MY_PASSWORD = '*'
BCC = '*'

BUZZER_GPIOPIN=23

class Beacon(object):
    def __init__(self, data, address, oldrssi=None, olddistance=None):
        self._uuid = data[0]
        # ライブラリがバグっていて8bitシフトする必要がある，またhexにしているのはこ補数表現であることを加味していないことに起因するれもライブラリのバグ
        self._major = data[1] >> 8
        self._minor = data[2] >> 8
        power = hex(data[3])
        self._power = int.from_bytes(bytes.fromhex(power[2:]), byteorder='big', signed=True)
        self._rssi = data[4]

        self._address = address
        self._oldrssi = oldrssi
        self._olddistance = olddistance

    def __str__(self):
        ret = "Beacon: address:{ADDR} uuid:{UUID} major:{MAJOR}" \
              " minor:{MINOR} txpower:{POWER} rssi:{RSSI} rssi_re:{RSSIRE} distance:{DISTANCE}" \
            .format(ADDR=self._address, UUID=self._uuid, MAJOR=self._major,
                    MINOR=self._minor, POWER=self._power, RSSI=self._rssi,
                    RSSIRE=int(self.get_low_rssi(0.95)), DISTANCE=round(self.get_distance(calibration=0.95), 1))
        return ret

    def get_major_minor(self):
        return self._major, self._minor

    def get_uuid(self):
        return self._uuid

    def get_rssi(self):
        return self._rssi if not (self._rssi is None) else None

    def get_low_rssi(self, a=0.1):
        old_rssi = self._oldrssi if not (self._oldrssi is None) else self._rssi
        return (1 - a) * self._rssi + a * old_rssi

    def get_distance(self, n=1.0, calibration=0.0, set="now"):
        if set == "now":
            if calibration != 0.0:
                # N == 2:障害物なし
                # N < 2: 反射される場合
                # N > 2: ぶつかって減衰されるとき
                return pow(10.0, (self._power - int(self.get_low_rssi(calibration))) / 10 * n)
            else:
                return pow(10.0, (self._power - self._rssi) / 10 * n)
        else:
            return self._olddistance


def nonfication_mails(userlist, subject, body):
    print("nonfication!")

    for user in userlist:
        to_addr = user.nonfication_address

        msg = create_message(FROM_ADDRESS, to_addr, BCC, subject, body)
        send(FROM_ADDRESS, to_addr, msg)
        print(user.nonfication_address)


def is_out_distance(distance, old_distance_1, old_distance_2, threshold=40):
    if old_distance_2 is None:
        return False
    if distance > old_distance_1 > old_distance_2 and distance > threshold:
        return True
    else:
        return False


def is_in_distance(distance, old_distance_1, old_distance_2, threshold=40):
    if old_distance_2 is None:
        return False
    if old_distance_2 > old_distance_1 > distance and distance <= threshold:
        return True
    else:
        return False


def check_uuid(address):
    matchlist = session.query(User).filter_by(device_id=address).count()
    is_address = True if matchlist > 0 else False
    return is_address, session.query(User).filter_by(device_id=address)


def create_message(from_addr, to_addr, bcc_addrs, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Bcc'] = bcc_addrs
    msg['Date'] = formatdate()
    return msg


def send(from_addr, to_addrs, msg):
    smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpobj.ehlo()
    smtpobj.starttls()
    smtpobj.ehlo()
    smtpobj.login(FROM_ADDRESS, MY_PASSWORD)
    smtpobj.sendmail(from_addr, to_addrs, msg.as_string())
    smtpobj.close()


def check_notifincation(uuid, al):
    if not(uuid in al):
        al[uuid] = False
        return True
    elif al[uuid] == False:
        return True
    else:
        return False


def is_user_turnover():
    return True


def send_alert_mails(userlist, beacon):
    #TODO:角度をとってやる評価関数
    data = beacon.get_major_minor()
    subject = "転倒を検知しました"
    body = "第一データ{0}第二データ{1}".format(data[0], data[1])

    for user in userlist:
        to_addr = user.nonfication_address
        msg = create_message(FROM_ADDRESS, to_addr, BCC, subject, body)
        send(FROM_ADDRESS, to_addr, msg)


def on_buzzer(time, loop=5):
    for x in range(loop):
        pi.digitalWrite(BUZZER_GPIOPIN, pi.HIGH)
        time.sleep(time)

        pi.digitalWrite(BUZZER_GPIOPIN, pi.LOW)
        time.sleep(time)


def main():
    pi.wiringPiSetupGpio()
    pi.pinMode(BUZZER_GPIOPIN, pi.OUTPUT)
    service = BeaconService()
    service.start_advertising()
    oldbeacon = {}
    al_notification = {}
    # hoge = []

    devices = service.scan(2)
    for i, (address, data) in enumerate(list(devices.items())):
        b = Beacon(data, address)
        oldbeacon[b.get_uuid()] = b

    while True:
        devices = service.scan(1)
        for i, (address, data) in enumerate(list(devices.items())):
            b = Beacon(data, address, oldbeacon[data[0]].get_low_rssi(), oldbeacon[data[0]].get_distance())

            # hoge.append(b.get_rssi())
            print(b)
            # print(len(hoge))
            # if len(hoge) == 100:
            #     print(oldbeacon)
            #     print(sum(hoge)/len(hoge))
            #     exit(0)
            is_address, userlist = check_uuid(b.get_uuid())

            # send_alert_mails(userlist, b)

            #出ているのか
            if is_out_distance(b.get_distance(),
                               oldbeacon[b.get_uuid()].get_distance(),
                               oldbeacon[b.get_uuid()].get_distance(set="old")) and is_address:

                # 以前通知したかどうか
                if check_notifincation(b.get_uuid(), al_notification):
                    al_notification[b.get_uuid()] = True
                    nonfication_mails(userlist,
                                      "{0}さんが外出しました".format(userlist[0].name),
                                      str(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))+"に外出されました"
                                      )
            # 入っているのか
            elif is_in_distance(b.get_distance(), oldbeacon[b.get_uuid()].get_distance(), oldbeacon[b.get_uuid()].get_distance(set="old")):
                al_notification[b.get_uuid()] = False
                print("戻った")

            # 最後に今回のビーコン情報の更新
            oldbeacon[b.get_uuid()] = b

    print("Done.")


if __name__ == "__main__":
    print("play")
    main()
